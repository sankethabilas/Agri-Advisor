"""Rule-based crop pest risk prediction from current weather."""

from typing import Any, Dict, List

from agents.weather.risk_utils import risk_result, value


def predict(current: Any) -> Dict[str, Any]:
    temperature = value(current, "temperature_c")
    humidity = value(current, "humidity_pct")
    rainfall = value(current, "rainfall_mm")
    score = 0.0
    factors: List[str] = []

    warm = 25 <= temperature <= 35
    suitable_humidity = 60 <= humidity <= 85
    dry = rainfall < 5
    if warm:
        score += 0.35
        factors.append("Temperature is in the 25-35 C pest-favorable range")
    if suitable_humidity:
        score += 0.25
        factors.append("Relative humidity is between 60% and 85%")
    if dry:
        score += 0.25
        factors.append("Current rainfall is below 5 mm")

    level = risk_result(score, factors, "")["level"]
    if level in {"High", "Critical"}:
        recommendation = (
            "Inspect crops within 24 hours, monitor pest populations, and use "
            "cultural or physical controls; follow local action thresholds."
        )
    elif level == "Moderate":
        recommendation = "Scout fields regularly and record pest counts before taking control action."
    else:
        recommendation = "Continue routine pest scouting."

    result = risk_result(score, factors, recommendation)
    result["susceptible_pests"] = ["Sap-sucking pests"]
    return result