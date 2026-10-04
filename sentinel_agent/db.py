"""SQLite database access layer for the Outbreak Sentinel Agent.

Enforces data minimisation: stores only district-level agricultural data,
no personal identities or farmer names.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from sentinel_agent.config import settings

# Sri Lankan District Adjacency Mapping (Initial Seed Map)
DEFAULT_DISTRICT_NEIGHBOURS: List[Tuple[str, str]] = [
    # Anuradhapura & Neighbours
    ("Anuradhapura", "Polonnaruwa"),
    ("Anuradhapura", "Kurunegala"),
    ("Anuradhapura", "Matale"),
    ("Anuradhapura", "Vavuniya"),
    ("Anuradhapura", "Mannar"),
    ("Anuradhapura", "Puttalam"),
    # Polonnaruwa & Neighbours
    ("Polonnaruwa", "Anuradhapura"),
    ("Polonnaruwa", "Matale"),
    ("Polonnaruwa", "Batticaloa"),
    ("Polonnaruwa", "Ampara"),
    # Kurunegala & Neighbours
    ("Kurunegala", "Anuradhapura"),
    ("Kurunegala", "Puttalam"),
    ("Kurunegala", "Gampaha"),
    ("Kurunegala", "Kegalle"),
    ("Kurunegala", "Matale"),
    ("Kurunegala", "Kandy"),
    # Kandy & Neighbours
    ("Kandy", "Matale"),
    ("Kandy", "Kurunegala"),
    ("Kandy", "Kegalle"),
    ("Kandy", "Nuwara Eliya"),
    ("Kandy", "Badulla"),
    # Badulla & Neighbours
    ("Badulla", "Nuwara Eliya"),
    ("Badulla", "Monaragala"),
    ("Badulla", "Kandy"),
    ("Badulla", "Ampara"),
]

DEFAULT_OFFICERS = [
    ("Anuradhapura", "en", "sms", "+94770001001"),
    ("Anuradhapura", "si", "sms", "+94770001002"),
    ("Polonnaruwa", "si", "sms", "+94770001003"),
    ("Kurunegala", "si", "sms", "+94770001004"),
    ("Jaffna", "ta", "sms", "+94770001005"),
    ("Batticaloa", "ta", "sms", "+94770001006"),
]

DEFAULT_SUBSCRIBERS = [
    ("Anuradhapura", "Rice", "si", "sms", "+94711111111"),
    ("Anuradhapura", "Rice", "en", "sms", "+94711111112"),
    ("Polonnaruwa", "Rice", "si", "sms", "+94711111113"),
    ("Kurunegala", "Rice", "si", "sms", "+94711111114"),
    ("Jaffna", "Paddy", "ta", "sms", "+94711111115"),
]


def get_db_path(db_path: Optional[str] = None) -> str:
    path = db_path or settings.db_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(db_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initializes the database schema and default seeds."""
    path = get_db_path(db_path)
    with sqlite3.connect(path, timeout=15.0) as conn:
        cursor = conn.cursor()

        # 1. diagnosis_log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnosis_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crop TEXT NOT NULL,
                disease TEXT NOT NULL,
                district TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL,
                is_simulated BOOLEAN DEFAULT 0,
                outcome TEXT NULL
            );
        """)

        # 2. sentinel_decisions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentinel_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                district TEXT NOT NULL,
                crop TEXT NOT NULL,
                disease TEXT NOT NULL,
                level TEXT NOT NULL,
                reason TEXT NOT NULL,
                case_count INTEGER NOT NULL,
                baseline REAL NOT NULL,
                weather_level TEXT NOT NULL,
                alert_sent BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                evaluated_at TEXT NULL,
                outcome TEXT NULL
            );
        """)

        # 3. subscribers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                district TEXT NOT NULL,
                crop TEXT NOT NULL,
                language TEXT NOT NULL,
                channel TEXT NOT NULL,
                contact TEXT NOT NULL
            );
        """)

        # 4. officers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS officers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                district TEXT NOT NULL,
                language TEXT NOT NULL,
                channel TEXT NOT NULL,
                contact TEXT NOT NULL
            );
        """)

        # 5. district_neighbours
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS district_neighbours (
                district TEXT NOT NULL,
                neighbour TEXT NOT NULL,
                PRIMARY KEY (district, neighbour)
            );
        """)

        # 6. threshold_config
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threshold_config (
                disease TEXT PRIMARY KEY,
                multiplier REAL DEFAULT 1.0
            );
        """)

        # Seed district neighbours if empty
        cursor.execute("SELECT COUNT(*) FROM district_neighbours;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT OR IGNORE INTO district_neighbours (district, neighbour) VALUES (?, ?);",
                DEFAULT_DISTRICT_NEIGHBOURS,
            )

        # Seed sample officers if empty
        cursor.execute("SELECT COUNT(*) FROM officers;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO officers (district, language, channel, contact) VALUES (?, ?, ?, ?);",
                DEFAULT_OFFICERS,
            )

        # Seed sample subscribers if empty
        cursor.execute("SELECT COUNT(*) FROM subscribers;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO subscribers (district, crop, language, channel, contact) VALUES (?, ?, ?, ?, ?);",
                DEFAULT_SUBSCRIBERS,
            )

        conn.commit()


def record_diagnosis(
    crop: str,
    disease: str,
    district: str,
    confidence: float,
    created_at: Optional[str] = None,
    is_simulated: bool = False,
    db_path: Optional[str] = None,
) -> int:
    """Inserts an anonymized diagnosis log entry."""
    init_db(db_path)
    now_iso = created_at or datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO diagnosis_log (crop, disease, district, confidence, created_at, is_simulated)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (crop, disease, district, float(confidence), now_iso, int(is_simulated)),
        )
        conn.commit()
        return cursor.lastrowid


def get_threshold_multiplier(disease: str, db_path: Optional[str] = None) -> float:
    """Retrieves the learned threshold multiplier for a disease."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT multiplier FROM threshold_config WHERE disease = ?;", (disease,))
        row = cursor.fetchone()
        return float(row["multiplier"]) if row else 1.0


def set_threshold_multiplier(disease: str, multiplier: float, db_path: Optional[str] = None) -> None:
    """Sets/updates the threshold multiplier bounded in [1.0, 3.0]."""
    bounded = max(1.0, min(3.0, round(multiplier, 2)))
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO threshold_config (disease, multiplier)
            VALUES (?, ?)
            ON CONFLICT(disease) DO UPDATE SET multiplier = excluded.multiplier;
            """,
            (disease, bounded),
        )
        conn.commit()


def get_neighbouring_districts(district: str, db_path: Optional[str] = None) -> List[str]:
    """Returns the list of neighbouring districts."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT neighbour FROM district_neighbours WHERE district = ?;",
            (district,),
        )
        rows = cursor.fetchall()
        return [row["neighbour"] for row in rows]
