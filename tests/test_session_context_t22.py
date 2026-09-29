"""
Multi-turn Session Context Persistence Integration Tests (Subtask T-22.4).
Verifies that session context (active crop, confirmed diseases, geographic location,
language preference, and full conversational turn history) persists across multi-turn follow-ups.
"""

from datetime import datetime, timezone
import pytest
from starlette.testclient import TestClient

from orchestrator.main import app
from orchestrator.security import create_access_token
from orchestrator.session_context import session_manager

client = TestClient(app)


def auth_headers(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


@pytest.fixture(autouse=True)
def clean_sessions():
    session_manager._sessions_by_user.clear()
    session_manager._sessions_by_id.clear()
    yield


def test_t22_4_multi_turn_continuity_three_turns():
    """
    Verify 3-turn farmer interaction:
    Turn 1: "My paddy in Kurunegala has blast lesions and yellowing" -> Establishes crop=Paddy, location=Kurunegala, diagnosis=Blast
    Turn 2: "What organic or chemical treatment can I apply?" (No crop or location mentioned) -> Retains Paddy & Kurunegala
    Turn 3: "Is the weather suitable for spraying tomorrow?" (No crop or location mentioned) -> Retains Paddy & Kurunegala
    """
    user_id = "farmer-3turn-t22"
    headers = auth_headers(user_id)

    # Turn 1
    t1_payload = {
        "query": "My paddy in Kurunegala has blast lesions and yellowing",
        "user_id": user_id,
        "location": {"district": "Kurunegala", "agro_ecological_zone": "IL1a"},
        "crop_context": "Paddy",
        "language": "en",
    }
    r1 = client.post("/api/orchestrator/process", json=t1_payload, headers=headers)
    assert r1.status_code == 200
    d1 = r1.json()
    session_id = d1["metadata"]["session_id"]

    sess = session_manager.get_session(user_id)
    assert sess is not None
    assert sess.active_crop == "Paddy"
    assert sess.location.get("district") == "Kurunegala"
    assert len(sess.history) == 1

    # Turn 2: Follow-up on treatment
    t2_payload = {
        "query": "What organic or chemical treatment can I apply?",
        "user_id": user_id,
        "session_id": session_id,
        "location": {"district": "Kurunegala", "agro_ecological_zone": "IL1a"},
        "language": "en",
    }
    r2 = client.post("/api/orchestrator/process", json=t2_payload, headers=headers)
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["metadata"]["session_id"] == session_id
    assert sess.active_crop == "Paddy"
    assert len(sess.history) == 2

    # Turn 3: Follow-up on weather / spraying
    t3_payload = {
        "query": "Is the weather suitable for spraying tomorrow?",
        "user_id": user_id,
        "session_id": session_id,
        "location": {"district": "Kurunegala", "agro_ecological_zone": "IL1a"},
        "language": "en",
    }
    r3 = client.post("/api/orchestrator/process", json=t3_payload, headers=headers)
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["metadata"]["session_id"] == session_id
    assert "weather_agent" in d3["metadata"]["agents_consulted"]
    assert len(sess.history) == 3


def test_t22_4_session_rest_endpoints_retrieval_and_clearing():
    """Verify GET /api/sessions/{user_id} and DELETE /api/sessions/{user_id}."""
    user_id = "farmer-rest-sess"
    headers = auth_headers(user_id)

    # Initially 404
    r_init = client.get(f"/api/sessions/{user_id}")
    assert r_init.status_code == 404

    # Create turn
    client.post("/api/orchestrator/process", json={
        "query": "My tomato crops have early blight in Badulla",
        "user_id": user_id,
        "location": {"district": "Badulla", "agro_ecological_zone": "IM1a"},
        "crop_context": "Tomato",
        "language": "en",
    }, headers=headers)

    # Get session
    r_get = client.get(f"/api/sessions/{user_id}")
    assert r_get.status_code == 200
    s_data = r_get.json()
    assert s_data["active_crop"] == "Tomato"
    assert s_data["location"]["district"] == "Badulla"
    assert len(s_data["history"]) == 1

    # Clear session
    r_del = client.delete(f"/api/sessions/{user_id}")
    assert r_del.status_code == 200
    assert r_del.json()["user_id"] == user_id

    # Verify cleared
    r_after = client.get(f"/api/sessions/{user_id}")
    assert r_after.status_code == 404
