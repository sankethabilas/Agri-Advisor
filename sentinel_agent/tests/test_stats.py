"""Unit tests for statistical anomaly detection logic."""

import pytest
from sentinel_agent.stats import calculate_baseline_and_std, is_anomalous_cluster, classify_sentinel_risk


def test_baseline_calculation_empty_bins():
    """Handles zero activity historical periods safely using std floor."""
    mean, std = calculate_baseline_and_std([], std_floor=0.5)
    assert mean == 0.0
    assert std == 0.5


def test_baseline_calculation_uniform_data():
    """Calculates mean correctly and applies std floor if variance is 0."""
    bins = [2, 2, 2, 2, 2]
    mean, std = calculate_baseline_and_std(bins, std_floor=0.5)
    assert mean == 2.0
    assert std == 0.5


def test_is_anomalous_cluster_below_min_cases():
    """Rejects clusters below MIN_CASES (5) even if mathematically elevated."""
    # 4 cases vs 0.0 baseline (threshold = 1.0)
    anomalous, reason = is_anomalous_cluster(
        recent_count=4,
        baseline=0.0,
        std_dev=0.5,
        multiplier=1.0,
        min_cases=5,
    )
    assert not anomalous
    assert "4 cases" in reason


def test_is_anomalous_cluster_zero_baseline_above_min_cases():
    """Identifies sudden outbreak on clean baseline when count >= MIN_CASES."""
    # 6 cases vs 0.0 baseline (threshold = 1.0)
    anomalous, reason = is_anomalous_cluster(
        recent_count=6,
        baseline=0.0,
        std_dev=0.5,
        multiplier=1.0,
        min_cases=5,
    )
    assert anomalous
    assert "6 cases" in reason


def test_is_anomalous_cluster_high_baseline():
    """Normal seasonal background cases do not trigger false anomalies."""
    # 6 cases vs 8.0 baseline with std 1.5 (threshold = 11.0)
    anomalous, reason = is_anomalous_cluster(
        recent_count=6,
        baseline=8.0,
        std_dev=1.5,
        multiplier=1.0,
        min_cases=5,
    )
    assert not anomalous


def test_classify_sentinel_risk():
    """Tests none / watch / outbreak decision states."""
    # 1. Non-anomalous -> none
    level, _ = classify_sentinel_risk(
        is_anomalous=False,
        weather_disease_risk_level="High",
        recent_count=3,
        baseline=2.0,
        effective_std=0.5,
    )
    assert level == "none"

    # 2. Anomalous + Medium weather -> watch
    level, reason = classify_sentinel_risk(
        is_anomalous=True,
        weather_disease_risk_level="Medium",
        recent_count=7,
        baseline=1.2,
        effective_std=0.5,
        weather_score=0.45,
    )
    assert level == "watch"
    assert "weather risk Medium" in reason

    # 3. Anomalous + High weather -> outbreak
    level, reason = classify_sentinel_risk(
        is_anomalous=True,
        weather_disease_risk_level="High",
        recent_count=7,
        baseline=1.2,
        effective_std=0.5,
        weather_score=0.88,
    )
    assert level == "outbreak"
    assert "weather risk High" in reason
