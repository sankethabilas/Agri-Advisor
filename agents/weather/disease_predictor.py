"""Rule-based crop disease risk prediction from current weather."""

from typing import Any, Dict, List

from agents.weather.risk_utils import risk_result, value


def predict(current: Any) -> Dict[str, Any]:
    temperature = value(current, "temperature_c")
    humidity = value(current, "humidity_pct")
    rainfall = value(current, "rainfall_mm")
    score = 0.0
    factors: List[str] = []

    warm = 20 <= temperature <= 32
    humid = humidity >= 80
    if warm:
        score += 0.25
        factors.append("Temperature is in the 20-32 C disease-favorable range")
    if humid:
        score += 0.35
        factors.append("Relative humidity is at least 80%")
    if rainfall >= 5:
        score += 0.25
        factors.append("Current rainfall is at least 5 mm")
    if warm and humid:
        score += 0.25
        factors.append("Warm and humid conditions compound disease pressure")

    level = risk_result(score, factors, "") ["level"]
    if level in {"High", "Critical"}:
        recommendation = (
            "Inspect susceptible crops within 24 hours; consider locally approved "
            "preventive fungicide only when the forecast allows a safe application window."
        )
    elif level == "Moderate":
        recommendation = "Inspect crops daily and remove infected plant material where practical."
    else:
        recommendation = "Continue routine crop monitoring and field sanitation."

    result = risk_result(score, factors, recommendation)
    result["susceptible_diseases"] = ["Fungal leaf diseases"]
    return result