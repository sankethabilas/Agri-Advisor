"""Outbreak Sentinel Agent: Autonomous Sense -> Reason -> Act -> Learn loop.

Executes scheduled, autonomous agricultural disease surveillance for Sri Lankan districts.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional

from sentinel_agent.config import settings
from sentinel_agent.db import (
    get_connection,
    get_neighbouring_districts,
    get_threshold_multiplier,
    init_db,
    set_threshold_multiplier,
)
from sentinel_agent.notifier import BaseNotifier, default_notifier, get_notifier
from sentinel_agent.prompts import (
    build_officer_template_alert,
    generate_farmer_alert_llm,
)
from sentinel_agent.stats import classify_sentinel_risk, is_anomalous_cluster
from sentinel_agent.tools import (
    get_baseline,
    get_recent_cases,
    get_weather_risk,
    is_in_cooldown,
    log_decision,
    retrieve_guidance,
)

logger = logging.getLogger("sentinel_agent")


class OutbreakSentinelAgent:
    """Autonomous Outbreak Sentinel Agent implementation."""

    def __init__(self, db_path: Optional[str] = None, notifier: Optional[BaseNotifier] = None) -> None:
        self.db_path = db_path or settings.db_path
        self.notifier = notifier or get_notifier()
        init_db(self.db_path)

    def scan(self, weather_url: Optional[str] = None, rag_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Executes one full Sense -> Reason -> Decide -> Act cycle across all districts.

        Returns:
            List of decisions made during this scan.
        """
        logger.info("Starting Outbreak Sentinel Scan...")
        decisions: List[Dict[str, Any]] = []

        # 1. SENSE: Identify active disease clusters in last 48 hours
        recent_clusters = get_recent_cases(
            hours=48,
            min_confidence=settings.confidence_threshold,
            db_path=self.db_path,
        )

        if not recent_clusters:
            logger.info("No active disease clusters found above confidence threshold.")
            return decisions

        for cluster in recent_clusters:
            district = cluster["district"]
            crop = cluster["crop"]
            disease = cluster["disease"]
            count = cluster["case_count"]

            # 2. REASON: Compare against 28-day baseline and disease threshold
            baseline_mean, std_dev = get_baseline(district, crop, disease, days=28, db_path=self.db_path)
            multiplier = get_threshold_multiplier(disease, db_path=self.db_path)

            is_anomalous, stat_reason = is_anomalous_cluster(
                recent_count=count,
                baseline=baseline_mean,
                std_dev=std_dev,
                multiplier=multiplier,
                min_cases=settings.min_cases,
            )

            # Weather risk query for anomalous clusters
            weather_risk_level = "None"
            weather_score = 0.0
            if is_anomalous:
                weather_info = get_weather_risk(district, crop, weather_url=weather_url)
                weather_risk_level = weather_info.get("level", "Unknown")
                weather_score = weather_info.get("score", 0.0)

            # 3. DECIDE: Classify status (none / watch / outbreak)
            level, reason = classify_sentinel_risk(
                is_anomalous=is_anomalous,
                weather_disease_risk_level=weather_risk_level,
                recent_count=count,
                baseline=baseline_mean,
                effective_std=std_dev,
                weather_score=weather_score,
            )

            alert_sent = False

            # 4. ACT: Execute notification actions based on level
            if level == "watch":
                # Notify Extension Officer only
                self._notify_officers(
                    district=district,
                    crop=crop,
                    disease=disease,
                    level=level,
                    case_count=count,
                    baseline=baseline_mean,
                    weather_level=weather_risk_level,
                    reason=reason,
                )
                alert_sent = True

            elif level == "outbreak":
                # Check 24h cooldown to avoid alert fatigue
                if is_in_cooldown(district, crop, disease, db_path=self.db_path):
                    reason += " [Alert skipped: 24h cooldown active]"
                    logger.info("Cooldown active for %s - %s (%s); farmer alert skipped.", district, crop, disease)
                else:
                    # Retrieve verified RAG treatment guidance
                    rag_data = retrieve_guidance(disease, rag_url=rag_url)
                    guidance = rag_data.get("context", "")
                    sources = rag_data.get("sources", ["DOA Sri Lanka"])

                    # Notify Extension Officers
                    self._notify_officers(
                        district=district,
                        crop=crop,
                        disease=disease,
                        level=level,
                        case_count=count,
                        baseline=baseline_mean,
                        weather_level=weather_risk_level,
                        reason=reason,
                    )

                    # Notify Subscribed Farmers in District + Neighbouring Districts
                    self._notify_farmers(
                        district=district,
                        crop=crop,
                        disease=disease,
                        guidance=guidance,
                        sources=sources,
                    )
                    alert_sent = True

            # Record decision in DB
            decision_id = log_decision(
                district=district,
                crop=crop,
                disease=disease,
                level=level,
                reason=reason,
                case_count=count,
                baseline=baseline_mean,
                weather_level=weather_risk_level,
                alert_sent=alert_sent,
                db_path=self.db_path,
            )

            decision_record = {
                "id": decision_id,
                "district": district,
                "crop": crop,
                "disease": disease,
                "level": level,
                "reason": reason,
                "case_count": count,
                "baseline": round(baseline_mean, 2),
                "weather_level": weather_risk_level,
                "alert_sent": alert_sent,
            }
            decisions.append(decision_record)

        logger.info("Scan completed with %d decisions.", len(decisions))
        return decisions

    def evaluate_past_alerts(self, days_post_alert: int = 5) -> List[Dict[str, Any]]:
        """LEARN tool: Evaluates outbreak decisions after 5 days to assess trajectory and adjust thresholds."""
        logger.info("Evaluating past outbreak alerts for feedback learning...")
        now = datetime.now(timezone.utc)
        eval_cutoff = (now - timedelta(days=days_post_alert)).isoformat()
        evaluations: List[Dict[str, Any]] = []

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, district, crop, disease, case_count, created_at
                FROM sentinel_decisions
                WHERE level = 'outbreak'
                  AND evaluated_at IS NULL
                  AND created_at <= ?;
                """,
                (eval_cutoff,),
            )
            rows = [dict(r) for r in cursor.fetchall()]

        for row in rows:
            decision_id = row["id"]
            district = row["district"]
            crop = row["crop"]
            disease = row["disease"]
            initial_cases = row["case_count"]

            # Count recent cases in the last 48 hours for this cluster
            recent_cases = get_recent_cases(
                district=district,
                crop=crop,
                hours=48,
                db_path=self.db_path,
            )
            current_count = 0
            for cluster in recent_cases:
                if cluster["disease"] == disease:
                    current_count = cluster["case_count"]
                    break

            # Determine trajectory: resolved / persisting / worsening
            current_multiplier = get_threshold_multiplier(disease, db_path=self.db_path)
            if current_count <= initial_cases * 0.7:  # >= 30% reduction
                outcome = "resolved"
                new_multiplier = max(1.0, current_multiplier - 0.25)
            elif current_count >= initial_cases * 1.3:  # >= 30% increase
                outcome = "worsening"
                new_multiplier = min(3.0, current_multiplier + 0.25)
            else:
                outcome = "persisting"
                new_multiplier = current_multiplier

            # Update database records
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE sentinel_decisions
                    SET evaluated_at = ?, outcome = ?
                    WHERE id = ?;
                    """,
                    (now.isoformat(), outcome, decision_id),
                )
                conn.commit()

            set_threshold_multiplier(disease, new_multiplier, db_path=self.db_path)

            eval_record = {
                "decision_id": decision_id,
                "district": district,
                "crop": crop,
                "disease": disease,
                "initial_cases": initial_cases,
                "current_cases": current_count,
                "outcome": outcome,
                "previous_multiplier": current_multiplier,
                "new_multiplier": new_multiplier,
            }
            evaluations.append(eval_record)

        logger.info("Evaluated %d past alerts.", len(evaluations))
        return evaluations

    def _notify_officers(
        self,
        district: str,
        crop: str,
        disease: str,
        level: str,
        case_count: int,
        baseline: float,
        weather_level: str,
        reason: str,
    ) -> None:
        """Dispatches notification to district extension officers."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT language, channel, contact FROM officers WHERE district = ?;",
                (district,),
            )
            officers = cursor.fetchall()
            for officer in officers:
                lang = officer["language"]
                channel = officer["channel"]
                contact = officer["contact"]
                msg = build_officer_template_alert(
                    district=district,
                    crop=crop,
                    disease=disease,
                    level=level,
                    case_count=case_count,
                    baseline=baseline,
                    weather_level=weather_level,
                    reason=reason,
                    language=lang,
                )
                self.notifier.send(
                    audience="officer",
                    district=district,
                    contact=contact,
                    message=msg,
                    language=lang,
                    channel=channel,
                )

    def _notify_farmers(
        self,
        district: str,
        crop: str,
        disease: str,
        guidance: str,
        sources: List[str],
    ) -> None:
        """Dispatches alerts to subscribed farmers in target district and neighbouring districts."""
        target_districts = [district] + get_neighbouring_districts(district, db_path=self.db_path)
        placeholders = ",".join("?" for _ in target_districts)

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT district, language, channel, contact
                FROM subscribers
                WHERE crop = ? AND district IN ({placeholders});
                """,
                [crop] + target_districts,
            )
            subscribers = cursor.fetchall()

            for sub in subscribers:
                sub_district = sub["district"]
                lang = sub["language"]
                channel = sub["channel"]
                contact = sub["contact"]

                alert_text = generate_farmer_alert_llm(
                    district=district,
                    crop=crop,
                    disease=disease,
                    guidance_context=guidance,
                    sources=sources,
                    language=lang,
                )

                self.notifier.send(
                    audience="farmer",
                    district=sub_district,
                    contact=contact,
                    message=alert_text,
                    language=lang,
                    channel=channel,
                )


sentinel_agent = OutbreakSentinelAgent()
