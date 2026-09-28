"""
Tests for Agri-Advisor Routing Logic & Specialist Agent Dispatch (Task T-14).
Validates T-14.1 through T-14.8:
- T-14.1: route_to_disease() calling Disease and Weather agents
- T-14.2: route_to_weather() calling Weather and RAG agents only
- T-14.3: route_to_crop_advisor() calling Crop Advisor and RAG agents
- T-14.4: route_to_multiple() for mixed queries with documented selection rules
- T-14.5: Unconditional RAG retrieval per Business Rule BR-4
- T-14.6: RAG query expansion with Disease Agent findings per Rule IR-4
- T-14.7: Structured RoutingResult object
- T-14.8: Routing decision logging
"""

import logging
import pytest
from starlette.testclient import TestClient

from orchestrator.main import app
from orchestrator.nlp import analyze_query
from orchestrator.router import (
    AgentRouter,
    RoutingResult,
    agent_router,
    dispatch_query,
    route_to_crop_advisor,
    route_to_disease,
    route_to_multiple,
    route_to_weather,
)
from orchestrator.schemas import (
    CropAdviceRequest,
    CropAdviceResponse,
    DiseaseDiagnoseRequest,
    DiseaseDiagnoseResponse,
    Location,
    OrchestratorProcessRequest,
    RagRetrieveRequest,
    RagRetrieveResponse,
    WeatherAdviceRequest,
    WeatherAdviceResponse,
)
from orchestrator.session_context import SessionManager, session_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_sessions():
    session_manager._sessions_by_user.clear()
    session_manager._sessions_by_id.clear()
    yield


@pytest.fixture
def mock_router():
    """Router with mock callables for isolated unit testing."""
    disease_calls = []
    weather_calls = []
    crop_calls = []
    rag_calls = []

    def mock_disease(req: DiseaseDiagnoseRequest) -> DiseaseDiagnoseResponse:
        disease_calls.append(req)
        return DiseaseDiagnoseResponse.model_validate({
            "disease": "Paddy Blast (Pyricularia oryzae)",
            "confidence": 0.92,
            "severity": "High",
            "treatment": {
                "chemical": [{"name": "Tebuconazole 250 EC", "dosage": "15ml/16L", "instructions": "Spray at onset", "pre_harvest_interval_days": 14}],
                "organic": [{"name": "Neem Oil 5%", "dosage": "50ml/L", "instructions": "Foliar application"}],
                "cultural": [{"practice": "Water Management", "description": "Drain excess water"}]
            },
            "prevention": ["Use certified seed", "Avoid excess nitrogen"],
            "source": "DOA Rice Pathology Handbook 2023",
            "symptoms_confirmed": ["yellow spots", "leaf lesions"],
        })

    def mock_weather(req: WeatherAdviceRequest) -> WeatherAdviceResponse:
        weather_calls.append(req)
        return WeatherAdviceResponse.model_validate({
            "current": {
                "temperature_c": 29.5,
                "humidity_pct": 82,
                "rainfall_mm": 5.0,
                "wind_speed_kmh": 12.0,
                "wind_direction": "NE",
                "condition": "Light rain",
                "icon": "10d",
                "timestamp": "2026-09-28T12:00:00Z"
            },
            "forecast": [{
                "date": "2026-09-29",
                "temp_min_c": 24.0,
                "temp_max_c": 31.0,
                "rainfall_mm": 15.0,
                "rainfall_prob_pct": 75,
                "humidity_pct": 85,
                "wind_speed_kmh": 14.0,
                "condition": "Rain showers"
            }],
            "disease_risk": {
                "level": "High",
                "score": 0.80,
                "susceptible_diseases": ["Paddy Blast", "Brown Spot"],
                "contributing_factors": ["High humidity (>80%) and rainfall expected"]
            },
            "pest_risk": {
                "level": "Moderate",
                "score": 0.50,
                "susceptible_pests": ["Brown Planthopper"],
                "contributing_factors": ["Moderate temperature"]
            },
            "advisory": "Postpone pesticide spraying before rain; ensure drainage.",
            "alerts": []
        })

    def mock_crop(req: CropAdviceRequest) -> CropAdviceResponse:
        crop_calls.append(req)
        return CropAdviceResponse.model_validate({
            "crop": req.crop,
            "season": req.season,
            "agro_ecological_zone": "DL1b",
            "soil_type": req.soil_type or "Reddish Brown Earths",
            "land_extent_acres": 1.0,
            "advisory_sections": {
                "1_land_preparation": "Plough 3 weeks before sowing.",
                "2_seed_treatment": "Soak seeds for 24 hours."
            },
            "source": "DOA Crop Production Guide",
            "generated_at": "2026-09-28T12:00:00Z"
        })

    def mock_rag(req: RagRetrieveRequest) -> RagRetrieveResponse:
        rag_calls.append(req)
        return RagRetrieveResponse.model_validate({
            "context": "Paddy blast management requires fungicide and water control.",
            "sources": [{
                "id": "DOA-PADDY-01",
                "title": "DOA Paddy Blast Management Guide",
                "content": "Apply Tebuconazole at first symptom sign.",
                "crop": req.crop_filter or "Paddy",
                "category": "Pathology",
                "language": "en",
                "source": "DOA",
                "source_id": "DOA-GUIDE-2023",
                "region": "Dry Zone",
                "season": "Maha",
                "score": 0.91
            }],
            "confidence": [0.91],
            "metadata": {
                "total_chunks_retrieved": 1,
                "query_embedding_model": "all-MiniLM-L6-v2",
                "vector_distance_metric": "cosine"
            }
        })

    router = AgentRouter(
        disease_agent=mock_disease,
        weather_agent=mock_weather,
        crop_agent=mock_crop,
        rag_agent=mock_rag,
    )
    router._disease_calls = disease_calls
    router._weather_calls = weather_calls
    router._crop_calls = crop_calls
    router._rag_calls = rag_calls
    return router


# ==============================================================================
# T-14.1: route_to_disease() calling Disease and Weather agents
# ==============================================================================

def test_t14_1_route_to_disease(mock_router):
    """
    T-14.1 Completion Criteria:
    A disease query demonstrably calls the Disease, Weather and RAG agents.
    """
    req = OrchestratorProcessRequest(
        query="My paddy leaves have yellow spots and blast lesions",
        user_id="farmer-101",
        location=Location(district="Anuradhapura", agro_ecological_zone="DL1b"),
        crop_context="Paddy",
    )
    result = mock_router.dispatch(req)

    assert result.intent == "disease_diagnosis"
    assert "disease_agent" in result.selected_agents
    assert "weather_agent" in result.selected_agents
    assert "rag_agent" in result.selected_agents
    assert "crop_agent" not in result.selected_agents

    assert result.disease_response is not None
    assert result.disease_response.disease == "Paddy Blast (Pyricularia oryzae)"
    assert result.weather_response is not None
    assert result.crop_response is None
    assert result.rag_response is not None

    assert len(mock_router._disease_calls) == 1
    assert len(mock_router._weather_calls) == 1
    assert len(mock_router._crop_calls) == 0
    assert len(mock_router._rag_calls) == 1


# ==============================================================================
# T-14.2: route_to_weather() calling Weather and RAG agents only
# ==============================================================================

def test_t14_2_route_to_weather(mock_router):
    """
    T-14.2 Completion Criteria:
    A weather query calls only Weather and RAG agents.
    """
    req = OrchestratorProcessRequest(
        query="Will it rain tomorrow in Kurunegala?",
        user_id="farmer-102",
        location=Location(district="Kurunegala", agro_ecological_zone="IL1a"),
    )
    result = mock_router.dispatch(req)

    assert result.intent in ["weather_query", "weather_inquiry"]
    assert result.selected_agents == ["weather_agent", "rag_agent"]
    assert "disease_agent" not in result.selected_agents
    assert "crop_agent" not in result.selected_agents

    assert result.weather_response is not None
    assert result.disease_response is None
    assert result.crop_response is None
    assert result.rag_response is not None

    assert len(mock_router._weather_calls) == 1
    assert len(mock_router._disease_calls) == 0
    assert len(mock_router._crop_calls) == 0
    assert len(mock_router._rag_calls) == 1


# ==============================================================================
# T-14.3: route_to_crop_advisor() calling Crop Advisor and RAG agents
# ==============================================================================

def test_t14_3_route_to_crop_advisor(mock_router):
    """
    T-14.3 Completion Criteria:
    A crop cultivation query calls the Crop Advisor and RAG agents.
    """
    req = OrchestratorProcessRequest(
        query="What is the recommended fertilizer schedule for Maize in Maha season?",
        user_id="farmer-103",
        location=Location(district="Monaragala", agro_ecological_zone="DL1b"),
        crop_context="Maize",
    )
    result = mock_router.dispatch(req)

    assert result.intent in ["crop_advice", "crop_cultivation"]
    assert "crop_agent" in result.selected_agents
    assert "rag_agent" in result.selected_agents
    assert "disease_agent" not in result.selected_agents

    assert result.crop_response is not None
    assert result.disease_response is None
    assert result.rag_response is not None

    assert len(mock_router._crop_calls) == 1
    assert len(mock_router._disease_calls) == 0
    assert len(mock_router._rag_calls) == 1


# ==============================================================================
# T-14.4: route_to_multiple() for mixed queries with intent score selection
# ==============================================================================

def test_t14_4_route_to_multiple_mixed_query(mock_router):
    """
    T-14.4 Completion Criteria:
    Mixed queries select agents based on intent score thresholds (>= 0.35) and entities.
    """
    # Mixed query 1: Weather + Disease
    req_disease_weather = OrchestratorProcessRequest(
        query="Will the heavy rain worsen the fungal blast in my paddy fields?",
        user_id="farmer-104",
        location=Location(district="Polonnaruwa", agro_ecological_zone="DL1c"),
        crop_context="Paddy",
    )
    result_dw = mock_router.dispatch(req_disease_weather)

    assert result_dw.intent in ["mixed_query", "mixed"]
    assert "disease_agent" in result_dw.selected_agents
    assert "weather_agent" in result_dw.selected_agents
    assert "rag_agent" in result_dw.selected_agents

    assert result_dw.disease_response is not None
    assert result_dw.weather_response is not None
    assert result_dw.rag_response is not None

    # Mixed query 2: Weather + Crop Cultivation
    req_crop_weather = OrchestratorProcessRequest(
        query="Should I apply urea fertilizer before the rain in Kurunegala?",
        user_id="farmer-105",
        location=Location(district="Kurunegala", agro_ecological_zone="IL1a"),
        crop_context="Paddy",
    )
    result_cw = mock_router.dispatch(req_crop_weather)

    assert result_cw.intent in ["mixed_query", "mixed"]
    assert "crop_agent" in result_cw.selected_agents
    assert "weather_agent" in result_cw.selected_agents
    assert "rag_agent" in result_cw.selected_agents


# ==============================================================================
# T-14.5: Unconditional RAG Agent Call per Business Rule BR-4
# ==============================================================================

def test_t14_5_unconditional_rag_agent_call_br4(mock_router):
    """
    T-14.5 Completion Criteria:
    RAG agent is called unconditionally for every query type outside intent branches.
    """
    queries = [
        ("My tomato leaves have brown spots", "disease_diagnosis"),
        ("Weather forecast for Badulla", "weather_query"),
        ("Seed rate for mung bean in Yala", "crop_advice"),
        ("Rain forecast and paddy leaf blast", "mixed_query"),
        ("How do I contact the DOA extension office?", "general_query"),
    ]

    for q, expected_intent in queries:
        req = OrchestratorProcessRequest(
            query=q,
            user_id="test-br4-user",
            location=Location(district="Matale", agro_ecological_zone="IM1a"),
        )
        res = mock_router.dispatch(req)
        assert "rag_agent" in res.selected_agents, f"RAG agent was not called for query '{q}' (intent: {res.intent})"
        assert res.rag_response is not None, f"RAG response missing for query '{q}'"


# ==============================================================================
# T-14.6: RAG Query Expansion with Disease Finding per Rule IR-4
# ==============================================================================

def test_t14_6_rag_query_expansion_ir4(mock_router):
    """
    T-14.6 Completion Criteria:
    Expand RAG query with Disease Agent's finding before retrieval (Rule IR-4).
    """
    # 1. Disease Query: IR-4 should expand the query
    disease_req = OrchestratorProcessRequest(
        query="My paddy leaves have yellow spots",
        user_id="farmer-ir4-01",
        location=Location(district="Anuradhapura", agro_ecological_zone="DL1b"),
        crop_context="Paddy",
    )
    res_disease = mock_router.dispatch(disease_req)

    assert res_disease.ir4_expanded is True
    assert "Paddy Blast (Pyricularia oryzae)" in res_disease.rag_query
    # Check that RAG agent actually received the expanded query
    last_rag_call = mock_router._rag_calls[-1]
    assert "Paddy Blast (Pyricularia oryzae)" in last_rag_call.query

    # 2. Weather Query: IR-4 should NOT expand the query
    weather_req = OrchestratorProcessRequest(
        query="Will it rain tomorrow in Galle?",
        user_id="farmer-ir4-02",
        location=Location(district="Galle", agro_ecological_zone="WL1a"),
    )
    res_weather = mock_router.dispatch(weather_req)

    assert res_weather.ir4_expanded is False
    assert res_weather.rag_query == "Will it rain tomorrow in Galle?"


# ==============================================================================
# T-14.7: Structured Routing Result Object
# ==============================================================================

def test_t14_7_structured_routing_result_object(mock_router):
    """
    T-14.7 Completion Criteria:
    Collect all agent results into a single structured routing result object.
    """
    req = OrchestratorProcessRequest(
        query="My tomato leaves have yellow spots and wilting",
        user_id="farmer-struct-01",
        session_id="sess-custom-uuid",
        location=Location(district="Badulla", agro_ecological_zone="IU3c"),
        crop_context="Tomato",
    )
    result = mock_router.dispatch(req)

    assert isinstance(result, RoutingResult)
    assert result.query == req.query
    assert result.user_id == req.user_id
    assert result.session_id == req.session_id
    assert result.intent == "disease_diagnosis"
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.intent_scores, dict)
    assert isinstance(result.entities, dict)
    assert isinstance(result.selected_agents, list)
    assert isinstance(result.latencies_ms, dict)
    assert result.total_latency_ms >= 0
    assert "br4_rag_unconditional" in result.routing_decision
    assert result.routing_decision["br4_rag_unconditional"] is True


# ==============================================================================
# T-14.8: Logging the Routing Decision
# ==============================================================================

def test_t14_8_routing_decision_logging(mock_router, caplog):
    """
    T-14.8 Completion Criteria:
    Log the routing decision for each query for debugging and demonstration.
    """
    caplog.set_level(logging.INFO, logger="agri_advisor.router")

    req = OrchestratorProcessRequest(
        query="Is there a heavy rain warning for Anuradhapura?",
        user_id="farmer-log-01",
        location=Location(district="Anuradhapura", agro_ecological_zone="DL1b"),
    )
    mock_router.dispatch(req)

    found_log = False
    for record in caplog.records:
        if "[ROUTING DECISION]" in record.message:
            assert "farmer-log-01" in record.message
            assert "weather_agent" in record.message
            found_log = True
            break

    assert found_log, "Routing decision log was not found in logger output"


# ==============================================================================
# End-to-End Orchestration Integration via FastAPI
# ==============================================================================

def test_end_to_end_orchestrator_with_real_router():
    """Verify that full orchestrator process endpoint executes router smoothly."""
    payload = {
        "query": "My rice crop leaves are dying with brown spots",
        "user_id": "e2e-farmer-01",
        "location": {"district": "Polonnaruwa", "agro_ecological_zone": "DL1c"},
        "crop_context": "Paddy",
        "language": "en"
    }
    response = client.post("/api/orchestrator/process", json=payload)
    assert response.status_code == 200
    data = response.json()

    meta = data["metadata"]
    assert meta["intent"] == "disease_diagnosis"
    assert "disease_agent" in meta["agents_consulted"]
    assert "weather_agent" in meta["agents_consulted"]
    assert "rag_agent" in meta["agents_consulted"]
    assert len(data["sources"]) > 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
