"""End-to-end integration tests for the Outbreak Sentinel demo scenarios."""

from datetime import datetime, timezone
import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from sentinel_agent.agent import OutbreakSentinelAgent
from sentinel_agent.notifier import ConsoleNotifier
from sentinel_agent.prompts import COMPACT_DISCLAIMER
from sentinel_agent.seed import seed_demo_data
from sentinel_agent.main import app


def test_e2e_scenario_1_outbreak_rice_blb(temp_db: str):
    """Demo Scenario 1:

    - 6 simulated cases of Bacterial Leaf Blight in Anuradhapura in 48h.
    - 28-day baseline is low (~1 case).
    - Weather Agent disease_risk is 'High' (0.85).
    - Expected: Decision is 'outbreak', officer notified, farmers in Anuradhapura & neighbours notified.
    """
    # 1. Seed demo data
    seed_demo_data(district="Anuradhapura", crop="Rice", disease="Bacterial Leaf Blight", db_path=temp_db)

    notifier = ConsoleNotifier()
    agent = OutbreakSentinelAgent(db_path=temp_db, notifier=notifier)

    # Mock Weather Agent to return High risk
    mock_weather_resp = MagicMock()
    mock_weather_resp.status_code = 200
    mock_weather_resp.json.return_value = {
        "disease_risk": {"level": "High", "score": 0.85, "recommendation": "High humidity fosters blight."},
        "pest_risk": {"level": "Low", "score": 0.2},
        "alerts": ["High humidity detected"],
    }

    # Mock RAG Agent
    mock_rag_resp = MagicMock()
    mock_rag_resp.status_code = 200
    mock_rag_resp.json.return_value = {
        "context": "Drain standing water immediately and reduce nitrogen application.",
        "sources": ["DOA Sri Lanka Paddy Advisory 2024"],
        "confidence": [0.95],
    }

    def mock_requests_post(url, *args, **kwargs):
        if "weather" in url:
            return mock_weather_resp
        elif "rag" in url:
            return mock_rag_resp
        return MagicMock(status_code=404)

    with patch("requests.post", side_effect=mock_requests_post), \
         patch("sentinel_agent.tools.requests.post", side_effect=mock_requests_post):
        decisions = agent.scan()

    assert len(decisions) >= 1
    blb_decision = next(d for d in decisions if d["disease"] == "Bacterial Leaf Blight")

    assert blb_decision["level"] == "outbreak"
    assert blb_decision["weather_level"] == "High"
    assert blb_decision["alert_sent"] is True
    assert "cases vs baseline" in blb_decision["reason"]

    # Assert notifications
    officer_messages = [m for m in notifier.sent_messages if m.audience == "officer"]
    farmer_messages = [m for m in notifier.sent_messages if m.audience == "farmer"]

    assert len(officer_messages) >= 1
    assert any(m.district == "Anuradhapura" for m in officer_messages)

    # Farmer messages should reach Anuradhapura AND neighbours (e.g. Polonnaruwa, Kurunegala)
    assert len(farmer_messages) >= 1
    farmer_districts = {m.district for m in farmer_messages}
    assert "Anuradhapura" in farmer_districts
    assert "Polonnaruwa" in farmer_districts or "Kurunegala" in farmer_districts

    # Verify disclaimer in every farmer alert
    for f_msg in farmer_messages:
        assert COMPACT_DISCLAIMER in f_msg.message or "උපදේශනාත්මක" in f_msg.message or "ஆலோசனைக்" in f_msg.message


def test_e2e_scenario_2_watch_medium_weather(temp_db: str):
    """Demo Scenario 2:

    - 6 simulated cases in Anuradhapura.
    - Weather Agent disease_risk is 'Medium' (0.50).
    - Expected: Decision is 'watch', officer notified, NO farmer alerts.
    """
    seed_demo_data(district="Anuradhapura", crop="Rice", disease="Bacterial Leaf Blight", db_path=temp_db)

    notifier = ConsoleNotifier()
    agent = OutbreakSentinelAgent(db_path=temp_db, notifier=notifier)

    mock_weather_resp = MagicMock()
    mock_weather_resp.status_code = 200
    mock_weather_resp.json.return_value = {
        "disease_risk": {"level": "Medium", "score": 0.50, "recommendation": "Moderate humidity."},
        "pest_risk": {"level": "Low", "score": 0.2},
        "alerts": [],
    }

    with patch("requests.post", return_value=mock_weather_resp), \
         patch("sentinel_agent.tools.requests.post", return_value=mock_weather_resp):
        decisions = agent.scan()

    assert len(decisions) >= 1
    blb_decision = next(d for d in decisions if d["disease"] == "Bacterial Leaf Blight")

    assert blb_decision["level"] == "watch"
    assert blb_decision["weather_level"] == "Medium"

    # Only officer alerts sent; zero farmer alerts
    assert any(m.audience == "officer" for m in notifier.sent_messages)
    assert not any(m.audience == "farmer" for m in notifier.sent_messages)


def test_api_endpoints_health_and_scan(temp_db: str):
    """Tests FastAPI /api/sentinel endpoints via TestClient."""
    with patch("sentinel_agent.config.settings.db_path", temp_db), \
         patch("sentinel_agent.agent.sentinel_agent.db_path", temp_db):
        client = TestClient(app)

        # Health
        health_resp = client.get("/api/sentinel/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "healthy"

        # Seed Demo
        seed_resp = client.post("/api/sentinel/seed-demo")
        assert seed_resp.status_code == 200
        assert seed_resp.json()["status"] == "seeded"

        # Decisions Query
        dec_resp = client.get("/api/sentinel/decisions")
        assert dec_resp.status_code == 200
        assert "decisions" in dec_resp.json()
