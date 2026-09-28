"""
Tests for Agri-Advisor LLM Client & Response Synthesis (Task T-18).
Validates T-18.1 through T-18.8:
- T-18.1: LLM client for Groq and OpenAI providers
- T-18.2: Synthesis prompt construction with role, agent outputs, and RAG context
- T-18.3: Eight-block advisory layout order (Header, Diagnosis, Treatment, Prevention, Weather, Sources, Disclaimer, Follow-up/Helpline)
- T-18.4: Anti-hallucination grounding (Rule BR-9)
- T-18.5: Mandatory disclaimer (Rule BR-1, BR-2) & helpline attachment
- T-18.6: Prompt token cost optimization
- T-18.7: Rule-based fallback response on LLM failure (Rule FR-47)
- T-18.8: Full synthesis across all intent types (disease, weather, crop, mixed)
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from starlette.testclient import TestClient

from orchestrator.llm_client import LLMClient, LLMClientError
from orchestrator.main import app
from orchestrator.router import AgentRouter
from orchestrator.schemas import Location, OrchestratorProcessRequest
from orchestrator.session_context import session_manager
from orchestrator.synthesis import (
    ADVISORY_DISCLAIMER,
    AGRICULTURE_HELPLINE,
    PromptBuilder,
    ResponseSynthesizer,
    RuleBasedFallbackSynthesizer,
)

client = TestClient(app)
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(autouse=True)
def clean_sessions():
    session_manager._sessions_by_user.clear()
    session_manager._sessions_by_id.clear()
    yield


# ==============================================================================
# T-18.1: LLM Client Unit Tests (Groq & OpenAI)
# ==============================================================================

def test_t18_1_llm_client_initialization_and_availability():
    """Verify LLM client handles Groq and OpenAI configurations properly."""
    # Groq provider with dummy key
    groq_client = LLMClient(provider="groq", api_key="gsk_dummy123", model="llama-3.1-8b-instant")
    assert groq_client.provider == "groq"
    assert groq_client.is_available() is True

    # OpenAI provider with dummy key
    openai_client = LLMClient(provider="openai", api_key="sk-dummy123", model="gpt-3.5-turbo")
    assert openai_client.provider == "openai"
    assert openai_client.is_available() is True

    # Unconfigured client
    empty_client = LLMClient(provider="groq", api_key="")
    assert empty_client.is_available() is False
    with pytest.raises(LLMClientError, match="No API key configured"):
        empty_client.generate("Test prompt")


def test_t18_1_llm_client_mock_generation():
    """Verify generation with mock HTTP responses for both Groq and OpenAI."""
    # 1. Groq mock
    mock_groq_resp = MagicMock()
    mock_groq_resp.status_code = 200
    mock_groq_resp.json.return_value = {
        "choices": [{"message": {"content": "Groq synthetic advisory for Paddy"}}]
    }

    with patch("requests.post", return_value=mock_groq_resp):
        client_groq = LLMClient(provider="groq", api_key="gsk_test")
        # Ensure SDK client is disabled for REST test
        client_groq._groq_sdk_client = None
        ans = client_groq.generate("Query prompt")
        assert "Groq synthetic advisory" in ans

    # 2. OpenAI mock
    mock_openai_resp = MagicMock()
    mock_openai_resp.status_code = 200
    mock_openai_resp.json.return_value = {
        "choices": [{"message": {"content": "OpenAI synthetic advisory for Tomato"}}]
    }

    with patch("requests.post", return_value=mock_openai_resp):
        client_openai = LLMClient(provider="openai", api_key="sk-test", model="gpt-3.5-turbo")
        ans_oai = client_openai.generate("Query prompt")
        assert "OpenAI synthetic advisory" in ans_oai


# ==============================================================================
# T-18.2, T-18.3, T-18.4, T-18.6: Prompt Builder & Grounding Directives
# ==============================================================================

def test_t18_2_to_t18_6_prompt_builder():
    """Verify prompt builder formats agent data, enforces grounding (BR-9) and eight-block order."""
    router = AgentRouter()
    req = OrchestratorProcessRequest(
        query="My rice has yellow spots and blast lesions",
        user_id="farmer-prompt-01",
        location=Location(district="Anuradhapura", agro_ecological_zone="DL1b"),
        crop_context="Paddy",
    )
    routing_res = router.dispatch(req)

    user_prompt = PromptBuilder.build_user_prompt(req, routing_res)

    # Check that system prompt contains grounding directive (Rule BR-9)
    assert "STRICT GROUNDING" in PromptBuilder.SYSTEM_PROMPT
    assert "Rule BR-9" in PromptBuilder.SYSTEM_PROMPT

    # Check user prompt contents
    assert "farmer_query" in user_prompt
    assert "Paddy" in user_prompt
    assert "Anuradhapura" in user_prompt
    assert "EIGHT-BLOCK LAYOUT" in user_prompt
    assert ADVISORY_DISCLAIMER in user_prompt


# ==============================================================================
# T-18.7: Rule-Based Fallback Synthesis Engine (Rule FR-47)
# ==============================================================================

def test_t18_7_rule_based_fallback_eight_block_order():
    """
    T-18.7 & Completion Criteria:
    Disabling the API key produces a usable rule-based response containing all eight blocks.
    """
    # Create synthesizer with no API key (simulating offline / disabled LLM)
    offline_llm = LLMClient(provider="groq", api_key="")
    synth = ResponseSynthesizer(llm=offline_llm)

    router = AgentRouter()
    req = OrchestratorProcessRequest(
        query="My rice has yellow spots on the leaves",
        user_id="farmer-rice-01",
        location=Location(district="Anuradhapura", agro_ecological_zone="DL1b"),
        crop_context="Paddy",
    )
    routing_res = router.dispatch(req)

    advisory = synth.synthesize(req, routing_res)

    # Verify All Eight Blocks are Present in the Rule-Based Fallback
    # Block 1: Header
    assert "Advisory for Paddy (Anuradhapura)" in advisory or "Agricultural Advisory for Paddy" in advisory
    # Block 2: Diagnosis
    assert "Disease Diagnosis" in advisory
    assert "Confidence:" in advisory
    assert "Severity Level:" in advisory
    # Block 3: Immediate Treatment
    assert "Immediate Treatment Plan" in advisory
    assert "Chemical Control" in advisory
    assert "Pre-Harvest Interval (PHI)" in advisory
    assert "Organic" in advisory
    assert "Cultural" in advisory
    # Block 4: Prevention
    assert "Prevention" in advisory
    # Block 5: Weather Advisory
    assert "Weather & Microclimate Risk Outlook" in advisory
    # Block 6: Sources
    assert "Verified Knowledge Sources" in advisory
    # Block 7: Disclaimer (Rule BR-1, BR-2)
    assert ADVISORY_DISCLAIMER in advisory
    # Block 8: Follow-up & Helpline
    assert "Extension Helpline:" in advisory
    assert "1920" in advisory


def test_t18_7_fallback_triggered_on_llm_exception():
    """Verify that when LLM call throws an exception, fallback seamlessly kicks in without crashing."""
    failing_llm = LLMClient(provider="groq", api_key="gsk_will_fail")
    # Mock LLMClient.generate to raise LLMClientError
    failing_llm.generate = MagicMock(side_effect=LLMClientError("503 Service Unavailable / Rate Limit"))

    synth = ResponseSynthesizer(llm=failing_llm)
    router = AgentRouter()
    req = OrchestratorProcessRequest(
        query="Yellow spots on tomato leaves",
        user_id="farmer-tomato-01",
        location=Location(district="Badulla", agro_ecological_zone="IU3c"),
        crop_context="Tomato",
    )
    routing_res = router.dispatch(req)

    # Should not raise exception; must return valid fallback advisory
    advisory = synth.synthesize(req, routing_res)
    assert advisory is not None
    assert len(advisory) > 100
    assert "Agricultural Advisory for Tomato" in advisory
    assert ADVISORY_DISCLAIMER in advisory


# ==============================================================================
# T-18.8: Synthesis Across All Four Intent Types
# ==============================================================================

def test_t18_8_synthesis_disease_diagnosis_documented_scenario():
    """
    T-18.8 Completion Criteria:
    The documented rice scenario ("My rice has yellow spots on the leaves")
    produces a full advisory containing all eight blocks.
    """
    router = AgentRouter()
    req = OrchestratorProcessRequest(
        query="My rice has yellow spots on the leaves",
        user_id="farmer-documented-rice",
        location=Location(district="Anuradhapura", agro_ecological_zone="DL1b"),
        crop_context="Paddy",
    )
    routing_res = router.dispatch(req)
    assert routing_res.intent == "disease_diagnosis"

    # Test Rule-based generation
    fallback_text = RuleBasedFallbackSynthesizer.synthesize(req, routing_res)

    assert "# 🌾 Agricultural Advisory for Paddy (Anuradhapura)" in fallback_text
    assert "🔬 Disease Diagnosis" in fallback_text
    assert "💊 Recommended Immediate Treatment Plan" in fallback_text
    assert "🛡️ Proactive Prevention" in fallback_text
    assert "⛅ Weather & Microclimate Risk Outlook" in fallback_text
    assert "📚 Verified Knowledge Sources" in fallback_text
    assert "⚠️ Advisory Disclaimer" in fallback_text
    assert ADVISORY_DISCLAIMER in fallback_text
    assert "1920" in fallback_text


def test_t18_8_synthesis_weather_query():
    """Verify synthesis on weather_query intent."""
    router = AgentRouter()
    req = OrchestratorProcessRequest(
        query="Will it rain tomorrow in Kurunegala?",
        user_id="farmer-weather-01",
        location=Location(district="Kurunegala", agro_ecological_zone="IL1a"),
    )
    routing_res = router.dispatch(req)
    assert routing_res.intent in ["weather_query", "weather_inquiry"]

    fallback_text = RuleBasedFallbackSynthesizer.synthesize(req, routing_res)
    assert "Kurunegala" in fallback_text
    assert "Weather & Microclimate Risk Outlook" in fallback_text
    assert ADVISORY_DISCLAIMER in fallback_text
    assert "1920" in fallback_text


def test_t18_8_synthesis_crop_advice_query():
    """Verify synthesis on crop_advice intent."""
    router = AgentRouter()
    req = OrchestratorProcessRequest(
        query="Fertilizer recommendations and planting guide for Maize in Maha season",
        user_id="farmer-crop-01",
        location=Location(district="Monaragala", agro_ecological_zone="DL1b"),
        crop_context="Maize",
    )
    routing_res = router.dispatch(req)
    assert routing_res.intent in ["crop_advice", "crop_cultivation"]

    fallback_text = RuleBasedFallbackSynthesizer.synthesize(req, routing_res)
    assert "Cultivation & Fertilizer Guidelines" in fallback_text
    assert "Maize" in fallback_text
    assert ADVISORY_DISCLAIMER in fallback_text


def test_t18_8_synthesis_mixed_query():
    """Verify synthesis on mixed_query intent."""
    router = AgentRouter()
    req = OrchestratorProcessRequest(
        query="Will the heavy rain worsen the fungal blast in my paddy fields?",
        user_id="farmer-mixed-01",
        location=Location(district="Polonnaruwa", agro_ecological_zone="DL1c"),
        crop_context="Paddy",
    )
    routing_res = router.dispatch(req)
    assert routing_res.intent in ["mixed_query", "mixed"]

    fallback_text = RuleBasedFallbackSynthesizer.synthesize(req, routing_res)
    assert "Disease Diagnosis" in fallback_text
    assert "Weather & Microclimate Risk Outlook" in fallback_text
    assert ADVISORY_DISCLAIMER in fallback_text


# ==============================================================================
# End-to-End Orchestrator Process Endpoint Integration Test
# ==============================================================================

def test_end_to_end_process_endpoint_synthesis():
    """Verify full HTTP POST /api/orchestrator/process generates synthesized response with disclaimer."""
    payload = {
        "query": "My paddy leaves have yellow spots and drying tips",
        "user_id": "e2e-synth-farmer",
        "location": {"district": "Anuradhapura", "agro_ecological_zone": "DL1b"},
        "crop_context": "Paddy",
        "language": "en"
    }
    response = client.post("/api/orchestrator/process", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify synthesized answer contains 8-block elements
    answer = data["answer"]
    assert len(answer) > 100
    assert ADVISORY_DISCLAIMER in answer
    assert "1920" in answer

    # Verify sources and weather alerts
    assert len(data["sources"]) > 0
    assert "weather_alert" in data
    assert data["metadata"]["intent"] == "disease_diagnosis"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
