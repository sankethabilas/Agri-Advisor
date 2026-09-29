import json
import logging
import threading

import pytest
import requests
from fastapi.testclient import TestClient

from orchestrator.agent import OrchestratorAgent
from orchestrator.llm_client import LLMClientError
from orchestrator.main import app, orchestrator_agent
from orchestrator.resilience import request_with_retry
from orchestrator.router import AgentRouter
from orchestrator.schemas import (
    CropAdviceRequest,
    DiseaseDiagnoseRequest,
    Location,
    OrchestratorProcessRequest,
    RagRetrieveRequest,
    WeatherAdviceRequest,
)
from orchestrator.session_context import SessionManager
from orchestrator.security import create_access_token
from orchestrator.stubs import stub_service
from orchestrator.synthesis import ADVISORY_DISCLAIMER, ResponseSynthesizer


def _request(query="My paddy leaves have yellow spots", user_id="resilience-test"):
    return OrchestratorProcessRequest(
        query=query,
        user_id=user_id,
        location=Location(district="Anuradhapura", agro_ecological_zone="DL1b"),
        crop_context="Paddy",
    )


class OfflineLLM:
    provider = "test"
    model = "disabled"

    def is_available(self):
        return False


def _partial_router(weather_agent=None):
    return AgentRouter(
        disease_agent=stub_service.get_disease_diagnosis,
        weather_agent=weather_agent or (lambda req: stub_service.get_weather_advice(req)),
        rag_agent=stub_service.get_rag_retrieve,
        crop_agent=stub_service.get_crop_advice,
    )


def test_weather_failure_keeps_diagnosis_and_explains_missing_context():
    def weather_down(_request):
        raise ConnectionError("private upstream detail")

    agent = OrchestratorAgent(
        session_mgr=SessionManager(),
        router=_partial_router(weather_down),
        synthesizer=ResponseSynthesizer(llm=OfflineLLM()),
    )
    response = agent.process(_request())

    assert response.diagnosis is not None
    assert response.weather_alert.severity == "none"
    assert response.weather_alert.title == "Weather information unavailable"
    assert response.answer
    assert "Current weather details are temporarily unavailable" in response.answer
    assert "Weather & Microclimate Risk Outlook" not in response.answer
    assert "private upstream detail" not in response.answer
    assert "Traceback" not in response.answer


def test_weather_timeout_returns_partial_result_and_structured_log(caplog):
    release = threading.Event()

    def slow_weather(_request):
        release.wait(2)
        return stub_service.get_weather_advice()

    router = _partial_router(slow_weather)
    router.agent_timeouts["weather_agent"] = 0.03
    caplog.set_level(logging.ERROR, logger="agri_advisor.router")
    try:
        result = router.dispatch(_request())
    finally:
        release.set()

    assert result.disease_response is not None
    assert result.weather_response is None
    assert result.agent_failures["weather_agent"] == "timeout"
    failure = next(record for record in caplog.records if getattr(record, "event", None) == "agent_call_failed")
    assert failure.agent == "weather_agent"
    assert failure.failure_mode == "timeout"


@pytest.mark.parametrize(
    ("agent_name", "method_name", "agent_request"),
    [
        (
            "disease_agent",
            "call_disease_agent",
            DiseaseDiagnoseRequest(
                crop="Paddy", symptoms=["yellow spots"],
                location=Location(district="Anuradhapura"),
            ),
        ),
        (
            "weather_agent",
            "call_weather_agent",
            WeatherAdviceRequest(location=Location(district="Anuradhapura")),
        ),
        (
            "crop_agent",
            "call_crop_agent",
            CropAdviceRequest(
                crop="Paddy", location=Location(district="Anuradhapura"),
                season="Maha", soil_type="RBE",
            ),
        ),
        (
            "rag_agent",
            "call_rag_agent",
            RagRetrieveRequest(query="paddy disease guidance"),
        ),
    ],
)
def test_each_agent_exception_is_isolated_and_logged(agent_name, method_name, agent_request, caplog):
    def unavailable(_request):
        raise RuntimeError("dependency disabled")

    router = AgentRouter(
        disease_agent=unavailable,
        weather_agent=unavailable,
        crop_agent=unavailable,
        rag_agent=unavailable,
    )
    caplog.set_level(logging.ERROR, logger="agri_advisor.router")

    assert getattr(router, method_name)(agent_request) is None
    failure = next(record for record in caplog.records if getattr(record, "agent", None) == agent_name)
    assert failure.event == "agent_call_failed"
    assert failure.failure_mode == "unavailable"
    assert json.loads(failure.message)["agent"] == agent_name


def test_external_api_request_retries_with_exponential_backoff(monkeypatch):
    calls = 0
    delays = []
    response = type("Response", (), {"raise_for_status": lambda self: None})()

    def operation():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise requests.ConnectionError("upstream offline")
        return response

    monkeypatch.setattr("orchestrator.resilience.time.sleep", delays.append)
    assert request_with_retry(operation, service="test_api") is response
    assert calls == 3
    assert delays == [0.2, 0.4]


def test_permanent_http_error_is_not_retried(monkeypatch):
    calls = 0
    response = requests.Response()
    response.status_code = 401
    error = requests.HTTPError(response=response)

    def operation():
        nonlocal calls
        calls += 1
        raise error

    monkeypatch.setattr("orchestrator.resilience.time.sleep", lambda _delay: None)
    with pytest.raises(requests.HTTPError):
        request_with_retry(operation, service="test_api")
    assert calls == 1


def test_failed_llm_uses_context_matched_cache_without_exposing_error():
    class FlakyLLM:
        provider = "test"
        model = "fake"

        def __init__(self):
            self.calls = 0

        def is_available(self):
            return True

        def generate(self, **_kwargs):
            self.calls += 1
            if self.calls > 1:
                raise LLMClientError("secret upstream stack detail")
            return "A prepared advisory based on the available crop and weather information."

    routing = _partial_router().dispatch(_request())
    llm = FlakyLLM()
    synthesizer = ResponseSynthesizer(llm=llm)
    first = synthesizer.synthesize(_request(), routing)
    second = synthesizer.synthesize(_request(), routing)

    assert "prepared advisory" in first
    assert "prepared advisory" in second
    assert "recent saved advisory" in second
    assert "secret upstream stack detail" not in second


def test_keyword_fallback_is_plain_language_and_never_exposes_internal_error():
    synthesizer = ResponseSynthesizer(llm=OfflineLLM())
    synthesizer.fallback_synthesizer.synthesize = lambda *_args: (_ for _ in ()).throw(
        RuntimeError("internal stack detail")
    )

    answer = synthesizer.synthesize(
        _request(query="Will it rain in Anuradhapura?"),
        _partial_router().dispatch(_request(query="Will it rain in Anuradhapura?")),
    )

    assert "cannot retrieve current weather information" in answer
    assert "internal stack detail" not in answer
    assert ADVISORY_DISCLAIMER in answer
    assert "1920" in answer


def test_orchestrator_endpoint_does_not_return_internal_exception(monkeypatch):
    user_id = "resilience-http-error"

    def fail_processing(_request):
        raise RuntimeError("private stack and database details")

    monkeypatch.setattr(orchestrator_agent, "process", fail_processing)
    response = TestClient(app).post(
        "/api/orchestrator/process",
        json={
            "query": "Yellow spots on paddy leaves",
            "user_id": user_id,
            "location": {"district": "Anuradhapura"},
            "crop_context": "Paddy",
        },
        headers={"Authorization": f"Bearer {create_access_token(user_id)}"},
    )

    assert response.status_code == 500
    assert "Please try again shortly" in response.json()["error"]["message"]
    assert "private stack and database details" not in response.text
    assert "Traceback" not in response.text