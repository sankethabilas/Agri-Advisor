"""Tests for alert generation, translation, cooldown enforcement, and template fallbacks."""

from datetime import datetime, timezone
import pytest
from unittest.mock import patch, MagicMock

from sentinel_agent.agent import OutbreakSentinelAgent
from sentinel_agent.db import record_diagnosis
from sentinel_agent.notifier import ConsoleNotifier
from sentinel_agent.prompts import (
    COMPACT_DISCLAIMER,
    build_farmer_template_alert,
    generate_farmer_alert_llm,
    translate,
)
from sentinel_agent.tools import is_in_cooldown, log_decision


def test_cooldown_prevents_duplicate_farmer_alerts(temp_db: str):
    """Verifies that farmer alerts are not duplicated within 24h for the same cluster."""
    # Log an outbreak alert sent 2 hours ago
    now = datetime.now(timezone.utc).isoformat()
    log_decision(
        district="Anuradhapura",
        crop="Rice",
        disease="Bacterial Leaf Blight",
        level="outbreak",
        reason="Test outbreak",
        case_count=7,
        baseline=1.0,
        weather_level="High",
        alert_sent=True,
        created_at=now,
        db_path=temp_db,
    )

    # Check cooldown
    assert is_in_cooldown("Anuradhapura", "Rice", "Bacterial Leaf Blight", db_path=temp_db)
    # Different district should NOT be in cooldown
    assert not is_in_cooldown("Kurunegala", "Rice", "Bacterial Leaf Blight", db_path=temp_db)


def test_farmer_alert_template_format_and_disclaimer():
    """Ensures fallback template has disclaimer, correct sources, and fits SMS constraints."""
    alert = build_farmer_template_alert(
        district="Anuradhapura",
        crop="Rice",
        disease="Bacterial Leaf Blight",
        guidance="Drain excess field water and apply copper-based bactericide.",
        sources=["DOA Sri Lanka"],
        language="en",
    )
    assert len(alert) <= 320
    assert "Bacterial Leaf Blight" in alert
    assert "DOA Sri Lanka" in alert
    assert COMPACT_DISCLAIMER in alert


def test_multilingual_translation_stub():
    """Tests Sinhala and Tamil translation stubs."""
    sinhala = translate("Rice crop ALERT", "si")
    tamil = translate("Rice crop ALERT", "ta")
    assert "වී වගාව" in sinhala or "අවධානයයි" in sinhala
    assert "நெல் பயிர்" in tamil or "எச்சரிக்கை" in tamil


def test_llm_failure_falls_back_to_template():
    """If Groq/OpenAI throws an error, the agent generates a valid template alert."""
    with patch("sentinel_agent.config.settings.groq_api_key", "mock-key"):
        with patch("sentinel_agent.config.settings.llm_provider", "groq"):
            with patch("groq.Groq", side_effect=Exception("API quota exceeded")):
                alert = generate_farmer_alert_llm(
                    district="Kurunegala",
                    crop="Rice",
                    disease="Brown Spot",
                    guidance_context="Apply balanced potash fertilizer.",
                    sources=["DOA Rice Guide"],
                    language="en",
                )
                assert "Brown Spot" in alert
                assert "Kurunegala" in alert
                assert COMPACT_DISCLAIMER in alert
