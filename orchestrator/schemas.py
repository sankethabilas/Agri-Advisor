"""
Pydantic Schemas for Agri-Advisor Orchestrator and Specialist Agents.
Strictly compliant with API Contract Specification v1.0.0 (docs/api-contract.md).
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# Common & Location Models
# ==============================================================================

class Location(BaseModel):
    district: str = Field(..., description="e.g. Anuradhapura, Kurunegala, Polonnaruwa, Badulla")
    province: Optional[str] = Field(None, description="e.g. North Central, North Western")
    latitude: Optional[float] = Field(None, ge=5.0, le=10.0)
    longitude: Optional[float] = Field(None, ge=79.0, le=82.0)
    agro_ecological_zone: Optional[str] = Field(None, description="e.g. DL1b, IL1a, WU2")


# ==============================================================================
# Orchestrator Models (T-02.1 & T-02.6)
# ==============================================================================

class OrchestratorProcessRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query from farmer")
    user_id: str = Field(..., description="Unique farmer or session identifier")
    location: Location
    session_id: Optional[str] = Field(None, description="Optional session UUID for multi-turn state")
    language: Literal["en", "si", "ta"] = Field("en", description="Target language for synthesized response")
    crop_context: Optional[str] = Field(None, description="Optional active crop context e.g. Paddy, Tomato")


class SourceItem(BaseModel):
    title: str
    author_organization: str
    document_id: str
    section: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reference_url: Optional[str] = None


class WeatherAlert(BaseModel):
    severity: Literal["none", "low", "moderate", "high", "severe"]
    title: str
    message: str
    impact_warning: str
    valid_until: str


class ResponseMetadata(BaseModel):
    session_id: str
    user_id: str
    intent: Literal[
        "disease_diagnosis",
        "weather_inquiry",
        "weather_query",
        "crop_cultivation",
        "crop_advice",
        "general_farming",
        "general_query",
        "mixed",
        "mixed_query",
    ]
    confidence: float = Field(..., ge=0.0, le=1.0)
    agents_consulted: List[str]
    language: Literal["en", "si", "ta"]
    latency_ms: int
    timestamp: str


class OrchestratorProcessResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    weather_alert: WeatherAlert
    metadata: ResponseMetadata


class AuthCredentials(BaseModel):
    username: str = Field(..., min_length=3, max_length=254, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.@+-]{2,253}$")
    password: str = Field(..., min_length=12, max_length=128)


# ==============================================================================
# Disease Diagnosis Models (T-02.2)
# ==============================================================================

class DiseaseDiagnoseRequest(BaseModel):
    crop: str
    symptoms: List[str] = Field(..., min_length=1)
    location: Location
    growth_stage: Optional[str] = None
    season: Optional[Literal["Maha", "Yala"]] = None


class ChemicalTreatment(BaseModel):
    name: str
    dosage: str
    instructions: str
    pre_harvest_interval_days: int


class OrganicTreatment(BaseModel):
    name: str
    dosage: str
    instructions: str


class CulturalTreatment(BaseModel):
    practice: str
    description: str


class TreatmentPlan(BaseModel):
    chemical: List[ChemicalTreatment]
    organic: List[OrganicTreatment]
    cultural: List[CulturalTreatment]


class DifferentialDiagnosis(BaseModel):
    disease: str
    confidence: float
    distinguishing_factor: str


class DiseaseDiagnoseResponse(BaseModel):
    disease: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: Literal["Low", "Moderate", "High", "Critical"]
    treatment: TreatmentPlan
    prevention: List[str]
    source: str
    symptoms_confirmed: List[str]
    differential_diagnoses: Optional[List[DifferentialDiagnosis]] = None


# ==============================================================================
# Weather & Risk Models (T-02.3)
# ==============================================================================

class WeatherAdviceRequest(BaseModel):
    location: Location
    crop: Optional[str] = None
    growth_stage: Optional[str] = None


class CurrentWeather(BaseModel):
    temperature_c: float
    humidity_pct: int
    rainfall_mm: float
    wind_speed_kmh: float
    wind_direction: Optional[str] = None
    condition: str
    icon: str
    timestamp: str


class DailyForecast(BaseModel):
    date: str
    temp_min_c: float
    temp_max_c: float
    rainfall_mm: float
    rainfall_prob_pct: int
    humidity_pct: int
    wind_speed_kmh: float
    condition: str


class DiseaseRisk(BaseModel):
    level: Literal["Low", "Moderate", "High", "Critical"]
    score: float = Field(..., ge=0.0, le=1.0)
    susceptible_diseases: List[str]
    contributing_factors: List[str]
    recommendation: Optional[str] = None


class PestRisk(BaseModel):
    level: Literal["Low", "Moderate", "High", "Critical"]
    score: float = Field(..., ge=0.0, le=1.0)
    susceptible_pests: List[str]
    contributing_factors: List[str]
    recommendation: Optional[str] = None


class WeatherAlertItem(BaseModel):
    id: str
    alert_type: Literal["heavy_rain", "flood", "drought", "high_wind", "pest_outbreak", "extreme_heat"]
    severity: Literal["advisory", "watch", "warning", "emergency"]
    title: str
    description: str
    valid_from: str
    valid_to: str
    recommended_action: str


class WeatherAdviceResponse(BaseModel):
    current: CurrentWeather
    forecast: List[DailyForecast]
    disease_risk: DiseaseRisk
    pest_risk: PestRisk
    advisory: str
    alerts: List[WeatherAlertItem]


# ==============================================================================
# RAG / IR Models (T-02.4)
# ==============================================================================

class RagRetrieveRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)
    crop_filter: Optional[str] = None
    category_filter: Optional[str] = None
    min_score: float = Field(default=0.60, ge=0.0, le=1.0)


class RagSourceItem(BaseModel):
    id: str
    title: str
    content: str
    crop: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None
    source_id: Optional[str] = None
    region: Optional[str] = None
    season: Optional[str] = None
    score: float = Field(..., ge=0.0, le=1.0)
    document_id: Optional[str] = None
    section: Optional[str] = None
    author_organization: Optional[str] = None
    publication_year: Optional[int] = None
    url: Optional[str] = None
    reference_url: Optional[str] = None


class RagMetadata(BaseModel):
    total_chunks_retrieved: Optional[int] = None
    query_embedding_model: Optional[str] = None
    vector_distance_metric: Optional[str] = None
    execution_time_ms: Optional[int] = None


class RagRetrieveResponse(BaseModel):
    context: str
    sources: List[RagSourceItem]
    confidence: List[float]
    metadata: Optional[RagMetadata] = None


# ==============================================================================
# Crop Advisory Models (T-02.5)
# ==============================================================================

class CropAdviceRequest(BaseModel):
    crop: str
    location: Location
    season: Literal["Maha", "Yala"]
    soil_type: Optional[str] = None
    land_extent_acres: Optional[float] = 1.0
    irrigation_type: Optional[Literal["Major Irrigation", "Minor Irrigation", "Rainfed"]] = None


class CropAdviceResponse(BaseModel):
    crop: str
    season: Literal["Maha", "Yala"]
    agro_ecological_zone: str
    soil_type: Optional[str] = None
    land_extent_acres: Optional[float] = None
    advisory_sections: Dict[str, Any]
    source: str
    generated_at: str


# ==============================================================================
# System Health & Error Models (T-02.7 & Health)
# ==============================================================================

class ServiceHealth(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    latency_ms: int
    message: str


class HealthCheckResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    environment: str
    timestamp: str
    services: Dict[str, ServiceHealth]


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str


class ErrorPayload(BaseModel):
    code: str
    message: str
    status_code: int
    details: Optional[List[ErrorDetail]] = None
    timestamp: str
    request_id: str


class ErrorEnvelope(BaseModel):
    error: ErrorPayload
