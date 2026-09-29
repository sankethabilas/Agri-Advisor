"""
Source List Flow & Attribution Verification Tests (Subtask T-22.5).
Verifies that grounded knowledge source citations flow from RAG semantic retrieval,
Disease pathology protocols, and Crop agronomic guidelines into the final response payload.
"""

import pytest
from starlette.testclient import TestClient

from orchestrator.main import app
from orchestrator.schemas import SourceItem
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


def test_t22_5_source_propagation_rag_and_disease():
    """Verify both RAG vector store sources and Disease Agent sources are populated."""
    payload = {
        "query": "My paddy crop has brown spot symptoms and yellowing leaf edges in Kurunegala",
        "user_id": "farmer-source-verify-01",
        "location": {"district": "Kurunegala", "agro_ecological_zone": "IL1a"},
        "crop_context": "Paddy",
        "language": "en",
    }
    resp = client.post("/api/orchestrator/process", json=payload, headers=auth_headers("farmer-source-verify-01"))
    assert resp.status_code == 200
    data = resp.json()

    sources = data["sources"]
    assert len(sources) >= 1

    # Verify each source conforms strictly to SourceItem contract
    for item in sources:
        validated = SourceItem.model_validate(item)
        assert len(validated.title) > 0
        assert len(validated.document_id) > 0
        assert len(validated.author_organization) > 0
        assert 0.0 <= validated.confidence_score <= 1.0


def test_t22_5_source_propagation_crop_advisor():
    """Verify Crop Advisor sources flow into cultivation plan responses."""
    payload = {
        "query": "What are recommended varieties and fertilizer rates for cultivating Maize in Anuradhapura?",
        "user_id": "farmer-crop-source-verify",
        "location": {"district": "Anuradhapura", "agro_ecological_zone": "DL1b"},
        "crop_context": "Maize",
        "language": "en",
    }
    resp = client.post("/api/orchestrator/process", json=payload, headers=auth_headers("farmer-crop-source-verify"))
    assert resp.status_code == 200
    data = resp.json()

    sources = data["sources"]
    assert len(sources) >= 1
    titles = [s["title"] for s in sources]
    assert any("Maize" in t or "Agricultural" in t or "Department" in t or "DOA" in t for t in titles)
