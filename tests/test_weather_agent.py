from datetime import date, timedelta

import pytest
from starlette.testclient import TestClient

from agents.weather.agent import WeatherAgent, WeatherServiceError
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