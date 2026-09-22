"""Fetch and normalize live weather data for the weather API contract."""

from datetime import datetime, timedelta, timezone
from threading import Lock
from time import monotonic
from typing import Any, Dict, List, Optional, Tuple

import requests

from orchestrator.schemas import Location, WeatherAdviceResponse


class WeatherServiceError(RuntimeError):
    """Raised when the upstream weather service cannot provide valid data."""


SRI_LANKAN_LOCATIONS: Dict[str, Tuple[float, float]] = {
    "ampara": (7.2917, 81.6724), "anuradhapura": (8.3114, 80.4037),
    "badulla": (6.9934, 81.0550), "batticaloa": (7.7310, 81.6747),
    "colombo": (6.9271, 79.8612), "galle": (6.0329, 80.2168),
    "gampaha": (7.0840, 80.0098), "hambantota": (6.1429, 81.1212),
    "jaffna": (9.6615, 80.0255), "kalutara": (6.5854, 79.9607),
    "kandy": (7.2906, 80.6337), "kegalle": (7.2513, 80.3464),
    "kilinochchi": (9.3803, 80.3770), "kurunegala": (7.4863, 80.3623),
    "mannar": (8.9810, 79.9044), "matale": (7.4675, 80.6234),
    "matara": (5.9549, 80.5550), "monaragala": (6.8728, 81.3507),
    "mullaitivu": (9.2671, 80.8128), "nuwara eliya": (6.9497, 80.7891),
    "polonnaruwa": (7.9403, 81.0188), "puttalam": (8.0408, 79.8394),
    "ratnapura": (6.6828, 80.3992), "trincomalee": (8.5874, 81.2152),
    "vavuniya": (8.7514, 80.4971),
}

WMO_CONDITIONS = {
    0: ("Clear sky", "01d"), 1: ("Mainly clear", "02d"),
    2: ("Partly cloudy", "03d"), 3: ("Overcast", "04d"),
    45: ("Fog", "50d"), 48: ("Depositing rime fog", "50d"),
    51: ("Light drizzle", "09d"), 53: ("Drizzle", "09d"),
    55: ("Heavy drizzle", "09d"), 61: ("Light rain", "10d"),
    63: ("Rain", "10d"), 65: ("Heavy rain", "10d"),
    80: ("Rain showers", "09d"), 81: ("Rain showers", "09d"),
    82: ("Heavy rain showers", "09d"), 95: ("Thunderstorm", "11d"),
    96: ("Thunderstorm with hail", "11d"), 99: ("Thunderstorm with hail", "11d"),
}


class WeatherAgent:
    """Live weather client with coordinate resolution and a short local cache."""

    API_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, cache_ttl_seconds: int = 300, timeout_seconds: int = 10) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds
        self.timeout_seconds = timeout_seconds
        self._cache: Dict[Tuple[float, float, int], Tuple[float, Dict[str, Any]]] = {}
        self._cache_lock = Lock()

    @staticmethod
    def resolve_location(location: Location) -> Tuple[float, float]:
        if location.latitude is not None and location.longitude is not None:
            return location.latitude, location.longitude
        key = " ".join(location.district.strip().lower().split())
        try:
            return SRI_LANKAN_LOCATIONS[key]
        except KeyError as exc:
            supported = ", ".join(sorted(SRI_LANKAN_LOCATIONS))
            raise WeatherServiceError(
                f"Unknown Sri Lankan district '{location.district}'. Supported locations: {supported}."
            ) from exc

    def _fetch(self, location: Location, days: int = 7) -> Dict[str, Any]:
        latitude, longitude = self.resolve_location(location)
        cache_key = (round(latitude, 4), round(longitude, 4), days)
        now = monotonic()
        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if cached and now - cached[0] < self.cache_ttl_seconds:
                return cached[1]

        params = {
            "latitude": latitude, "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum,precipitation_probability_max,relative_humidity_2m_mean,wind_speed_10m_max,weather_code",
            "forecast_days": days, "timezone": "UTC",
        }
        try:
            response = requests.get(self.API_URL, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise WeatherServiceError(f"Weather service request failed: {exc}") from exc
        if not isinstance(data, dict) or "current" not in data or "daily" not in data:
            raise WeatherServiceError("Weather service returned an incomplete response")
        with self._cache_lock:
            self._cache[cache_key] = (now, data)
        return data

    @staticmethod
    def _condition(code: int) -> Tuple[str, str]:
        return WMO_CONDITIONS.get(code, ("Unknown", "01d"))

    def get_current(self, location: Location) -> Dict[str, Any]:
        """Return normalized live conditions for a named or coordinate location."""
        current = self._fetch(location)["current"]
        condition, icon = self._condition(int(current.get("weather_code", 0)))
        observed_at = current.get("time") or datetime.now(timezone.utc).isoformat()
        return {
            "temperature_c": float(current["temperature_2m"]),
            "humidity_pct": int(round(current["relative_humidity_2m"])),
            "rainfall_mm": float(current.get("precipitation", 0.0)),
            "wind_speed_kmh": float(current["wind_speed_10m"]),
            "wind_direction": self._wind_direction(float(current.get("wind_direction_10m", 0))),
            "condition": condition, "icon": icon,
            "timestamp": self._iso_timestamp(observed_at),
        }

    def get_forecast(self, location: Location, days: int = 7) -> List[Dict[str, Any]]:
        """Return a normalized daily forecast, limited to seven days."""
        if not 1 <= days <= 7:
            raise ValueError("days must be between 1 and 7")
        daily = self._fetch(location, days=days)["daily"]
        forecast = []
        for index, date in enumerate(daily["time"][:days]):
            condition, _ = self._condition(int(daily["weather_code"][index]))
            forecast.append({
                "date": date,
                "temp_min_c": float(daily["temperature_2m_min"][index]),
                "temp_max_c": float(daily["temperature_2m_max"][index]),
                "rainfall_mm": float(daily["precipitation_sum"][index]),
                "rainfall_prob_pct": int(round(daily["precipitation_probability_max"][index] or 0)),
                "humidity_pct": int(round(daily["relative_humidity_2m_mean"][index])),
                "wind_speed_kmh": float(daily["wind_speed_10m_max"][index]),
                "condition": condition,
            })
        return forecast

    def get_weather_advice(self, location: Location, crop: Optional[str] = None) -> WeatherAdviceResponse:
        current = self.get_current(location)
        forecast = self.get_forecast(location)
        alerts = self._alerts(forecast, location.district)
        return WeatherAdviceResponse.model_validate({
            "current": current, "forecast": forecast,
            "disease_risk": self._risk(forecast, current, crop, disease=True),
            "pest_risk": self._risk(forecast, current, crop, disease=False),
            "advisory": self._advisory(forecast, alerts, crop), "alerts": alerts,
        })

    @staticmethod
    def _wind_direction(degrees: float) -> str:
        directions = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
        return directions[int((degrees % 360) / 45 + 0.5) % 8]

    @staticmethod
    def _iso_timestamp(value: str) -> str:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat()

    @staticmethod
    def _risk(forecast: List[Dict[str, Any]], current: Dict[str, Any], crop: Optional[str], disease: bool) -> Dict[str, Any]:
        wet_days = sum(day["rainfall_mm"] >= 5 or day["humidity_pct"] >= 85 for day in forecast)
        score = min(1.0, (wet_days / max(1, len(forecast))) * (0.8 if disease else 0.55) + (0.2 if current["humidity_pct"] >= 80 else 0))
        level = "Critical" if score >= 0.85 else "High" if score >= 0.65 else "Moderate" if score >= 0.35 else "Low"
        subject = crop or "crops"
        return {
            "level": level, "score": round(score, 2),
            "susceptible_diseases" if disease else "susceptible_pests": ([f"Fungal diseases in {subject}"] if disease else [f"Sap-sucking pests in {subject}"]),
            "contributing_factors": ["High humidity or rainfall is expected" if wet_days else "Mostly dry conditions are expected"],
        }

    def _alerts(self, forecast: List[Dict[str, Any]], district: str) -> List[Dict[str, Any]]:
        rain_total = sum(day["rainfall_mm"] for day in forecast[:3])
        if rain_total < 25:
            return []
        now = datetime.now(timezone.utc)
        return [{
            "id": f"ALT-WEATHER-{now:%Y%m%d}-{district.lower().replace(' ', '-')}",
            "alert_type": "heavy_rain", "severity": "warning" if rain_total >= 50 else "watch",
            "title": "Heavy rain alert",
            "description": f"Approximately {rain_total:.1f} mm of rain is forecast in {district} over the next three days.",
            "valid_from": now.isoformat(), "valid_to": (now + timedelta(days=3)).isoformat(),
            "recommended_action": "Keep drainage channels clear and postpone spraying before rainfall.",
        }]

    @staticmethod
    def _advisory(forecast: List[Dict[str, Any]], alerts: List[Dict[str, Any]], crop: Optional[str]) -> str:
        if alerts:
            return "Postpone pesticide spraying and fertilizer application before rain; inspect and clear field drainage."
        return f"Conditions are suitable for routine field work on {crop or 'the crop'}; monitor soil moisture and local showers."


weather_agent = WeatherAgent()