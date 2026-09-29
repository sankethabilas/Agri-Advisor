"""
End-to-End Test Suite for Agri-Advisor Orchestrator Service (Task T-06).
Tests FastAPI endpoints, stub agent chains, multi-turn session context, and error envelopes.
"""

import json
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from orchestrator.main import app
from orchestrator.security import create_access_token
from orchestrator.session_context import session_manager

client = TestClient(app)
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def auth_headers(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def clean_sessions():
    """Ensure clean session state before each test."""
    session_manager._sessions_by_user.clear()
    session_manager._sessions_by_id.clear()
    yield


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "orchestrator_process" in data["endpoints"]
    assert "X-Request-ID" in response.headers


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "services" in data
    assert "orchestrator" in data["services"]
    assert "disease_agent" in data["services"]
    assert "weather_agent" in data["services"]
    assert "rag_agent" in data["services"]
    assert "crop_agent" in data["services"]


def test_orchestrator_process_full_chain_t06_2_and_t06_7():
    """Test full process request matches frozen T-02.1 & T-02.6 contracts."""
    req_payload = load_fixture("orchestrator_process_request.json")
    response = client.post("/api/orchestrator/process", json=req_payload, headers=auth_headers(req_payload["user_id"]))

    assert response.status_code == 200
    data = response.json()

    # Verify Response Contract Fields
    assert "answer" in data and isinstance(data["answer"], str) and len(data["answer"]) > 0
    assert "sources" in data and isinstance(data["sources"], list) and len(data["sources"]) > 0
    assert "weather_alert" in data and isinstance(data["weather_alert"], dict)
    assert "metadata" in data and isinstance(data["metadata"], dict)

    # Verify Metadata
    meta = data["metadata"]
    assert meta["user_id"] == req_payload["user_id"]
    assert meta["intent"] in ["disease_diagnosis", "weather_inquiry", "crop_cultivation", "general_farming", "mixed"]
    assert 0.0 <= meta["confidence"] <= 1.0
    assert len(meta["agents_consulted"]) > 0
    assert meta["latency_ms"] >= 1
    assert "timestamp" in meta

    # Verify Headers
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time-Ms" in response.headers


def test_session_context_persistence_across_turns_t06_5():
    """Test that session context retains crop context and history across consecutive turns."""
    user_id = "farmer-session-test-01"

    # Turn 1: Farmer mentions crop issue with Paddy
    req_1 = {
        "query": "My paddy leaves have yellow and brown spots",
        "user_id": user_id,
        "location": {"district": "Anuradhapura", "agro_ecological_zone": "DL1b"},
        "language": "en",
    }
    res_1 = client.post("/api/orchestrator/process", json=req_1, headers=auth_headers(user_id))
    assert res_1.status_code == 200
    data_1 = res_1.json()
    session_id = data_1["metadata"]["session_id"]
    assert session_id is not None

    # Inspect session via API
    sess_res = client.get(f"/api/sessions/{user_id}")
    assert sess_res.status_code == 200
    sess_data = sess_res.json()
    assert sess_data["turn_count"] == 1
    assert sess_data["active_crop"] == "Paddy"

    # Turn 2: Farmer follows up without repeating the crop name
    req_2 = {
        "query": "What fertilizer should I apply next week?",
        "user_id": user_id,
        "session_id": session_id,
        "location": {"district": "Anuradhapura", "agro_ecological_zone": "DL1b"},
        "language": "en",
    }
    res_2 = client.post("/api/orchestrator/process", json=req_2, headers=auth_headers(user_id))
    assert res_2.status_code == 200
    data_2 = res_2.json()
    assert data_2["metadata"]["session_id"] == session_id

    # Inspect session turn count after turn 2
    sess_res_2 = client.get(f"/api/sessions/{user_id}")
    assert sess_res_2.status_code == 200
    sess_data_2 = sess_res_2.json()
    assert sess_data_2["turn_count"] == 2
    assert sess_data_2["active_crop"] == "Paddy"

    # Test Session Clear
    del_res = client.delete(f"/api/sessions/{user_id}")
    assert del_res.status_code == 200


def test_disease_agent_stub_endpoint_t06_4():
    req_payload = load_fixture("disease_diagnose_request.json")
    response = client.post("/api/disease/diagnose", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    assert "disease" in data
    assert "treatment" in data
    assert "chemical" in data["treatment"]
    assert "organic" in data["treatment"]
    assert "cultural" in data["treatment"]
    assert data["severity"] in ["Low", "Moderate", "High", "Critical"]


def test_weather_agent_stub_endpoint_t06_4():
    req_payload = load_fixture("weather_advice_request.json")
    response = client.post("/api/weather/advice", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    assert "current" in data
    assert "forecast" in data
    assert "disease_risk" in data
    assert "pest_risk" in data
    assert "alerts" in data


def test_rag_agent_stub_endpoint_t06_4():
    req_payload = load_fixture("rag_retrieve_request.json")
    response = client.post("/api/rag/retrieve", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    assert "context" in data
    assert "sources" in data
    assert "confidence" in data
    assert len(data["sources"]) == len(data["confidence"])


def test_crop_agent_stub_endpoint_t06_4():
    req_payload = load_fixture("crop_advice_request.json")
    response = client.post("/api/crop/advice", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    assert "advisory_sections" in data
    sections = data["advisory_sections"]
    for i in range(1, 9):
        key = [k for k in sections.keys() if k.startswith(f"{i}_")]
        assert len(key) == 1, f"Missing advisory section {i}"


def test_validation_error_envelope_t02_7():
    """Test that ill-formed requests return the standardized RFC 7807 error format."""
    invalid_req = {
        "query": "",  # Empty query violates min_length=1
        "user_id": "test-user",
        # Missing required location field
    }
    response = client.post(
        "/api/orchestrator/process",
        json=invalid_req,
        headers=auth_headers(invalid_req["user_id"]),
    )
    assert response.status_code in [400, 422]
    data = response.json()
    assert "error" in data
    err = data["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert "status_code" in err
    assert "timestamp" in err
    assert "request_id" in err
    assert "details" in err and len(err["details"]) > 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
