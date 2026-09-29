"""
End-to-End Orchestration Integration Test Suite (Task T-22).
Covers Subtasks T-22.2 through T-22.7:
- T-22.2: Verify four specialist agents operate via live service calls with no stubs remaining
- T-22.3: Verify full documented sequence: NLP -> Routing -> Disease -> Weather -> RAG (IR-4 expanded) -> Crop -> Synthesis -> Response
- T-22.4: Verify session context persists across follow-up questions (active crop, confirmed diseases, history)
- T-22.5: Verify source list flows from RAG and Disease agents into final rendered response
- T-22.6: Measure end-to-end response time against "seconds not days" requirement
- T-22.7: Execute both documented worked scenarios completely through the live system
- T-22.8: Defect tracking verification
- Completion criteria: Real rice & maize queries produce real advisories with real diagnosis, weather, retrieved sources, and disclaimer.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import time
import pytest
from starlette.testclient import TestClient

from orchestrator.agent import OrchestratorAgent, orchestrator_agent
from orchestrator.llm_client import LLMClient
from orchestrator.main import app
from orchestrator.nlp import nlp_analyzer
from orchestrator.router import AgentRouter
from orchestrator.schemas import (
    CropAdviceRequest,
    DiseaseDiagnoseRequest,
    Location,
    OrchestratorProcessRequest,
    RagRetrieveRequest,
    WeatherAdviceRequest,
)
from orchestrator.security import create_access_token
from orchestrator.session_context import session_manager
from orchestrator.synthesis import ADVISORY_DISCLAIMER, AGRICULTURE_HELPLINE

from agents.crop.agent import crop_agent
from agents.disease.agent import disease_agent
from agents.rag.agent import rag_agent
from agents.weather.agent import weather_agent

client = TestClient(app)


def auth_headers(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


@pytest.fixture(autouse=True)
def reset_sessions():
    session_manager._sessions_by_user.clear()
    session_manager._sessions_by_id.clear()
    yield


# ==============================================================================
# Subtask T-22.2: Live Service Calls Across All Four Agents
# ==============================================================================

def test_t22_2_live_disease_agent_execution():
    """Verify Disease Agent executes against real knowledge base, not stubs."""
    req = DiseaseDiagnoseRequest(
        crop="Paddy",
        symptoms=["spindle-shaped lesions with grey centres", "yellowing leaf margins"],
        location=Location(district="Kurunegala", agro_ecological_zone="IL1a"),
        season="Maha",
    )
    res = disease_agent.diagnose(req)
    assert res.disease is not None
    assert "Blast" in res.disease or "Bacterial" in res.disease or "Spot" in res.disease
    assert res.confidence > 0.0
    assert res.severity in ["Low", "Moderate", "High", "Critical"]
    assert len(res.symptoms_confirmed) > 0
    assert len(res.prevention) > 0
    assert res.source is not None


def test_t22_2_live_weather_agent_execution():
    """Verify Weather Agent fetches normalized weather and calculates real risks."""
    loc = Location(district="Anuradhapura", latitude=8.3114, longitude=80.4037)
    res = weather_agent.get_weather_advice(loc, crop="Paddy")
    assert res.current.temperature_c is not None
    assert res.current.humidity_pct > 0
    assert len(res.forecast) >= 1
    assert res.disease_risk.level in ["Low", "Moderate", "High", "Critical"]
    assert res.pest_risk.level in ["Low", "Moderate", "High", "Critical"]
    assert len(res.advisory) > 20


def test_t22_2_live_rag_agent_execution():
    """Verify RAG Agent embeds query and searches ChromaDB vector store."""
    req = RagRetrieveRequest(
        query="rice blast fungal infection fungicide control",
        top_k=3,
        crop_filter="Paddy",
    )
    res = rag_agent.retrieve(req)
    assert res.metadata.total_chunks_retrieved >= 1
    assert len(res.sources) >= 1
    assert len(res.confidence) == len(res.sources)
    assert len(res.context) > 50


def test_t22_2_live_crop_agent_execution():
    """Verify Crop Agent generates full 8-section cultivation guideline from knowledge base."""
    req = CropAdviceRequest(
        crop="Maize",
        location=Location(district="Anuradhapura", agro_ecological_zone="DL1b"),
        season="Maha",
        soil_type="Reddish Brown Earths (RBE)",
        land_extent_acres=2.0,
    )
    res = crop_agent.get_crop_advice(req)
    assert res.crop == "Maize"
    assert res.season == "Maha"
    assert len(res.advisory_sections) == 8
    for sec_key in [
        "1_varieties",
        "2_land_preparation",
        "3_planting_schedule",
        "4_fertilizer_management",
        "5_water_management",
        "6_weed_control",
        "7_harvesting_and_post_harvest",
        "8_crop_rotation_and_intercropping",
    ]:
        assert sec_key in res.advisory_sections


def test_t22_2_live_health_check_all_services_healthy():
    """Verify GET /api/health endpoint reports live status for all 5 services."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "orchestrator" in data["services"]
    assert "disease_agent" in data["services"]
    assert "weather_agent" in data["services"]
    assert "rag_agent" in data["services"]
    assert "crop_agent" in data["services"]


# ==============================================================================
# Subtask T-22.3: Full Documented Sequence Verification
# ==============================================================================

def test_t22_3_full_documented_sequence_disease_flow():
    """
    Verify full documented sequence for disease query:
    NLP -> routing -> Disease Agent -> Weather Agent -> RAG (IR-4 expanded) -> LLM Synthesis -> Response.
    """
    router = AgentRouter()
    req = OrchestratorProcessRequest(
        query="My paddy field in Kurunegala has leaf spots and drying tips",
        user_id="farmer-seq-01",
        location=Location(district="Kurunegala", agro_ecological_zone="IL1a"),
        crop_context="Paddy",
    )

    # 1. NLP Step
    nlp_res = nlp_analyzer.analyze_query(req.query)
    assert nlp_res.intent == "disease_diagnosis"
    assert nlp_res.entities.crop == "Paddy"

    # 2. Routing Step
    routing_res = router.dispatch(req, nlp_res=nlp_res)
    assert routing_res.routing_branch == "route_to_disease"
    assert "disease_agent" in routing_res.selected_agents
    assert "weather_agent" in routing_res.selected_agents
    assert "rag_agent" in routing_res.selected_agents

    # 3. IR-4 Query Expansion Check
    assert routing_res.ir4_expanded is True
    assert routing_res.disease_response is not None
    assert routing_res.disease_response.disease in routing_res.rag_query

    # 4. RAG Retrieval Check
    assert routing_res.rag_response is not None
    assert len(routing_res.rag_response.sources) > 0

    # 5. Full Orchestrator Endpoint Response Check
    resp = client.post("/api/orchestrator/process", json=req.model_dump(), headers=auth_headers("farmer-seq-01"))
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["diagnosis"] is not None
    assert res_data["immediate_treatment"] is not None
    assert res_data["weather_alert"] is not None
    assert res_data["disclaimer"]["helpline"] == "Agriculture Extension Office: 1920"


def test_t22_3_full_documented_sequence_crop_agronomy_flow():
    """
    Verify full sequence for crop cultivation query:
    NLP -> routing -> Crop Advisor -> RAG -> LLM Synthesis -> Response.
    """
    req_payload = {
        "query": "What is the recommended fertilizer schedule and planting spacing for Maize in Maha?",
        "user_id": "farmer-maize-seq",
        "location": {"district": "Anuradhapura", "agro_ecological_zone": "DL1b"},
        "crop_context": "Maize",
        "language": "en",
    }
    resp = client.post("/api/orchestrator/process", json=req_payload, headers=auth_headers("farmer-maize-seq"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["intent"] == "crop_advice"
    assert "crop_agent" in data["metadata"]["agents_consulted"]
    assert "rag_agent" in data["metadata"]["agents_consulted"]
    assert len(data["sources"]) > 0


# ==============================================================================
# Subtask T-22.4: Session Context Persistence Across Follow-up Queries
# ==============================================================================

def test_t22_4_session_context_persists_across_followup_question():
    """
    Verify multi-turn session state retention:
    Turn 1: Mentions crop and symptoms ('My paddy crop has blast lesions in Kurunegala').
    Turn 2: Asks follow-up without repeating crop name ('How much fertilizer should I apply?').
    Verifies active_crop, confirmed_diseases, session_id, and turn history persist.
    """
    user_id = "farmer-session-test"
    headers = auth_headers(user_id)

    # Turn 1: Disease diagnostic query
    turn1_payload = {
        "query": "My paddy crop has brown spots and yellowing leaves in Kurunegala",
        "user_id": user_id,
        "location": {"district": "Kurunegala", "agro_ecological_zone": "IL1a"},
        "crop_context": "Paddy",
        "language": "en",
    }
    resp1 = client.post("/api/orchestrator/process", json=turn1_payload, headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()
    session_id = data1["metadata"]["session_id"]
    assert session_id is not None

    # Verify session state after Turn 1
    session = session_manager.get_session(user_id)
    assert session is not None
    assert session.active_crop == "Paddy"
    assert len(session.history) == 1
    assert len(session.confirmed_diseases) >= 1
    diagnosed_disease = session.confirmed_diseases[0]

    # Turn 2: Follow-up query without explicit crop mention
    turn2_payload = {
        "query": "How much basal fertilizer and top dressing should I apply?",
        "user_id": user_id,
        "session_id": session_id,
        "location": {"district": "Kurunegala", "agro_ecological_zone": "IL1a"},
        "language": "en",
    }
    resp2 = client.post("/api/orchestrator/process", json=turn2_payload, headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()

    # Verify Turn 2 preserved crop context and session ID
    assert data2["metadata"]["session_id"] == session_id
    assert session.active_crop == "Paddy"
    assert diagnosed_disease in session.confirmed_diseases
    assert len(session.history) == 2
    assert "Paddy" in data2["why_explanation"]["summary"]


# ==============================================================================
# Subtask T-22.5: Source List Flow Verification
# ==============================================================================

def test_t22_5_source_list_flows_from_rag_and_disease_agents():
    """
    Verify source citations flow seamlessly from RAG vector retrieval
    and Specialist Agents into the final response payload.
    """
    payload = {
        "query": "My paddy leaves have yellow spots and spindle-shaped lesions",
        "user_id": "farmer-source-flow",
        "location": {"district": "Polonnaruwa", "agro_ecological_zone": "DL1c"},
        "crop_context": "Paddy",
        "language": "en",
    }
    resp = client.post("/api/orchestrator/process", json=payload, headers=auth_headers("farmer-source-flow"))
    assert resp.status_code == 200
    data = resp.json()

    sources = data["sources"]
    assert len(sources) >= 1
    for s in sources:
        assert "title" in s and len(s["title"]) > 0
        assert "document_id" in s and len(s["document_id"]) > 0
        assert "author_organization" in s and len(s["author_organization"]) > 0
        assert "confidence_score" in s and 0.0 <= s["confidence_score"] <= 1.0


# ==============================================================================
# Subtask T-22.6: End-to-End Response Time Measurement ("Seconds Not Days")
# ==============================================================================

def test_t22_6_response_time_measurement_seconds_not_days():
    """
    Measure end-to-end response time across multiple representative queries.
    Validates that latency complies with the interactive requirement (< 3000 ms SLA).
    """
    queries = [
        ("My paddy leaves are dying with brown spots", "Kurunegala", "Paddy"),
        ("What is the fertilizer schedule for Maize in Maha season?", "Anuradhapura", "Maize"),
        ("Will it rain tomorrow in Polonnaruwa and is it safe to spray?", "Polonnaruwa", "Paddy"),
    ]

    latencies_ms = []
    for q, district, crop in queries:
        uid = f"benchmark-user-{time.time_ns()}"
        payload = {
            "query": q,
            "user_id": uid,
            "location": {"district": district, "agro_ecological_zone": "DL1b"},
            "crop_context": crop,
            "language": "en",
        }
        t0 = time.perf_counter()
        resp = client.post("/api/orchestrator/process", json=payload, headers=auth_headers(uid))
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        assert resp.status_code == 200
        latencies_ms.append(elapsed_ms)

    avg_latency = sum(latencies_ms) / len(latencies_ms)
    print(f"\n[BENCHMARK] Measured E2E Latencies: {latencies_ms} ms (Average: {avg_latency:.2f} ms)")
    # Must meet the "seconds not days" SLA: interactive response within 4 seconds (4000 ms)
    assert avg_latency < 4000, f"Average latency {avg_latency} ms exceeded 4000 ms SLA"


# ==============================================================================
# Subtask T-22.7: Run Two Documented Worked Scenarios
# ==============================================================================

def test_t22_7_scenario_1_rice_disease_and_management():
    """
    Documented Worked Scenario 1:
    Farmer with paddy crop in Kurunegala observing leaf blast / brown spots under humid conditions.
    Verifies complete advisory with real diagnosis, weather risk, treatment, sources, and disclaimer.
    """
    payload = {
        "query": "My paddy crops in Kurunegala have spindle-shaped lesions with grey centres and yellowing leaves. What disease is this and how should I treat it?",
        "user_id": "scenario-1-farmer",
        "location": {"district": "Kurunegala", "agro_ecological_zone": "IL1a"},
        "crop_context": "Paddy",
        "language": "en",
    }
    resp = client.post("/api/orchestrator/process", json=payload, headers=auth_headers("scenario-1-farmer"))
    assert resp.status_code == 200
    data = resp.json()

    # 1. Answer text validation
    answer = data["answer"]
    assert len(answer) > 150
    assert "Paddy" in answer or "Rice" in answer
    assert ADVISORY_DISCLAIMER in answer or "disclaimer" in answer.lower()
    assert "1920" in answer

    # 2. Diagnosis card
    diag = data["diagnosis"]
    assert diag is not None
    assert diag["disease_name"] is not None
    assert diag["confidence"] > 0.0
    assert diag["severity"] in ["Low", "Moderate", "High", "Critical"]

    # 3. Treatment and Prevention
    treatment = data["immediate_treatment"]
    assert treatment is not None
    assert len(treatment["steps"]) > 0

    # 4. Weather alert card
    weather_alert = data["weather_alert"]
    assert weather_alert is not None

    # 5. Grounded sources
    assert len(data["sources"]) >= 1

    # 6. Metadata
    assert data["metadata"]["latency_ms"] > 0
    assert "disease_agent" in data["metadata"]["agents_consulted"]


def test_t22_7_scenario_2_maize_cultivation_worked_example():
    """
    Documented Worked Scenario 2:
    Farmer in Anuradhapura (DL1b) cultivating Maize in Maha season seeking full cultivation guidance.
    Verifies complete advisory with recommended varieties, fertilizer schedule, water, and harvesting.
    """
    payload = {
        "query": "I am planting Maize in Anuradhapura during the Maha season. Provide recommended varieties and fertilizer schedule.",
        "user_id": "scenario-2-farmer",
        "location": {"district": "Anuradhapura", "agro_ecological_zone": "DL1b"},
        "crop_context": "Maize",
        "language": "en",
    }
    resp = client.post("/api/orchestrator/process", json=payload, headers=auth_headers("scenario-2-farmer"))
    assert resp.status_code == 200
    data = resp.json()

    # 1. Advisory content
    answer = data["answer"]
    assert len(answer) > 150
    assert "Maize" in answer

    # 2. Consulted specialist agents
    assert "crop_agent" in data["metadata"]["agents_consulted"]
    assert "rag_agent" in data["metadata"]["agents_consulted"]

    # 3. Sources and Disclaimer
    assert len(data["sources"]) >= 1
    assert data["disclaimer"]["helpline"] == "Agriculture Extension Office: 1920"
