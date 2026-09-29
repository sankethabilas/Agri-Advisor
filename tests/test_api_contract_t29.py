"""Day 1 API contract verification (T-29)."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
from typing import get_args, get_origin
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from pydantic import BaseModel

from orchestrator import main as api
from orchestrator.schemas import (
    CropAdviceResponse,
    DiseaseDiagnoseResponse,
    ErrorEnvelope,
    HealthCheckResponse,
    OrchestratorProcessResponse,
    RagRetrieveResponse,
    WeatherAdviceResponse,
)
from orchestrator.security import JWT_ALGORITHM, JWT_SECRET, create_access_token, user_rate_limiter


FIXTURES = Path(__file__).parent / "fixtures"
client = TestClient(api.app)
TIMINGS_MS = {}


def _fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _timed_request(method, path, **kwargs):
    started = time.perf_counter()
    response = getattr(client, method)(path, **kwargs)
    TIMINGS_MS[path] = round((time.perf_counter() - started) * 1000, 2)
    return response


def _auth(user_id):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


class _OfflineLLM:
    provider = "contract-test"
    model = "disabled"

    @staticmethod
    def is_available():
        return False


@pytest.fixture(autouse=True)
def reset_contract_test_state(monkeypatch):
    api.session_manager._sessions_by_user.clear()
    api.session_manager._sessions_by_id.clear()
    user_rate_limiter._events.clear()
    monkeypatch.setattr(api.orchestrator_agent.synthesizer, "llm", _OfflineLLM())

    weather = _fixture("weather_advice_response.json")
    monkeypatch.setattr(
        api.weather_agent,
        "get_weather_advice",
        lambda _location, _crop=None: WeatherAdviceResponse.model_validate(weather),
    )
    yield
    user_rate_limiter._events.clear()


def _assert_error(response, expected_status):
    assert response.status_code == expected_status, response.text
    envelope = ErrorEnvelope.model_validate(response.json())
    error = envelope.error
    assert error.status_code == expected_status
    assert error.code == {
        400: "VALIDATION_ERROR",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        409: "ERROR",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
    }[expected_status]
    assert error.message
    assert error.timestamp
    assert error.request_id
    if expected_status in (400, 422):
        assert error.details


def _assert_required_keys(value, required, path):
    assert isinstance(value, dict), f"{path} must be an object"
    missing = set(required) - value.keys()
    assert not missing, f"{path} is missing contract fields: {sorted(missing)}"


def _nested_model(annotation):
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    for argument in get_args(annotation):
        model = _nested_model(argument)
        if model is not None:
            return model
    return None


def _assert_no_undocumented_fields(value, model, path):
    if not isinstance(value, dict):
        return
    allowed = set(model.model_fields)
    assert value.keys() <= allowed, f"{path} has undocumented fields: {sorted(value.keys() - allowed)}"
    for field_name, field in model.model_fields.items():
        if field_name not in value or value[field_name] is None:
            continue
        nested = _nested_model(field.annotation)
        if nested is None:
            continue
        field_value = value[field_name]
        origin = get_origin(field.annotation)
        if origin is list and isinstance(field_value, list):
            for index, item in enumerate(field_value):
                _assert_no_undocumented_fields(item, nested, f"{path}.{field_name}[{index}]")
        elif origin is dict and isinstance(field_value, dict):
            for key, item in field_value.items():
                _assert_no_undocumented_fields(item, nested, f"{path}.{field_name}.{key}")
        else:
            _assert_no_undocumented_fields(field_value, nested, f"{path}.{field_name}")


def test_valid_responses_match_all_six_service_contracts_and_auth_contracts():
    timings = {}

    process_request = _fixture("orchestrator_process_request.json")
    process_user = process_request["user_id"]
    response = _timed_request(
        "post", "/api/orchestrator/process", json=process_request, headers=_auth(process_user)
    )
    assert response.status_code == 200, response.text
    body = response.json()
    OrchestratorProcessResponse.model_validate(body)
    _assert_no_undocumented_fields(body, OrchestratorProcessResponse, "process")
    _assert_required_keys(body, ["answer", "sources", "weather_alert", "metadata"], "process")
    assert isinstance(body["answer"], str) and body["answer"]
    assert isinstance(body["sources"], list)
    for index, source in enumerate(body["sources"]):
        _assert_required_keys(
            source,
            ["title", "author_organization", "document_id", "section", "confidence_score"],
            f"process.sources[{index}]",
        )
    _assert_required_keys(
        body["weather_alert"],
        ["severity", "title", "message", "impact_warning", "valid_until"],
        "process.weather_alert",
    )
    _assert_required_keys(
        body["metadata"],
        ["session_id", "user_id", "intent", "confidence", "agents_consulted", "language", "latency_ms", "timestamp"],
        "process.metadata",
    )
    timings["POST /api/orchestrator/process"] = TIMINGS_MS["/api/orchestrator/process"]

    disease_response = _timed_request(
        "post", "/api/disease/diagnose", json=_fixture("disease_diagnose_request.json")
    )
    assert disease_response.status_code == 200, disease_response.text
    disease = disease_response.json()
    DiseaseDiagnoseResponse.model_validate(disease)
    _assert_no_undocumented_fields(disease, DiseaseDiagnoseResponse, "disease")
    _assert_required_keys(
        disease,
        ["disease", "confidence", "severity", "treatment", "prevention", "source", "symptoms_confirmed"],
        "disease",
    )
    _assert_required_keys(disease["treatment"], ["chemical", "organic", "cultural"], "disease.treatment")
    for kind, fields in {
        "chemical": ["name", "dosage", "instructions", "pre_harvest_interval_days"],
        "organic": ["name", "dosage", "instructions"],
        "cultural": ["practice", "description"],
    }.items():
        for index, treatment in enumerate(disease["treatment"][kind]):
            _assert_required_keys(treatment, fields, f"disease.treatment.{kind}[{index}]")
    timings["POST /api/disease/diagnose"] = TIMINGS_MS["/api/disease/diagnose"]

    weather_response = _timed_request(
        "post", "/api/weather/advice", json=_fixture("weather_advice_request.json")
    )
    assert weather_response.status_code == 200, weather_response.text
    weather = weather_response.json()
    WeatherAdviceResponse.model_validate(weather)
    _assert_no_undocumented_fields(weather, WeatherAdviceResponse, "weather")
    _assert_required_keys(weather, ["current", "forecast", "disease_risk", "pest_risk", "advisory", "alerts"], "weather")
    for index, forecast in enumerate(weather["forecast"]):
        _assert_required_keys(
            forecast,
            ["date", "temp_min_c", "temp_max_c", "rainfall_mm", "rainfall_prob_pct", "humidity_pct", "wind_speed_kmh", "condition"],
            f"weather.forecast[{index}]",
        )
    timings["POST /api/weather/advice"] = TIMINGS_MS["/api/weather/advice"]

    rag_response = _timed_request(
        "post", "/api/rag/retrieve", json=_fixture("rag_retrieve_request.json")
    )
    assert rag_response.status_code == 200, rag_response.text
    rag = rag_response.json()
    RagRetrieveResponse.model_validate(rag)
    _assert_no_undocumented_fields(rag, RagRetrieveResponse, "rag")
    _assert_required_keys(rag, ["context", "sources", "confidence"], "rag")
    assert len(rag["sources"]) == len(rag["confidence"])
    for index, source in enumerate(rag["sources"]):
        _assert_required_keys(
            source,
            ["id", "document_id", "title", "section", "content", "score", "author_organization", "publication_year"],
            f"rag.sources[{index}]",
        )
    timings["POST /api/rag/retrieve"] = TIMINGS_MS["/api/rag/retrieve"]

    crop_response = _timed_request(
        "post", "/api/crop/advice", json=_fixture("crop_advice_request.json")
    )
    assert crop_response.status_code == 200, crop_response.text
    crop = crop_response.json()
    CropAdviceResponse.model_validate(crop)
    _assert_no_undocumented_fields(crop, CropAdviceResponse, "crop")
    _assert_required_keys(
        crop,
        ["crop", "season", "agro_ecological_zone", "advisory_sections", "source", "generated_at"],
        "crop",
    )
    section_names = [
        "1_varieties", "2_land_preparation", "3_planting_schedule", "4_fertilizer_management",
        "5_water_management", "6_weed_control", "7_harvesting_and_post_harvest",
        "8_crop_rotation_and_intercropping",
    ]
    assert set(section_names) <= crop["advisory_sections"].keys()
    timings["POST /api/crop/advice"] = TIMINGS_MS["/api/crop/advice"]

    health_response = _timed_request("get", "/api/health")
    assert health_response.status_code == 200, health_response.text
    health = health_response.json()
    HealthCheckResponse.model_validate(health)
    _assert_no_undocumented_fields(health, HealthCheckResponse, "health")
    assert set(health["services"]) == {
        "orchestrator", "disease_agent", "weather_agent", "rag_agent", "crop_agent"
    }
    for service, result in health["services"].items():
        _assert_required_keys(result, ["status", "latency_ms", "message"], f"health.services.{service}")
    timings["GET /api/health"] = TIMINGS_MS["/api/health"]

    username = f"t29_{uuid4().hex[:16]}"
    password = "Contract-Test-2026!"
    register_response = _timed_request(
        "post", "/api/auth/register", json={"username": username, "password": password}
    )
    assert register_response.status_code == 201, register_response.text
    register = register_response.json()
    assert set(register) == {"user_id", "message"}
    assert register == {"user_id": username, "message": "Account created successfully."}
    timings["POST /api/auth/register"] = TIMINGS_MS["/api/auth/register"]

    login_response = _timed_request(
        "post", "/api/auth/login", json={"username": username, "password": password}
    )
    assert login_response.status_code == 200, login_response.text
    login = login_response.json()
    assert set(login) == {"access_token", "token_type", "expires_in", "user_id"}
    assert login["token_type"] == "bearer"
    assert isinstance(login["access_token"], str) and login["access_token"]
    assert isinstance(login["expires_in"], int) and login["expires_in"] > 0
    assert login["user_id"] == username
    timings["POST /api/auth/login"] = TIMINGS_MS["/api/auth/login"]

    print("\nT-29 valid endpoint response times (ms):")
    for endpoint, duration in timings.items():
        print(f"{endpoint}: {duration:.2f}")


@pytest.mark.parametrize(
    ("path", "payload", "field", "headers"),
    [
        ("/api/orchestrator/process", "orchestrator_process_request.json", "query", "process"),
        ("/api/disease/diagnose", "disease_diagnose_request.json", "crop", None),
        ("/api/weather/advice", "weather_advice_request.json", "location", None),
        ("/api/rag/retrieve", "rag_retrieve_request.json", "query", None),
        ("/api/crop/advice", "crop_advice_request.json", "season", None),
        ("/api/auth/register", None, "username", None),
        ("/api/auth/login", None, "password", None),
    ],
)
def test_missing_required_fields_return_contract_validation_error(path, payload, field, headers):
    body = _fixture(payload) if payload else {"username": "t29_invalid", "password": "Strong-Password-2026"}
    body.pop(field, None)
    request_headers = _auth(body.get("user_id", "farmer_anu_0842")) if headers == "process" else None
    response = client.post(path, json=body, headers=request_headers)
    _assert_error(response, 400)


@pytest.mark.parametrize(
    ("path", "payload", "field", "wrong_value"),
    [
        ("/api/orchestrator/process", "orchestrator_process_request.json", "query", 17),
        ("/api/disease/diagnose", "disease_diagnose_request.json", "symptoms", "yellow leaves"),
        ("/api/weather/advice", "weather_advice_request.json", "location", "Anuradhapura"),
        ("/api/rag/retrieve", "rag_retrieve_request.json", "query", ["paddy"]),
        ("/api/crop/advice", "crop_advice_request.json", "season", 2026),
        ("/api/auth/register", None, "username", 29),
        ("/api/auth/login", None, "password", ["not", "a", "string"]),
    ],
)
def test_wrong_data_types_return_contract_validation_error(path, payload, field, wrong_value):
    body = _fixture(payload) if payload else {"username": "t29_invalid", "password": "Strong-Password-2026"}
    body[field] = wrong_value
    headers = _auth(body["user_id"]) if path == "/api/orchestrator/process" else None
    _assert_error(client.post(path, json=body, headers=headers), 400)


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/api/orchestrator/process", "orchestrator_process_request.json"),
        ("/api/disease/diagnose", "disease_diagnose_request.json"),
        ("/api/weather/advice", "weather_advice_request.json"),
        ("/api/rag/retrieve", "rag_retrieve_request.json"),
        ("/api/crop/advice", "crop_advice_request.json"),
        ("/api/auth/register", None),
        ("/api/auth/login", None),
    ],
)
def test_malformed_json_returns_contract_validation_error(path, payload):
    headers = {"Content-Type": "application/json"}
    if path == "/api/orchestrator/process":
        headers.update(_auth("farmer_anu_0842"))
    response = client.post(path, content="{", headers=headers)
    _assert_error(response, 400)


def test_health_has_no_request_body_to_validate():
    response = client.request("GET", "/api/health", content="{")
    assert response.status_code == 200
    HealthCheckResponse.model_validate(response.json())


def test_semantic_constraint_uses_422_unprocessable_entity():
    request = _fixture("weather_advice_request.json")
    request["location"]["latitude"] = 11.0
    response = client.post("/api/weather/advice", json=request)
    _assert_error(response, 422)


def test_authentication_valid_missing_expired_and_tampered_tokens():
    user_id = "t29_auth_subject"
    payload = _fixture("orchestrator_process_request.json")
    payload["user_id"] = user_id

    valid = client.post("/api/orchestrator/process", json=payload, headers=_auth(user_id))
    assert valid.status_code == 200, valid.text
    OrchestratorProcessResponse.model_validate(valid.json())

    missing = client.post("/api/orchestrator/process", json=payload)
    _assert_error(missing, 401)

    expired_token = jwt.encode(
        {"sub": user_id, "iat": datetime.now(timezone.utc) - timedelta(hours=2),
         "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    expired = client.post(
        "/api/orchestrator/process", json=payload,
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    _assert_error(expired, 401)

    token = create_access_token(user_id)
    tampered_token = token[:-1] + ("A" if token[-1] != "A" else "B")
    tampered = client.post(
        "/api/orchestrator/process", json=payload,
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    _assert_error(tampered, 401)


def test_rate_limit_returns_429_and_retry_after(monkeypatch):
    user_id = "t29_rate_limit_user"
    monkeypatch.setattr(user_rate_limiter, "limit", 1)
    monkeypatch.setattr(user_rate_limiter, "window_seconds", 60)
    user_rate_limiter._events.clear()
    payload = _fixture("orchestrator_process_request.json")
    payload["user_id"] = user_id

    first = client.post("/api/orchestrator/process", json=payload, headers=_auth(user_id))
    assert first.status_code == 200, first.text
    limited = client.post("/api/orchestrator/process", json=payload, headers=_auth(user_id))
    _assert_error(limited, 429)
    assert int(limited.headers["Retry-After"]) >= 1