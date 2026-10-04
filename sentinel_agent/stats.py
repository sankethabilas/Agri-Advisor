"""Statistical anomaly detection for agricultural disease cluster monitoring.

All calculations here are pure, deterministic Python functions.
The LLM does NOT participate in statistical anomaly or threshold decisions.
"""

import math
from typing import Dict, List, Tuple


def calculate_baseline_and_std(
    past_counts_48h_bins: List[int],
    std_floor: float = 0.5,
) -> Tuple[float, float]:
    """Computes the mean baseline and standard deviation across past 48h time bins.

    Args:
        past_counts_48h_bins: List of counts in prior 48h windows (typically 14 bins for 28 days).
        std_floor: Minimum floor for standard deviation to safely handle low/zero activity.

    Returns:
        Tuple of (baseline_mean, std_dev)
    """
    if not past_counts_48h_bins:
        return 0.0, std_floor

    n = len(past_counts_48h_bins)
    mean = sum(past_counts_48h_bins) / n

    if n <= 1:
        return mean, std_floor

    variance = sum((x - mean) ** 2 for x in past_counts_48h_bins) / (n - 1)
    std_dev = math.sqrt(variance)
    return mean, max(std_dev, std_floor)


def is_anomalous_cluster(
    recent_count: int,
    baseline: float,
    std_dev: float,
    multiplier: float = 1.0,
    min_cases: int = 5,
    std_floor: float = 0.5,
) -> Tuple[bool, str]:
    """Evaluates whether a recent 48h case count is statistically anomalous.

    Condition:
      count >= min_cases AND count > (baseline + 2 * effective_std) * multiplier

    Returns:
        Tuple of (is_anomalous, reasoning_summary)
    """
    effective_std = max(std_dev, std_floor)
    threshold = (baseline + (2.0 * effective_std)) * multiplier

    is_anomalous = (recent_count >= min_cases) and (recent_count > threshold)

    reason = (
        f"{recent_count} cases vs baseline {baseline:.1f} "
        f"(threshold {threshold:.2f} with std {effective_std:.2f}, multiplier {multiplier:.2f})"
    )
    return is_anomalous, reason


def classify_sentinel_risk(
    is_anomalous: bool,
    weather_disease_risk_level: str,
    recent_count: int,
    baseline: float,
    effective_std: float,
    weather_score: float = 0.0,
) -> Tuple[str, str]:
    """Determines decision level: 'none', 'watch', or 'outbreak'.

    Rules:
      - not anomalous -> 'none'
      - anomalous AND weather disease_risk level != 'High' -> 'watch'
      - anomalous AND weather disease_risk level == 'High' -> 'outbreak'

    Returns:
        Tuple of (level, reason_string)
    """
    if not is_anomalous:
        return (
            "none",
            f"{recent_count} cases is within normal baseline limits ({baseline:.1f}).",
        )

    risk_clean = (weather_disease_risk_level or "Unknown").strip().title()

    if risk_clean == "High":
        level = "outbreak"
        reason = (
            f"{recent_count} cases vs baseline {baseline:.1f} (+2 sd), "
            f"weather risk High ({weather_score:.2f})."
        )
    else:
        level = "watch"
        reason = (
            f"{recent_count} cases vs baseline {baseline:.1f} (+2 sd), "
            f"weather risk {risk_clean} ({weather_score:.2f})."
        )

    return level, reason
