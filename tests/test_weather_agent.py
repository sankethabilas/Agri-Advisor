from datetime import date, timedelta

import pytest
from starlette.testclient import TestClient

from agents.weather.agent import (
    WeatherAgent,
    WeatherServiceError,
    check_alerts,
    generate_advisory,
)
from agents.weather.disease_predictor import predict as predict_disease
from agents.weather.pest_predictor import predict as predict_pests
from agents.weather.risk_utils import level_for_score
from orchestrator.main import app
from orchestrator.schemas import Location


def weather_payload() -> dict:
    start = date.today()
    return {
        "current": {
            "temperature_2m": 29.4,
            "relative_humidity_2m": 82,
            "precipitation": 1.2,
            "weather_code": 63,
            "wind_speed_10m": 14.5,
            "wind_direction_10m": 225,
            "time": "2026-09-23T10:00",
        },
        "daily": {
            "time": [(start + timedelta(days=index)).isoformat() for index in range(7)],
            "temperature_2m_min": [24.0] * 7,
            "temperature_2m_max": [31.0] * 7,
            "precipitation_sum": [4.0, 12.0, 3.0, 0.0, 5.0, 2.0, 1.0],
            "precipitation_probability_max": [40, 70, 30, 10, 50, 20, 15],
            "relative_humidity_2m_mean": [82] * 7,
            "wind_speed_10m_max": [18.0] * 7,
            "weather_code": [63, 80, 2, 0, 61, 1, 2],
        },
    }


@pytest.mark.parametrize("district", ["Anuradhapura", "Kandy", "Matara", "Colombo", "Jaffna"])
def test_five_sri_lankan_districts_resolve_to_contract_weather(monkeypatch, district):
    agent = WeatherAgent()
    calls = 0

    def fake_get(*args, **kwargs):
        nonlocal calls
        calls += 1
        return weather_payload()

    monkeypatch.setattr(agent, "_fetch", lambda location, days=7: fake_get())
    result = agent.get_weather_advice(Location(district=district), crop="Paddy")

    assert result.current.temperature_c == 29.4
    assert result.current.humidity_pct == 82
    assert result.current.rainfall_mm == 1.2
    assert result.current.condition == "Rain"
    assert len(result.forecast) == 7
    assert 0 <= result.disease_risk.score <= 1
    assert calls == 2


def test_weather_agent_cache_reuses_upstream_response(monkeypatch):
    agent = WeatherAgent()
    calls = 0

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return weather_payload()

    def fake_request(*args, **kwargs):
        nonlocal calls
        calls += 1
        return FakeResponse()

    monkeypatch.setattr("agents.weather.agent.requests.get", fake_request)
    location = Location(district="Kandy")
    agent.get_current(location)
    agent.get_forecast(location)
    assert calls == 1


def test_unknown_district_has_actionable_error():
    with pytest.raises(WeatherServiceError, match="Unknown Sri Lankan district"):
        WeatherAgent().resolve_location(Location(district="Atlantis"))


def test_weather_endpoint_returns_normalized_live_shape(monkeypatch):
    agent = WeatherAgent()
    monkeypatch.setattr(agent, "_fetch", lambda location, days=7: weather_payload())
    monkeypatch.setattr("orchestrator.main.weather_agent", agent)

    response = TestClient(app).post(
        "/api/weather/advice",
        json={"location": {"district": "Matara"}, "crop": "Paddy"},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"current", "forecast", "disease_risk", "pest_risk", "advisory", "alerts"}
    assert len(body["forecast"]) == 7
    assert body["current"]["wind_speed_kmh"] == 14.5
    assert body["disease_risk"]["recommendation"]
    assert body["pest_risk"]["recommendation"]


def test_warm_humid_weather_produces_high_disease_risk_and_24_hour_action():
    result = predict_disease({"temperature_c": 29, "humidity_pct": 85, "rainfall_mm": 0})
    assert result["score"] == 0.85
    assert result["level"] == "High"
    assert "24 hours" in result["recommendation"]


def test_pest_predictor_uses_temperature_humidity_and_rainfall():
    result = predict_pests({"temperature_c": 28, "humidity_pct": 70, "rainfall_mm": 0})
    assert result["score"] == 0.85
    assert result["level"] == "High"
    assert "cultural or physical controls" in result["recommendation"]


def test_documented_score_examples_map_to_high_and_moderate():
    assert level_for_score(0.85) == "High"
    assert level_for_score(0.60) == "Moderate"


def test_heavy_rain_alert_suppresses_fungicide_recommendation():
    current = {"temperature_c": 29, "humidity_pct": 85, "rainfall_mm": 0}
    forecast = [
        {"rainfall_mm": 30, "wind_speed_kmh": 15, "temp_max_c": 30},
        {"rainfall_mm": 0, "wind_speed_kmh": 15, "temp_max_c": 30},
        {"rainfall_mm": 0, "wind_speed_kmh": 15, "temp_max_c": 30},
    ]
    alerts = check_alerts(forecast)
    disease_risk = predict_disease(current)
    pest_risk = predict_pests(current)

    advisory = generate_advisory(current, forecast, disease_risk, pest_risk, alerts, "Paddy")

    assert any(alert["alert_type"] == "heavy_rain" for alert in alerts)
    assert "preventive fungicide" not in disease_risk["recommendation"]
    assert "defer pesticide applications" in disease_risk["recommendation"].lower()
    assert "postpone pesticide applications" in advisory


def test_alerts_cover_flood_high_wind_and_extreme_heat():
    forecast = [
        {"rainfall_mm": 55, "wind_speed_kmh": 42, "temp_max_c": 39},
        {"rainfall_mm": 0, "wind_speed_kmh": 15, "temp_max_c": 30},
        {"rainfall_mm": 0, "wind_speed_kmh": 15, "temp_max_c": 30},
    ]
    assert {alert["alert_type"] for alert in check_alerts(forecast)} == {
        "heavy_rain", "flood", "high_wind", "extreme_heat",
    }