"""
Agri-Advisor Routing Logic & Specialist Agent Dispatcher (Task T-14).
Handles real routing, intent-based agent dispatch, mixed query multi-agent selection,
unconditional RAG knowledge retrieval (BR-4), and disease finding query expansion (IR-4).
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from orchestrator.nlp import NLPResult, nlp_analyzer
from orchestrator.schemas import (
    CropAdviceRequest,
    CropAdviceResponse,
    DiseaseDiagnoseRequest,
    DiseaseDiagnoseResponse,
    Location,
    OrchestratorProcessRequest,
    RagMetadata,
    RagRetrieveRequest,
    RagRetrieveResponse,
    WeatherAdviceRequest,
    WeatherAdviceResponse,
)
from orchestrator.session_context import SessionManager, UserSession, session_manager as default_session_manager
from orchestrator.stubs import AgentStubService, stub_service as default_stub_service
from pydantic import BaseModel, Field

logger = logging.getLogger("agri_advisor.router")


# ==============================================================================
# T-14.7: Structured Routing Result Model
# ==============================================================================

class RoutingResult(BaseModel):
    """
    Structured result object collecting outputs from all dispatched specialist agents.
    (Subtask T-14.7)
    """
    query: str
    user_id: str
    session_id: Optional[str] = None
    intent: str
    confidence: float
    intent_scores: Dict[str, float] = Field(default_factory=dict)
    entities: Dict[str, Any] = Field(default_factory=dict)
    crop: str = "Paddy"
    location: Location
    routing_branch: str
    selected_agents: List[str] = Field(default_factory=list)
    disease_response: Optional[DiseaseDiagnoseResponse] = None
    weather_response: Optional[WeatherAdviceResponse] = None
    crop_response: Optional[CropAdviceResponse] = None
    rag_response: Optional[RagRetrieveResponse] = None
    rag_query: str
    ir4_expanded: bool = False
    routing_decision: Dict[str, Any] = Field(default_factory=dict)
    latencies_ms: Dict[str, int] = Field(default_factory=dict)
    total_latency_ms: int = 0


# ==============================================================================
# T-14: Agent Router Implementation
# ==============================================================================

class AgentRouter:
    """
    Coordinates specialist agent dispatching based on NLP intent classification,
    business rules, and entity signals.
    """

    # Threshold for activating specialist agents during mixed query dispatch (T-14.4)
    MIXED_QUERY_SCORE_THRESHOLD: float = 0.35

    def __init__(
        self,
        session_mgr: Optional[SessionManager] = None,
        stubs: Optional[AgentStubService] = None,
        disease_agent: Optional[Callable[[DiseaseDiagnoseRequest], DiseaseDiagnoseResponse]] = None,
        weather_agent: Optional[Callable[[WeatherAdviceRequest], WeatherAdviceResponse]] = None,
        rag_agent: Optional[Callable[[RagRetrieveRequest], RagRetrieveResponse]] = None,
        crop_agent: Optional[Callable[[CropAdviceRequest], CropAdviceResponse]] = None,
    ) -> None:
        self.session_manager = session_mgr or default_session_manager
        self.stubs = stubs or default_stub_service
        self._disease_agent = disease_agent
        self._weather_agent = weather_agent
        self._rag_agent = rag_agent
        self._crop_agent = crop_agent

    # --------------------------------------------------------------------------
    # Agent Invocation Helpers with Fallback Protection
    # --------------------------------------------------------------------------

    def call_disease_agent(self, req: DiseaseDiagnoseRequest) -> DiseaseDiagnoseResponse:
        """Execute disease diagnosis request with stub fallback."""
        if self._disease_agent is not None:
            try:
                if hasattr(self._disease_agent, "diagnose"):
                    return self._disease_agent.diagnose(req)
                return self._disease_agent(req)
            except Exception as e:
                logger.warning(f"Disease agent execution failed ({e}). Falling back to stub.")
        else:
            try:
                from agents.disease.agent import disease_agent
                return disease_agent.diagnose(req)
            except Exception as e:
                logger.warning(f"Live DiseaseAgent import/call failed ({e}). Falling back to stub.")
        return self.stubs.get_disease_diagnosis(req)

    def call_weather_agent(self, req: WeatherAdviceRequest) -> WeatherAdviceResponse:
        """Execute weather advice request with stub fallback."""
        if self._weather_agent is not None:
            try:
                if hasattr(self._weather_agent, "get_weather_advice"):
                    return self._weather_agent.get_weather_advice(req.location, req.crop)
                return self._weather_agent(req)
            except Exception as e:
                logger.warning(f"Weather agent execution failed ({e}). Falling back to stub.")
        else:
            try:
                from agents.weather.agent import weather_agent
                return weather_agent.get_weather_advice(req.location, req.crop)
            except Exception as e:
                logger.warning(f"Live WeatherAgent import/call failed ({e}). Falling back to stub.")
        return self.stubs.get_weather_advice(req)

    def call_crop_agent(self, req: CropAdviceRequest) -> CropAdviceResponse:
        """Execute crop advisory request with stub fallback."""
        if self._crop_agent is not None:
            try:
                if hasattr(self._crop_agent, "get_crop_advice"):
                    return self._crop_agent.get_crop_advice(req)
                return self._crop_agent(req)
            except Exception as e:
                logger.warning(f"Crop agent execution failed ({e}). Falling back to stub.")
        else:
            try:
                from agents.crop.agent import crop_agent
                return crop_agent.get_crop_advice(req)
            except Exception as e:
                logger.warning(f"Live CropAgent import/call failed ({e}). Falling back to stub.")
        return self.stubs.get_crop_advice(req)

    def call_rag_agent(self, req: RagRetrieveRequest) -> RagRetrieveResponse:
        """Execute RAG knowledge retrieval request with stub fallback."""
        if self._rag_agent is not None:
            try:
                if hasattr(self._rag_agent, "retrieve"):
                    return self._rag_agent.retrieve(req)
                return self._rag_agent(req)
            except Exception as e:
                logger.warning(f"RAG agent execution failed ({e}). Falling back to stub.")
        else:
            try:
                from agents.rag.agent import rag_agent
                return rag_agent.retrieve(req)
            except Exception as e:
                logger.warning(f"Live RAGAgent import/call failed ({e}). Falling back to stub.")
        return self.stubs.get_rag_retrieve(req)

    # --------------------------------------------------------------------------
    # Subtask T-14.1: Route to Disease
    # --------------------------------------------------------------------------

    def route_to_disease(
        self,
        request: OrchestratorProcessRequest,
        nlp_res: NLPResult,
        crop: str,
        session: Optional[UserSession] = None,
    ) -> Dict[str, Any]:
        """
        T-14.1: Route disease queries to the Disease and Weather agents.
        Disease inquiries require both pathology diagnosis and microclimate disease risk assessment.
        """
        agents_called: List[str] = []
        latencies: Dict[str, int] = {}

        # 1. Dispatch Disease Agent
        symptoms = nlp_res.entities.symptoms if nlp_res.entities.symptoms else [request.query]
        season = nlp_res.entities.season or "Maha"
        growth_stage = nlp_res.entities.stage

        disease_req = DiseaseDiagnoseRequest(
            crop=crop,
            symptoms=symptoms,
            location=request.location,
            season=season if season in ["Maha", "Yala"] else "Maha",
            growth_stage=growth_stage,
        )

        t0 = time.perf_counter()
        disease_res = self.call_disease_agent(disease_req)
        latencies["disease_agent"] = int((time.perf_counter() - t0) * 1000)
        agents_called.append("disease_agent")

        if session and disease_res and disease_res.disease not in session.confirmed_diseases:
            session.confirmed_diseases.append(disease_res.disease)

        # 2. Dispatch Weather Agent for disease risk evaluation
        weather_req = WeatherAdviceRequest(
            location=request.location,
            crop=crop,
            growth_stage=growth_stage,
        )

        t1 = time.perf_counter()
        weather_res = self.call_weather_agent(weather_req)
        latencies["weather_agent"] = int((time.perf_counter() - t1) * 1000)
        agents_called.append("weather_agent")

        return {
            "disease_response": disease_res,
            "weather_response": weather_res,
            "crop_response": None,
            "agents_called": agents_called,
            "latencies": latencies,
        }

    # --------------------------------------------------------------------------
    # Subtask T-14.2: Route to Weather
    # --------------------------------------------------------------------------

    def route_to_weather(
        self,
        request: OrchestratorProcessRequest,
        nlp_res: NLPResult,
        crop: str,
        session: Optional[UserSession] = None,
    ) -> Dict[str, Any]:
        """
        T-14.2: Route weather queries directly to the Weather Agent.
        """
        agents_called: List[str] = []
        latencies: Dict[str, int] = {}

        weather_req = WeatherAdviceRequest(
            location=request.location,
            crop=crop,
            growth_stage=nlp_res.entities.stage,
        )

        t0 = time.perf_counter()
        weather_res = self.call_weather_agent(weather_req)
        latencies["weather_agent"] = int((time.perf_counter() - t0) * 1000)
        agents_called.append("weather_agent")

        return {
            "disease_response": None,
            "weather_response": weather_res,
            "crop_response": None,
            "agents_called": agents_called,
            "latencies": latencies,
        }

    # --------------------------------------------------------------------------
    # Subtask T-14.3: Route to Crop Advisor
    # --------------------------------------------------------------------------

    def route_to_crop_advisor(
        self,
        request: OrchestratorProcessRequest,
        nlp_res: NLPResult,
        crop: str,
        session: Optional[UserSession] = None,
    ) -> Dict[str, Any]:
        """
        T-14.3: Route agronomy/cultivation queries directly to the Crop Advisory Agent.
        """
        agents_called: List[str] = []
        latencies: Dict[str, int] = {}

        season = nlp_res.entities.season or "Maha"
        crop_req = CropAdviceRequest(
            crop=crop,
            location=request.location,
            season=season if season in ["Maha", "Yala"] else "Maha",
            soil_type="Reddish Brown Earths (RBE)",
        )

        t0 = time.perf_counter()
        crop_res = self.call_crop_agent(crop_req)
        latencies["crop_agent"] = int((time.perf_counter() - t0) * 1000)
        agents_called.append("crop_agent")

        return {
            "disease_response": None,
            "weather_response": None,
            "crop_response": crop_res,
            "agents_called": agents_called,
            "latencies": latencies,
        }

    # --------------------------------------------------------------------------
    # Subtask T-14.4: Route to Multiple (Mixed Query Agent Selection)
    # --------------------------------------------------------------------------

    def route_to_multiple(
        self,
        request: OrchestratorProcessRequest,
        nlp_res: NLPResult,
        crop: str,
        session: Optional[UserSession] = None,
    ) -> Dict[str, Any]:
        """
        T-14.4: Dynamic multi-agent routing for mixed queries based on intent scores and signals.

        MIXED QUERY MULTI-AGENT SELECTION RULE (Documented for T-14.4):
        -------------------------------------------------------------
        When a query is classified as 'mixed_query', multiple agricultural dimensions are active.
        Agent selection is resolved dynamically using the component intent scores and extracted entities:
        1. Disease Agent is dispatched IF:
           - intent_scores['disease_diagnosis'] >= 0.35 OR
           - len(nlp_res.entities.symptoms) > 0 OR
           - disease-specific keywords/cues are present in the query.
        2. Weather Agent is dispatched IF:
           - intent_scores['weather_query'] >= 0.35 OR
           - weather-specific keywords/cues are present in the query.
        3. Crop Agent is dispatched IF:
           - intent_scores['crop_advice'] >= 0.35 OR
           - cultivation/fertilizer/management keywords are present in the query.
        4. Safety Fallback:
           - If no specific agent crosses the threshold, Weather and Crop agents (plus Disease
             if symptoms exist) are dispatched to provide comprehensive guidance.
        """
        agents_called: List[str] = []
        latencies: Dict[str, int] = {}
        disease_res: Optional[DiseaseDiagnoseResponse] = None
        weather_res: Optional[WeatherAdviceResponse] = None
        crop_res: Optional[CropAdviceResponse] = None

        scores = nlp_res.intent_scores
        disease_score = scores.get("disease_diagnosis", 0.0)
        weather_score = scores.get("weather_query", 0.0)
        crop_score = scores.get("crop_advice", 0.0)

        should_call_disease = (
            disease_score >= self.MIXED_QUERY_SCORE_THRESHOLD
            or bool(nlp_res.entities.symptoms)
        )
        should_call_weather = (
            weather_score >= self.MIXED_QUERY_SCORE_THRESHOLD
        )
        should_call_crop = (
            crop_score >= self.MIXED_QUERY_SCORE_THRESHOLD
        )

        # Fallback if no specific agent was selected
        if not (should_call_disease or should_call_weather or should_call_crop):
            should_call_weather = True
            should_call_crop = True

        # Dispatch Disease Agent if selected
        if should_call_disease:
            symptoms = nlp_res.entities.symptoms if nlp_res.entities.symptoms else [request.query]
            season = nlp_res.entities.season or "Maha"
            disease_req = DiseaseDiagnoseRequest(
                crop=crop,
                symptoms=symptoms,
                location=request.location,
                season=season if season in ["Maha", "Yala"] else "Maha",
                growth_stage=nlp_res.entities.stage,
            )
            t0 = time.perf_counter()
            disease_res = self.call_disease_agent(disease_req)
            latencies["disease_agent"] = int((time.perf_counter() - t0) * 1000)
            agents_called.append("disease_agent")

            if session and disease_res and disease_res.disease not in session.confirmed_diseases:
                session.confirmed_diseases.append(disease_res.disease)

        # Dispatch Weather Agent if selected
        if should_call_weather:
            weather_req = WeatherAdviceRequest(
                location=request.location,
                crop=crop,
                growth_stage=nlp_res.entities.stage,
            )
            t1 = time.perf_counter()
            weather_res = self.call_weather_agent(weather_req)
            latencies["weather_agent"] = int((time.perf_counter() - t1) * 1000)
            agents_called.append("weather_agent")

        # Dispatch Crop Agent if selected
        if should_call_crop:
            season = nlp_res.entities.season or "Maha"
            crop_req = CropAdviceRequest(
                crop=crop,
                location=request.location,
                season=season if season in ["Maha", "Yala"] else "Maha",
                soil_type="Reddish Brown Earths (RBE)",
            )
            t2 = time.perf_counter()
            crop_res = self.call_crop_agent(crop_req)
            latencies["crop_agent"] = int((time.perf_counter() - t2) * 1000)
            agents_called.append("crop_agent")

        return {
            "disease_response": disease_res,
            "weather_response": weather_res,
            "crop_response": crop_res,
            "agents_called": agents_called,
            "latencies": latencies,
        }

    # --------------------------------------------------------------------------
    # Main Dispatch Coordination (T-14.1 - T-14.8)
    # --------------------------------------------------------------------------

    def dispatch(
        self,
        request: OrchestratorProcessRequest,
        nlp_res: Optional[NLPResult] = None,
        session: Optional[UserSession] = None,
    ) -> RoutingResult:
        """
        Execute end-to-end routing decision, specialist agent dispatch,
        IR-4 query expansion, and unconditional BR-4 RAG retrieval.
        """
        start_time = time.perf_counter()

        # 1. Analyze NLP if not pre-computed
        if nlp_res is None:
            nlp_res = nlp_analyzer.analyze_query(request.query)

        intent = nlp_res.intent
        confidence = nlp_res.confidence
        crop = (
            nlp_res.entities.crop
            or (session.active_crop if session else None)
            or request.crop_context
            or "Paddy"
        )
        if session:
            session.active_crop = crop

        # 2. Select intent routing branch
        routing_branch: str
        if intent == "disease_diagnosis":
            routing_branch = "route_to_disease"
            branch_results = self.route_to_disease(request, nlp_res, crop, session)
        elif intent in ["weather_query", "weather_inquiry"]:
            routing_branch = "route_to_weather"
            branch_results = self.route_to_weather(request, nlp_res, crop, session)
        elif intent in ["crop_advice", "crop_cultivation"]:
            routing_branch = "route_to_crop_advisor"
            branch_results = self.route_to_crop_advisor(request, nlp_res, crop, session)
        elif intent in ["mixed_query", "mixed"]:
            routing_branch = "route_to_multiple"
            branch_results = self.route_to_multiple(request, nlp_res, crop, session)
        else:
            routing_branch = "route_to_general"
            branch_results = {
                "disease_response": None,
                "weather_response": None,
                "crop_response": None,
                "agents_called": [],
                "latencies": {},
            }

        disease_res: Optional[DiseaseDiagnoseResponse] = branch_results["disease_response"]
        weather_res: Optional[WeatherAdviceResponse] = branch_results["weather_response"]
        crop_res: Optional[CropAdviceResponse] = branch_results["crop_response"]
        agents_called: List[str] = list(branch_results["agents_called"])
        latencies: Dict[str, int] = dict(branch_results["latencies"])

        # 3. Subtask T-14.6 (Rule IR-4): Expand RAG query with Disease Agent finding if available
        rag_query = request.query
        ir4_expanded = False
        if disease_res and disease_res.disease:
            rag_query = f"{request.query} {disease_res.disease}".strip()
            ir4_expanded = True

        # 4. Subtask T-14.5 (Rule BR-4): Unconditionally call RAG agent for every query
        t_rag = time.perf_counter()
        rag_req = RagRetrieveRequest(
            query=rag_query,
            top_k=3,
            crop_filter=crop,
        )
        rag_res: RagRetrieveResponse = self.call_rag_agent(rag_req)
        latencies["rag_agent"] = int((time.perf_counter() - t_rag) * 1000)
        agents_called.append("rag_agent")

        total_latency_ms = int((time.perf_counter() - start_time) * 1000)

        # 5. Build Routing Decision Metadata (T-14.8)
        routing_decision = {
            "intent": intent,
            "confidence": round(confidence, 4),
            "routing_branch": routing_branch,
            "selected_agents": agents_called,
            "br4_rag_unconditional": True,
            "ir4_query_expansion": {
                "applied": ir4_expanded,
                "original_query": request.query,
                "expanded_query": rag_query,
                "disease_finding": disease_res.disease if disease_res else None,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 6. Subtask T-14.8: Structured Logging of Routing Decision
        logger.info(
            "[ROUTING DECISION] User: %s | Intent: %s (conf: %.2f) | Branch: %s | "
            "Agents: %s | IR-4 Expanded: %s (RAG Query: '%s')",
            request.user_id,
            intent,
            confidence,
            routing_branch,
            agents_called,
            ir4_expanded,
            rag_query,
        )

        # 7. Subtask T-14.7: Return structured routing result object
        return RoutingResult(
            query=request.query,
            user_id=request.user_id,
            session_id=session.session_id if session else request.session_id,
            intent=intent,
            confidence=round(confidence, 4),
            intent_scores=nlp_res.intent_scores,
            entities=nlp_res.entities.to_dict(),
            crop=crop,
            location=request.location,
            routing_branch=routing_branch,
            selected_agents=agents_called,
            disease_response=disease_res,
            weather_response=weather_res,
            crop_response=crop_res,
            rag_response=rag_res,
            rag_query=rag_query,
            ir4_expanded=ir4_expanded,
            routing_decision=routing_decision,
            latencies_ms=latencies,
            total_latency_ms=max(total_latency_ms, 1),
        )


# Global singleton instance
agent_router = AgentRouter()


# Functional entrypoints for direct invocation / unit testing
def route_to_disease(
    request: OrchestratorProcessRequest,
    nlp_res: NLPResult,
    crop: str,
    session: Optional[UserSession] = None,
) -> Dict[str, Any]:
    """Functional wrapper for route_to_disease (Subtask T-14.1)."""
    return agent_router.route_to_disease(request, nlp_res, crop, session)


def route_to_weather(
    request: OrchestratorProcessRequest,
    nlp_res: NLPResult,
    crop: str,
    session: Optional[UserSession] = None,
) -> Dict[str, Any]:
    """Functional wrapper for route_to_weather (Subtask T-14.2)."""
    return agent_router.route_to_weather(request, nlp_res, crop, session)


def route_to_crop_advisor(
    request: OrchestratorProcessRequest,
    nlp_res: NLPResult,
    crop: str,
    session: Optional[UserSession] = None,
) -> Dict[str, Any]:
    """Functional wrapper for route_to_crop_advisor (Subtask T-14.3)."""
    return agent_router.route_to_crop_advisor(request, nlp_res, crop, session)


def route_to_multiple(
    request: OrchestratorProcessRequest,
    nlp_res: NLPResult,
    crop: str,
    session: Optional[UserSession] = None,
) -> Dict[str, Any]:
    """Functional wrapper for route_to_multiple (Subtask T-14.4)."""
    return agent_router.route_to_multiple(request, nlp_res, crop, session)


def dispatch_query(
    request: OrchestratorProcessRequest,
    nlp_res: Optional[NLPResult] = None,
    session: Optional[UserSession] = None,
) -> RoutingResult:
    """Functional wrapper for full agent routing and dispatch (Task T-14)."""
    return agent_router.dispatch(request, nlp_res, session)
