"""Shared weather-risk scoring helpers."""

from typing import Any, Dict


def value(current: Any, name: str) -> float:
    if isinstance(current, dict):
        return float(current[name])
    return float(getattr(current, name))


def level_for_score(score: float) -> str:
    if score >= 0.95:
        return "Critical"
    if score >= 0.85:
        return "High"
    if score >= 0.60:
        return "Moderate"
    return "Low"


def risk_result(score: float, factors: list[str], recommendation: str) -> Dict[str, Any]:
    bounded_score = round(min(1.0, max(0.0, score)), 2)
    return {
        "level": level_for_score(bounded_score),
        "score": bounded_score,
        "contributing_factors": factors,
        "recommendation": recommendation,
    }