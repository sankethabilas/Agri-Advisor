"""
Test suite to validate all JSON fixtures in tests/fixtures against the frozen API contract (T-02).
"""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> dict:
    filepath = FIXTURES_DIR / filename
    assert filepath.exists(), f"Fixture file not found: {filename}"
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def test_all_fixtures_are_valid_json():
    """Ensure all JSON files in the fixtures directory can be parsed without syntax errors."""
    fixture_files = list(FIXTURES_DIR.glob("*.json"))
    assert len(fixture_files) >= 14, f"Expected at least 14 fixture files, found {len(fixture_files)}"
    for file in fixture_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data is not None, f"Fixture {file.name} is empty"


def test_orchestrator_process_contract_t02_1_and_t02_6():
    """Validate T-02.1 Request {query, user_id, location} and T-02.6 Response {answer, sources, weather_alert}."""
    req = load_fixture("orchestrator_process_request.json")
    assert "query" in req and isinstance(req["query"], str) and len(req["query"]) > 0
    assert "user_id" in req and isinstance(req["user_id"], str)
    assert "location" in req and isinstance(req["location"], dict)
    assert "district" in req["location"]

    res = load_fixture("orchestrator_process_response.json")
    assert "answer" in res and isinstance(res["answer"], str) and len(res["answer"]) > 0
    assert "sources" in res and isinstance(res["sources"], list) and len(res["sources"]) > 0
    assert "weather_alert" in res and isinstance(res["weather_alert"], dict)
    assert "metadata" in res and isinstance(res["metadata"], dict)
    assert "intent" in res["metadata"]
    assert "agents_consulted" in res["metadata"]


def test_disease_diagnose_contract_t02_2():
    """Validate T-02.2 Disease Diagnosis contract fields."""
    req = load_fixture("disease_diagnose_request.json")
    assert "crop" in req and isinstance(req["crop"], str)
    assert "symptoms" in req and isinstance(req["symptoms"], list) and len(req["symptoms"]) > 0
    assert "location" in req and isinstance(req["location"], dict)

    res = load_fixture("disease_diagnose_response.json")
    assert "disease" in res and isinstance(res["disease"], str)
    assert "confidence" in res and 0.0 <= res["confidence"] <= 1.0
    assert "severity" in res and res["severity"] in ["Low", "Moderate", "High", "Critical"]
    assert "treatment" in res and isinstance(res["treatment"], dict)
    assert "chemical" in res["treatment"] and isinstance(res["treatment"]["chemical"], list)
    assert "organic" in res["treatment"] and isinstance(res["treatment"]["organic"], list)
    assert "cultural" in res["treatment"] and isinstance(res["treatment"]["cultural"], list)
    assert "prevention" in res and isinstance(res["prevention"], list) and len(res["prevention"]) > 0
    assert "source" in res and isinstance(res["source"], str) and len(res["source"]) > 0
    assert "symptoms_confirmed" in res and isinstance(res["symptoms_confirmed"], list) and len(res["symptoms_confirmed"]) > 0


def test_weather_advice_contract_t02_3():
    """Validate T-02.3 Weather Advice contract fields."""
    req = load_fixture("weather_advice_request.json")
    assert "location" in req and isinstance(req["location"], dict)
    assert "district" in req["location"]

    res = load_fixture("weather_advice_response.json")
    assert "current" in res and isinstance(res["current"], dict)
    assert "temperature_c" in res["current"]
    assert "humidity_pct" in res["current"]
    assert "rainfall_mm" in res["current"]
    assert "forecast" in res and isinstance(res["forecast"], list) and len(res["forecast"]) >= 5
    assert "disease_risk" in res and isinstance(res["disease_risk"], dict)
    assert "level" in res["disease_risk"] and "score" in res["disease_risk"]
    assert "pest_risk" in res and isinstance(res["pest_risk"], dict)
    assert "level" in res["pest_risk"] and "score" in res["pest_risk"]
    assert "advisory" in res and isinstance(res["advisory"], str) and len(res["advisory"]) > 0
    assert "alerts" in res and isinstance(res["alerts"], list)


def test_rag_retrieve_contract_t02_4():
    """Validate T-02.4 RAG Retrieval contract fields."""
    req = load_fixture("rag_retrieve_request.json")
    assert "query" in req and isinstance(req["query"], str)
    assert "top_k" in req and isinstance(req["top_k"], int) and req["top_k"] > 0

    res = load_fixture("rag_retrieve_response.json")
    assert "context" in res and isinstance(res["context"], str) and len(res["context"]) > 0
    assert "sources" in res and isinstance(res["sources"], list) and len(res["sources"]) > 0
    assert "confidence" in res and isinstance(res["confidence"], list) and len(res["confidence"]) > 0
    assert len(res["sources"]) == len(res["confidence"])


def test_crop_advice_contract_t02_5():
    """Validate T-02.5 Crop Advice contract with all 8 documented advisory sections."""
    req = load_fixture("crop_advice_request.json")
    assert "crop" in req and isinstance(req["crop"], str)
    assert "location" in req and isinstance(req["location"], dict)
    assert "season" in req and req["season"] in ["Maha", "Yala"]

    res = load_fixture("crop_advice_response.json")
    assert "crop" in res
    assert "season" in res
    assert "advisory_sections" in res and isinstance(res["advisory_sections"], dict)

    sections = res["advisory_sections"]
    required_sections = [
        "1_varieties",
        "2_land_preparation",
        "3_planting_schedule",
        "4_fertilizer_management",
        "5_water_management",
        "6_weed_control",
        "7_harvesting_and_post_harvest",
        "8_crop_rotation_and_intercropping"
    ]
    for section_key in required_sections:
        assert section_key in sections, f"Missing advisory section: {section_key}"


def test_shared_error_responses_t02_7():
    """Validate T-02.7 Shared Error Response shapes and status codes."""
    for error_file in ["error_response_400.json", "error_response_404.json", "error_response_500.json"]:
        err_res = load_fixture(error_file)
        assert "error" in err_res and isinstance(err_res["error"], dict)
        err = err_res["error"]
        assert "code" in err and isinstance(err["code"], str)
        assert "message" in err and isinstance(err["message"], str)
        assert "timestamp" in err and isinstance(err["timestamp"], str)
        assert "request_id" in err and isinstance(err["request_id"], str)


def test_health_check_endpoint():
    """Validate System Health Check response schema."""
    res = load_fixture("health_check_response.json")
    assert "status" in res and res["status"] in ["healthy", "degraded", "unhealthy"]
    assert "version" in res
    assert "services" in res and isinstance(res["services"], dict)
    for service_name in ["orchestrator", "disease_agent", "weather_agent", "rag_agent", "crop_agent"]:
        assert service_name in res["services"]


if __name__ == "__main__":
    print("Running fixture contract validation tests...")
    test_all_fixtures_are_valid_json()
    test_orchestrator_process_contract_t02_1_and_t02_6()
    test_disease_diagnose_contract_t02_2()
    test_weather_advice_contract_t02_3()
    test_rag_retrieve_contract_t02_4()
    test_crop_advice_contract_t02_5()
    test_shared_error_responses_t02_7()
    test_health_check_endpoint()
    print("All API contract fixture tests passed successfully! (100% compliant with T-02)")
