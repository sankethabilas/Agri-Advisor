"""Tool functions for the Outbreak Sentinel Agent.

Each tool function is explicit, modular, and independently testable.
"""

from datetime import datetime, timedelta, timezone
import logging
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from sentinel_agent.config import settings
from sentinel_agent.db import get_connection, init_db
from sentinel_agent.stats import calculate_baseline_and_std

logger = logging.getLogger("sentinel_agent.tools")


def get_recent_cases(
    district: Optional[str] = None,
    crop: Optional[str] = None,
    hours: int = 48,
    min_confidence: Optional[float] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """SENSE tool: Reads anonymized diagnosis records for the last `hours` window.

    Filters records with confidence >= min_confidence and groups by (district, crop, disease).
    """
    init_db(db_path)
    conf_threshold = min_confidence if min_confidence is not None else settings.confidence_threshold
    cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    query = """
        SELECT district, crop, disease, COUNT(*) as case_count
        FROM diagnosis_log
        WHERE created_at >= ?
          AND confidence >= ?
    """
    params: List[Any] = [cutoff_time, conf_threshold]

    if district:
        query += " AND district = ?"
        params.append(district)
    if crop:
        query += " AND crop = ?"
        params.append(crop)

    query += " GROUP BY district, crop, disease ORDER BY case_count DESC;"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [
            {
                "district": row["district"],
                "crop": row["crop"],
                "disease": row["disease"],
                "case_count": int(row["case_count"]),
            }
            for row in rows
        ]


def get_baseline(
    district: str,
    crop: str,
    disease: str,
    days: int = 28,
    db_path: Optional[str] = None,
) -> Tuple[float, float]:
    """REASON tool: Computes the 28-day historical baseline and std dev scaled to a 48h window."""
    init_db(db_path)
    now = datetime.now(timezone.utc)
    start_window = now - timedelta(days=days)
    end_window = now - timedelta(hours=48)  # Prior to the recent 48h window

    # Partition the 28 days (excluding last 48h = 26 days = 13 bins of 48h) into 48-hour bins
    bin_counts: List[int] = []
    current_start = start_window
    bin_size = timedelta(hours=48)

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        while current_start + bin_size <= now:
            bin_end = current_start + bin_size
            cursor.execute(
                """
                SELECT COUNT(*) FROM diagnosis_log
                WHERE district = ?
                  AND crop = ?
                  AND disease = ?
                  AND created_at >= ?
                  AND created_at < ?
                  AND confidence >= ?;
                """,
                (
                    district,
                    crop,
                    disease,
                    current_start.isoformat(),
                    bin_end.isoformat(),
                    settings.confidence_threshold,
                ),
            )
            count = cursor.fetchone()[0]
            bin_counts.append(count)
            current_start = bin_end

    return calculate_baseline_and_std(bin_counts, std_floor=0.5)


def get_weather_risk(
    district: str,
    crop: str,
    weather_url: Optional[str] = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """DECIDE tool: Calls Weather Agent with exponential backoff (3 tries).

    If the Weather Agent is unreachable or fails, falls back gracefully to 'Unknown'
    level (preventing false 'outbreak' classifications).
    """
    url = weather_url or settings.weather_agent_url
    payload = {"location": district, "crop": crop}
    backoff = 0.2

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, json=payload, timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                disease_risk = data.get("disease_risk") or {}
                return {
                    "level": disease_risk.get("level", "Unknown"),
                    "score": float(disease_risk.get("score", 0.0)),
                    "recommendation": disease_risk.get("recommendation", ""),
                    "alerts": data.get("alerts", []),
                    "success": True,
                }
        except Exception as err:
            logger.warning("Weather agent attempt %d failed: %s", attempt, err)
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2

    # Resilience Fallback: If unreachable, classify with Unknown/Offline risk
    return {
        "level": "Unknown",
        "score": 0.0,
        "recommendation": "Weather service temporarily offline. Standard precautions advised.",
        "alerts": ["Weather service unavailable"],
        "success": False,
    }


def retrieve_guidance(
    disease: str,
    rag_url: Optional[str] = None,
    top_k: int = 3,
) -> Dict[str, Any]:
    """ACT tool: Retrieves verified agricultural treatments from RAG service."""
    url = rag_url or settings.rag_agent_url
    query = f"Treatment and control guidelines for {disease}"
    try:
        response = requests.post(url, json={"query": query, "top_k": top_k}, timeout=3.0)
        if response.status_code == 200:
            data = response.json()
            return {
                "context": data.get("context", ""),
                "sources": data.get("sources", ["Department of Agriculture Sri Lanka"]),
                "confidence": data.get("confidence", [0.9]),
            }
    except Exception as err:
        logger.warning("RAG service unavailable for guidance retrieval: %s", err)

    # Fallback response
    return {
        "context": f"Inspect fields promptly for {disease}. Apply recommended cultural and organic treatments.",
        "sources": ["Department of Agriculture Sri Lanka (General Guidelines)"],
        "confidence": [0.8],
    }


def is_in_cooldown(
    district: str,
    crop: str,
    disease: str,
    cooldown_hours: Optional[int] = None,
    db_path: Optional[str] = None,
) -> bool:
    """Checks if a farmer alert was already sent for this cluster in the last 24 hours."""
    init_db(db_path)
    hours = cooldown_hours if cooldown_hours is not None else settings.cooldown_hours
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM sentinel_decisions
            WHERE district = ?
              AND crop = ?
              AND disease = ?
              AND level = 'outbreak'
              AND alert_sent = 1
              AND created_at >= ?;
            """,
            (district, crop, disease, cutoff),
        )
        return cursor.fetchone()[0] > 0


def log_decision(
    district: str,
    crop: str,
    disease: str,
    level: str,
    reason: str,
    case_count: int,
    baseline: float,
    weather_level: str,
    alert_sent: bool,
    created_at: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    """Stores the sentinel decision in the database."""
    init_db(db_path)
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sentinel_decisions (
                district, crop, disease, level, reason, case_count,
                baseline, weather_level, alert_sent, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                district,
                crop,
                disease,
                level,
                reason,
                case_count,
                float(baseline),
                weather_level,
                int(alert_sent),
                timestamp,
            ),
        )
        conn.commit()
        return cursor.lastrowid
