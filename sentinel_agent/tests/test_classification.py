"""Tests for sentinel classification, confidence filtering, and weather fallbacks."""

from datetime import datetime, timezone
import pytest
from unittest.mock import patch

from sentinel_agent.agent import OutbreakSentinelAgent
from sentinel_agent.db import record_diagnosis
from sentinel_agent.notifier import ConsoleNotifier
from sentinel_agent.tools import get_recent_cases, get_weather_risk


def test_confidence_filtering(temp_db: str):
    """Verifies that diagnosis entries with confidence < 0.7 are ignored."""
    now = datetime.now(timezone.utc).isoformat()
    # Insert 4 low confidence cases (< 0.7)
    for _ in range(4):
        record_diagnosis("Rice", "Blast", "Polonnaruwa", 0.65, created_at=now, db_path=temp_db)
    # Insert 2 high confidence cases (>= 0.7)
    for _ in range(2):
        record_diagnosis("Rice", "Blast", "Polonnaruwa", 0.85, created_at=now, db_path=temp_db)

    recent = get_recent_cases(district="Polonnaruwa", crop="Rice", db_path=temp_db)
    assert len(recent) == 1
    # Only 2 cases should be counted
    assert recent[0]["case_count"] == 2


def test_weather_failure_classifies_as_watch(temp_db: str):
    """Ensures weather service unavailability falls back to 'watch' (never false 'outbreak')."""
    now = datetime.now(timezone.utc).isoformat()
    # Seed 6 high-confidence cases
    for _ in range(6):
        record_diagnosis("Rice", "Bacterial Leaf Blight", "Anuradhapura", 0.9, created_at=now, db_path=temp_db)

    notifier = ConsoleNotifier()
    agent = OutbreakSentinelAgent(db_path=temp_db, notifier=notifier)

    # Mock weather call to fail completely
    with patch("sentinel_agent.tools.requests.post", side_effect=Exception("Connection timeout")):
        decisions = agent.scan()

    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["level"] == "watch"
    assert decision["weather_level"] == "Unknown"
    # Officer alert should be sent, but not farmer alert
    assert any(msg.audience == "officer" for msg in notifier.sent_messages)
    assert not any(msg.audience == "farmer" for msg in notifier.sent_messages)
