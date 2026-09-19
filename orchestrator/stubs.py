"""
Agent Stub Services for Agri-Advisor (Subtask T-06.4).
Loads validated T-02 JSON fixtures to enable Day 2 offline development and testing.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from orchestrator.schemas import (
    CropAdviceRequest,
    CropAdviceResponse,
    DiseaseDiagnoseRequest,
    DiseaseDiagnoseResponse,
    HealthCheckResponse,
    OrchestratorProcessRequest,
    OrchestratorProcessResponse,
    RagRetrieveRequest,
    RagRetrieveResponse,
    WeatherAdviceRequest,
    WeatherAdviceResponse,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def _load_json_fixture(filename: str) -> Dict[str, Any]:
    filepath = FIXTURES_DIR / filename
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(f"Fixture not found at {filepath}")


class AgentStubService:
    """Provides contract-compliant mock responses loaded from T-02 fixtures."""

    @staticmethod
    def get_disease_diagnosis(request: Optional[DiseaseDiagnoseRequest] = None) -> DiseaseDiagnoseResponse:
        data = _load_json_fixture("disease_diagnose_response.json")
        if request and request.crop:
            data["disease"] = data.get("disease", "Paddy Blast (Pyricularia oryzae)")
        return DiseaseDiagnoseResponse.model_validate(data)

    @staticmethod
    def get_weather_advice(request: Optional[WeatherAdviceRequest] = None) -> WeatherAdviceResponse:
        data = _load_json_fixture("weather_advice_response.json")
        return WeatherAdviceResponse.model_validate(data)

    @staticmethod
    def get_rag_retrieve(request: Optional[RagRetrieveRequest] = None) -> RagRetrieveResponse:
        data = _load_json_fixture("rag_retrieve_response.json")
        if request and request.top_k:
            data["sources"] = data["sources"][: request.top_k]
            data["confidence"] = data["confidence"][: request.top_k]
        return RagRetrieveResponse.model_validate(data)

    @staticmethod
    def get_crop_advice(request: Optional[CropAdviceRequest] = None) -> CropAdviceResponse:
        data = _load_json_fixture("crop_advice_response.json")
        if request:
            data["crop"] = request.crop
            data["season"] = request.season
            if request.location.agro_ecological_zone:
                data["agro_ecological_zone"] = request.location.agro_ecological_zone
        return CropAdviceResponse.model_validate(data)

    @staticmethod
    def get_orchestrator_process(request: Optional[OrchestratorProcessRequest] = None) -> OrchestratorProcessResponse:
        data = _load_json_fixture("orchestrator_process_response.json")
        if request:
            data["metadata"]["user_id"] = request.user_id
            if request.session_id:
                data["metadata"]["session_id"] = request.session_id
            data["metadata"]["language"] = request.language
        return OrchestratorProcessResponse.model_validate(data)

    @staticmethod
    def get_health_check() -> HealthCheckResponse:
        data = _load_json_fixture("health_check_response.json")
        return HealthCheckResponse.model_validate(data)


stub_service = AgentStubService()
