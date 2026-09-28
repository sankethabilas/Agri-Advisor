"""
Agri-Advisor Central Orchestrator Service (Task T-06).
FastAPI application exposing multi-agent orchestration, session management, and stub endpoints.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
import uuid

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from orchestrator.agent import orchestrator_agent
from orchestrator.logging_middleware import RequestLoggingMiddleware, logger
from orchestrator.schemas import (
    CropAdviceRequest,
    CropAdviceResponse,
    DiseaseDiagnoseRequest,
    DiseaseDiagnoseResponse,
    ErrorDetail,
    ErrorEnvelope,
    ErrorPayload,
    HealthCheckResponse,
    OrchestratorProcessRequest,
    OrchestratorProcessResponse,
    RagRetrieveRequest,
    RagRetrieveResponse,
    WeatherAdviceRequest,
    WeatherAdviceResponse,
)
from orchestrator.session_context import session_manager
from orchestrator.stubs import stub_service
from agents.weather.agent import WeatherServiceError, weather_agent
from agents.disease.agent import disease_agent

app = FastAPI(
    title="Agri-Advisor Orchestrator Hub",
    description="Multi-Agent Conversational AI Hub for Sri Lankan Agriculture (Compliant with API Contract v1.0.0)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. Mount Logging & CORS Middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Standard RFC 7807 Error Handlers (Subtask T-02.7)
# ==============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", f"req-{uuid.uuid4().hex[:8]}")
    details = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        details.append(ErrorDetail(field=field_path, issue=err.get("msg", "Invalid parameter")))

    payload = ErrorPayload(
        code="VALIDATION_ERROR",
        message="Request failed validation against API contract.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
        timestamp=datetime.now(timezone.utc).isoformat(),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorEnvelope(error=payload).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", f"req-{uuid.uuid4().hex[:8]}")
    code_map = {
        400: "VALIDATION_ERROR",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "RESOURCE_NOT_FOUND",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "UPSTREAM_AGENT_ERROR",
        503: "SERVICE_UNAVAILABLE",
        504: "AGENT_TIMEOUT",
    }
    error_code = code_map.get(exc.status_code, "ERROR")

    payload = ErrorPayload(
        code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code,
        details=None,
        timestamp=datetime.now(timezone.utc).isoformat(),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorEnvelope(error=payload).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", f"req-{uuid.uuid4().hex[:8]}")
    logger.error(f"Unhandled exception in request {request_id}: {exc}", exc_info=True)

    payload = ErrorPayload(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=[ErrorDetail(field="server", issue=str(exc))],
        timestamp=datetime.now(timezone.utc).isoformat(),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorEnvelope(error=payload).model_dump(),
    )


# ==============================================================================
# Primary Orchestrator Endpoints (Subtask T-06.2)
# ==============================================================================

@app.post(
    "/api/orchestrator/process",
    response_model=OrchestratorProcessResponse,
    summary="Process Farmer Query End-to-End",
    description="Analyzes farmer intent, routes to specialist agents, grounds citations, and returns synthesized advisory.",
    tags=["Orchestrator"],
)
async def process_farmer_query(request: OrchestratorProcessRequest) -> OrchestratorProcessResponse:
    try:
        return orchestrator_agent.process(request)
    except Exception as error:
        logger.error(f"Orchestration pipeline failure: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query through multi-agent pipeline: {error}",
        )


# ==============================================================================
# Specialist Agent Stub Endpoints (Subtask T-06.4)
# ==============================================================================

@app.post(
    "/api/disease/diagnose",
    response_model=DiseaseDiagnoseResponse,
    summary="Diagnose Crop Disease",
    description="Matches symptoms to diseases, determines severity, and generates 3-tier treatment recommendations.",
    tags=["Disease Agent"],
)
async def diagnose_crop_disease(request: DiseaseDiagnoseRequest) -> DiseaseDiagnoseResponse:
    return disease_agent.diagnose(request)


@app.post(
    "/api/weather/advice",
    response_model=WeatherAdviceResponse,
    summary="Get Live Weather & Microclimate Risks",
    description="Returns live weather conditions, 7-day forecast, disease/pest risk scores, and weather alerts.",
    tags=["Weather Agent"],
)
async def get_weather_advice(request: WeatherAdviceRequest) -> WeatherAdviceResponse:
    try:
        return weather_agent.get_weather_advice(request.location, request.crop)
    except WeatherServiceError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error


@app.post(
    "/api/rag/retrieve",
    response_model=RagRetrieveResponse,
    summary="Retrieve Grounded Knowledge (Stub)",
    description="Performs semantic search over DOA/IRRI verified corpus using ChromaDB embeddings.",
    tags=["RAG Agent"],
)
async def retrieve_rag_knowledge(request: RagRetrieveRequest) -> RagRetrieveResponse:
    return stub_service.get_rag_retrieve(request)


@app.post(
    "/api/crop/advice",
    response_model=CropAdviceResponse,
    summary="Get 8-Stage Cultivation Advice (Stub)",
    description="Generates complete 8-stage agronomic cultivation schedule tailored to zone and season.",
    tags=["Crop Agent"],
)
async def get_crop_cultivation_advice(request: CropAdviceRequest) -> CropAdviceResponse:
    return stub_service.get_crop_advice(request)


# ==============================================================================
# System Health & Session Management Endpoints (Subtask T-06.5 & T-06.7)
# ==============================================================================

@app.get(
    "/api/health",
    response_model=HealthCheckResponse,
    summary="System Health Check",
    tags=["System"],
)
async def health_check() -> HealthCheckResponse:
    return stub_service.get_health_check()


@app.get(
    "/api/sessions/{user_id}",
    summary="Get User Session Context",
    tags=["Session Management"],
)
async def get_user_session(user_id: str) -> Dict[str, Any]:
    session = session_manager.get_session(user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found for user '{user_id}'",
        )
    return session.to_dict()


@app.delete(
    "/api/sessions/{user_id}",
    summary="Clear User Session Context",
    tags=["Session Management"],
)
async def clear_user_session(user_id: str) -> Dict[str, Any]:
    cleared = session_manager.clear_session(user_id)
    if not cleared:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active session found to clear for user '{user_id}'",
        )
    return {"message": f"Session for user '{user_id}' successfully cleared.", "user_id": user_id}


@app.get("/", summary="System Overview", tags=["System"])
async def root_overview() -> Dict[str, Any]:
    return {
        "system": "Agri-Advisor Multi-Agent Advisory System",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "orchestrator_process": "/api/orchestrator/process",
            "disease_diagnose": "/api/disease/diagnose",
            "weather_advice": "/api/weather/advice",
            "rag_retrieve": "/api/rag/retrieve",
            "crop_advice": "/api/crop/advice",
            "health_check": "/api/health",
            "docs": "/docs",
        },
        "active_sessions": session_manager.get_active_sessions_count(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("orchestrator.main:app", host="0.0.0.0", port=8000, reload=True)
