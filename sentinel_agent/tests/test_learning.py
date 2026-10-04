"""Tests for Sentinel feedback learning and threshold multiplier adjustments."""

from datetime import datetime, timedelta, timezone
import pytest

from sentinel_agent.agent import OutbreakSentinelAgent
from sentinel_agent.db import (
    get_threshold_multiplier,
    record_diagnosis,
    set_threshold_multiplier,
)
from sentinel_agent.tools import log_decision


def test_evaluate_past_alerts_resolved_outcome(temp_db: str):
    """When cases drop after 5 days, status marks 'resolved' and multiplier decreases."""
    disease = "Bacterial Leaf Blight"
    set_threshold_multiplier(disease, 1.5, db_path=temp_db)

    six_days_ago = (datetime.now(timezone.utc) - timedelta(days=6)).isoformat()
    # Log past outbreak decision with 10 initial cases
    log_decision(
        district="Anuradhapura",
        crop="Rice",
        disease=disease,
        level="outbreak",
        reason="Initial test outbreak",
        case_count=10,
        baseline=1.0,
        weather_level="High",
        alert_sent=True,
        created_at=six_days_ago,
        db_path=temp_db,
    )

    # Current cases in last 48h: only 2 cases (drop of 80%)
    now = datetime.now(timezone.utc).isoformat()
    for _ in range(2):
        record_diagnosis("Rice", disease, "Anuradhapura", 0.85, created_at=now, db_path=temp_db)

    agent = OutbreakSentinelAgent(db_path=temp_db)
    evaluations = agent.evaluate_past_alerts(days_post_alert=5)

    assert len(evaluations) == 1
    ev = evaluations[0]
    assert ev["outcome"] == "resolved"
    assert ev["new_multiplier"] == 1.25  # 1.5 - 0.25
    assert get_threshold_multiplier(disease, db_path=temp_db) == 1.25


def test_evaluate_past_alerts_worsening_outcome(temp_db: str):
    """When cases increase after 5 days, status marks 'worsening' and multiplier increases."""
    disease = "Rice Blast"
    set_threshold_multiplier(disease, 1.0, db_path=temp_db)

    six_days_ago = (datetime.now(timezone.utc) - timedelta(days=6)).isoformat()
    log_decision(
        district="Polonnaruwa",
        crop="Rice",
        disease=disease,
        level="outbreak",
        reason="Initial test outbreak",
        case_count=5,
        baseline=1.0,
        weather_level="High",
        alert_sent=True,
        created_at=six_days_ago,
        db_path=temp_db,
    )

    # Current cases in last 48h: 8 cases (60% increase)
    now = datetime.now(timezone.utc).isoformat()
    for _ in range(8):
        record_diagnosis("Rice", disease, "Polonnaruwa", 0.9, created_at=now, db_path=temp_db)

    agent = OutbreakSentinelAgent(db_path=temp_db)
    evaluations = agent.evaluate_past_alerts(days_post_alert=5)

    assert len(evaluations) == 1
    ev = evaluations[0]
    assert ev["outcome"] == "worsening"
    assert ev["new_multiplier"] == 1.25  # 1.0 + 0.25
    assert get_threshold_multiplier(disease, db_path=temp_db) == 1.25
