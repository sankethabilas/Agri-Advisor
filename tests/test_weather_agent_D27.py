import pytest

from agents.weather import disease_predictor
from agents.weather import pest_predictor
from agents.weather.risk_utils import (
    level_for_score,
    risk_result,
)
from agents.weather.agent import (
    check_alerts,
    generate_advisory,
)


# ============================================================
# Helper
# ============================================================

def make_forecast_day(
    rainfall_mm=0.0,
    wind_speed_kmh=10.0,
    temp_max_c=30.0,
):
    return {
        "rainfall_mm": rainfall_mm,
        "wind_speed_kmh": wind_speed_kmh,
        "temp_max_c": temp_max_c,
    }


# ============================================================
# T-27.7.1
# Risk-level threshold boundaries
# ============================================================

@pytest.mark.parametrize(
    "score, expected_level",
    [
        (0.00, "Low"),
        (0.59, "Low"),
        (0.60, "Moderate"),
        (0.84, "Moderate"),
        (0.85, "High"),
        (0.94, "High"),
        (0.95, "Critical"),
        (1.00, "Critical"),
    ],
)
def test_risk_level_thresholds(
    score,
    expected_level,
):
    assert (
        level_for_score(score)
        == expected_level
    )


# ============================================================
# T-27.7.2
# Risk score is bounded to 0–1
# ============================================================

def test_risk_result_bounds_score():

    high_result = risk_result(
        1.25,
        [],
        "test",
    )

    low_result = risk_result(
        -0.25,
        [],
        "test",
    )

    assert (
        high_result["score"]
        == 1.0
    )

    assert (
        high_result["level"]
        == "Critical"
    )

    assert (
        low_result["score"]
        == 0.0
    )

    assert (
        low_result["level"]
        == "Low"
    )


# ============================================================
# T-27.7.3
# Disease risk - Low
# ============================================================

def test_disease_risk_low():

    current = {
        "temperature_c": 15,
        "humidity_pct": 50,
        "rainfall_mm": 0,
    }

    result = (
        disease_predictor.predict(
            current
        )
    )

    assert (
        result["score"]
        == 0.0
    )

    assert (
        result["level"]
        == "Low"
    )


# ============================================================
# T-27.7.4
# Disease risk - Moderate
# ============================================================

def test_disease_risk_moderate():

    # Humidity >= 80% gives 0.35
    # Rainfall >= 5 mm gives 0.25
    # Total = 0.60
    current = {
        "temperature_c": 15,
        "humidity_pct": 80,
        "rainfall_mm": 5,
    }

    result = (
        disease_predictor.predict(
            current
        )
    )

    assert (
        result["score"]
        == 0.60
    )

    assert (
        result["level"]
        == "Moderate"
    )


# ============================================================
# T-27.7.5
# Disease risk - High
# ============================================================

def test_disease_risk_high():

    # Warm = 0.25
    # Humid = 0.35
    # Warm + humid bonus = 0.25
    # Total = 0.85
    current = {
        "temperature_c": 25,
        "humidity_pct": 80,
        "rainfall_mm": 0,
    }

    result = (
        disease_predictor.predict(
            current
        )
    )

    assert (
        result["score"]
        == 0.85
    )

    assert (
        result["level"]
        == "High"
    )


# ============================================================
# T-27.7.6
# Disease risk - Critical and bounded
# ============================================================

def test_disease_risk_critical():

    # Raw score:
    # warm     = 0.25
    # humid    = 0.35
    # rain     = 0.25
    # compound = 0.25
    # raw total = 1.10
    # risk_result must bound this to 1.00.
    current = {
        "temperature_c": 25,
        "humidity_pct": 90,
        "rainfall_mm": 10,
    }

    result = (
        disease_predictor.predict(
            current
        )
    )

    assert (
        result["score"]
        == 1.0
    )

    assert (
        result["level"]
        == "Critical"
    )


# ============================================================
# T-27.7.7
# Pest risk - Low
# ============================================================

def test_pest_risk_low():

    current = {
        "temperature_c": 15,
        "humidity_pct": 90,
        "rainfall_mm": 10,
    }

    result = (
        pest_predictor.predict(
            current
        )
    )

    assert (
        result["score"]
        == 0.0
    )

    assert (
        result["level"]
        == "Low"
    )


# ============================================================
# T-27.7.8
# Pest risk - Moderate
# ============================================================

def test_pest_risk_moderate():

    # Warm = 0.35
    # Suitable humidity = 0.25
    # Rain is >= 5, so dry condition is false
    # Total = 0.60
    current = {
        "temperature_c": 30,
        "humidity_pct": 70,
        "rainfall_mm": 5,
    }

    result = (
        pest_predictor.predict(
            current
        )
    )

    assert (
        result["score"]
        == 0.60
    )

    assert (
        result["level"]
        == "Moderate"
    )


# ============================================================
# T-27.7.9
# Pest risk - High
# ============================================================

def test_pest_risk_high():

    # Warm = 0.35
    # Suitable humidity = 0.25
    # Dry = 0.25
    # Total = 0.85
    current = {
        "temperature_c": 30,
        "humidity_pct": 70,
        "rainfall_mm": 0,
    }

    result = (
        pest_predictor.predict(
            current
        )
    )

    assert (
        result["score"]
        == 0.85
    )

    assert (
        result["level"]
        == "High"
    )


# ============================================================
# T-27.7.10
# No heavy-rain alert below 25 mm
# ============================================================

def test_no_heavy_rain_alert_below_threshold():

    forecast = [
        make_forecast_day(
            rainfall_mm=8,
        ),
        make_forecast_day(
            rainfall_mm=8,
        ),
        make_forecast_day(
            rainfall_mm=8.9,
        ),
    ]

    alerts = check_alerts(
        forecast
    )

    alert_types = {
        alert["alert_type"]
        for alert in alerts
    }

    assert (
        "heavy_rain"
        not in alert_types
    )


# ============================================================
# T-27.7.11
# Heavy-rain watch at 25 mm
# ============================================================

def test_heavy_rain_watch_at_25mm():

    forecast = [
        make_forecast_day(
            rainfall_mm=10,
        ),
        make_forecast_day(
            rainfall_mm=10,
        ),
        make_forecast_day(
            rainfall_mm=5,
        ),
    ]

    alerts = check_alerts(
        forecast
    )

    heavy_rain = next(
        alert
        for alert in alerts
        if alert["alert_type"]
        == "heavy_rain"
    )

    assert (
        heavy_rain["severity"]
        == "watch"
    )


# ============================================================
# T-27.7.12
# Heavy-rain warning at 50 mm total
# ============================================================

def test_heavy_rain_warning_at_50mm():

    forecast = [
        make_forecast_day(
            rainfall_mm=20,
        ),
        make_forecast_day(
            rainfall_mm=20,
        ),
        make_forecast_day(
            rainfall_mm=10,
        ),
    ]

    alerts = check_alerts(
        forecast
    )

    heavy_rain = next(
        alert
        for alert in alerts
        if alert["alert_type"]
        == "heavy_rain"
    )

    assert (
        heavy_rain["severity"]
        == "warning"
    )


# ============================================================
# T-27.7.13
# Flood emergency at 50 mm in one day
# ============================================================

def test_flood_alert_at_50mm_single_day():

    forecast = [
        make_forecast_day(
            rainfall_mm=50,
        ),
        make_forecast_day(),
        make_forecast_day(),
    ]

    alerts = check_alerts(
        forecast
    )

    flood = next(
        alert
        for alert in alerts
        if alert["alert_type"]
        == "flood"
    )

    assert (
        flood["severity"]
        == "emergency"
    )


# ============================================================
# T-27.7.14
# High-wind threshold
# ============================================================

def test_high_wind_alert_at_40_kmh():

    forecast = [
        make_forecast_day(
            wind_speed_kmh=40,
        ),
        make_forecast_day(),
        make_forecast_day(),
    ]

    alerts = check_alerts(
        forecast
    )

    alert_types = {
        alert["alert_type"]
        for alert in alerts
    }

    assert (
        "high_wind"
        in alert_types
    )


# ============================================================
# T-27.7.15
# Extreme-heat threshold
# ============================================================

def test_extreme_heat_alert_at_38c():

    forecast = [
        make_forecast_day(
            temp_max_c=38,
        ),
        make_forecast_day(),
        make_forecast_day(),
    ]

    alerts = check_alerts(
        forecast
    )

    alert_types = {
        alert["alert_type"]
        for alert in alerts
    }

    assert (
        "extreme_heat"
        in alert_types
    )


# ============================================================
# T-27.7.16
# BR-12 heavy-rain pesticide safety rule
# ============================================================

def test_heavy_rain_advisory_postpones_pesticide_use():

    current = {
        "temperature_c": 28.0,
        "humidity_pct": 90,
    }

    forecast = [
        make_forecast_day(
            rainfall_mm=25,
        ),
    ]

    disease_risk = {
        "level": "High",
        "score": 0.85,
        "contributing_factors": [],
        "recommendation":
            "Consider treatment.",
    }

    pest_risk = {
        "level": "Low",
        "score": 0.2,
        "contributing_factors": [],
        "recommendation":
            "Continue scouting.",
    }

    alerts = [
        {
            "alert_type":
                "heavy_rain"
        }
    ]

    advisory = generate_advisory(
        current=current,
        forecast=forecast,
        disease_risk=disease_risk,
        pest_risk=pest_risk,
        alerts=alerts,
        crop="rice",
    )

    advisory_lower = (
        advisory.lower()
    )

    assert (
        "postpone pesticide"
        in advisory_lower
    )

    assert (
        "defer pesticide"
        in disease_risk[
            "recommendation"
        ].lower()
    )