"""
Central Orchestrator Agent for Agri-Advisor (Subtasks T-06.2, T-06.3, T-06.7).
Handles intent classification, multi-agent dispatch, session context maintenance, and response synthesis.
"""

from datetime import datetime, timezone
import re
import time
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from orchestrator.schemas import (
    CropAdviceRequest,
    CropAdviceResponse,
    DiseaseDiagnoseRequest,
    DiseaseDiagnoseResponse,
    OrchestratorProcessRequest,
    OrchestratorProcessResponse,
    RagRetrieveRequest,
    RagRetrieveResponse,
    ResponseMetadata,
    SourceItem,
    WeatherAdviceRequest,
    WeatherAdviceResponse,
    WeatherAlert,
)
from orchestrator.nlp import (
    NLPResult,
    analyze_query as nlp_analyze_query,
    handle_general_query as nlp_handle_general_query,
    nlp_analyzer,
)
from orchestrator.session_context import SessionManager, session_manager as default_session_manager
from orchestrator.stubs import AgentStubService, stub_service as default_stub_service


from orchestrator.router import AgentRouter, RoutingResult, agent_router as default_agent_router


class OrchestratorAgent:
    """Central Hub coordinating specialist agents, session state, and advisory synthesis."""

    def __init__(
        self,
        session_mgr: Optional[SessionManager] = None,
        stubs: Optional[AgentStubService] = None,
        disease_agent: Optional[Callable[[
            DiseaseDiagnoseRequest], DiseaseDiagnoseResponse]] = None,
        weather_agent: Optional[Callable[[
            WeatherAdviceRequest], WeatherAdviceResponse]] = None,
        rag_agent: Optional[Callable[[RagRetrieveRequest],
                                     RagRetrieveResponse]] = None,
        crop_agent: Optional[Callable[[CropAdviceRequest],
                                      CropAdviceResponse]] = None,
        router: Optional[AgentRouter] = None,
    ) -> None:
        self.session_manager = session_mgr or default_session_manager
        self.stubs = stubs or default_stub_service
        self.router = router or AgentRouter(
            session_mgr=self.session_manager,
            stubs=self.stubs,
            disease_agent=disease_agent,
            weather_agent=weather_agent,
            rag_agent=rag_agent,
            crop_agent=crop_agent,
        )
        self.nlp = nlp_analyzer

    def analyze_query(self, query: str) -> NLPResult:
        """Analyze query using the T-10 NLP pipeline."""
        return self.nlp.analyze_query(query)

    def handle_general_query(self, query: str, nlp_result: Optional[NLPResult] = None) -> Dict[str, Any]:
        """Handle broad or unrecognised queries."""
        return self.nlp.handle_general_query(query, nlp_result)

    def classify_intent(self, query: str) -> Tuple[Literal["disease_diagnosis", "weather_query", "crop_advice", "mixed_query", "general_query"], float]:
        """Classify user intent using the NLP module."""
        result = self.nlp.analyze_query(query)
        return result.intent, result.confidence

    def extract_crop_entity(self, query: str, active_context: Optional[str] = None) -> str:
        """Extract crop from query or retain session context."""
        extracted = self.nlp.entity_extractor.extract_crop(query)
        if extracted:
            return extracted
        return active_context or "Paddy"

    def process(self, request: OrchestratorProcessRequest) -> OrchestratorProcessResponse:
        """Execute the end-to-end multi-agent orchestration workflow."""
        start_time = time.perf_counter()

        # 1. Manage session context
        session = self.session_manager.get_or_create_session(
            user_id=request.user_id,
            session_id=request.session_id,
            location=request.location.model_dump(),
            crop_context=request.crop_context,
            language=request.language,
        )

        # 2. Extract intent and crop context via NLP Layer
        nlp_res = self.nlp.analyze_query(request.query)

        # 3. Dispatch specialist agents via Router (Task T-14)
        routing_res: RoutingResult = self.router.dispatch(
            request=request,
            nlp_res=nlp_res,
            session=session,
        )

        intent = routing_res.intent
        confidence = routing_res.confidence
        crop = routing_res.crop
        agents_consulted = routing_res.selected_agents
        disease_res = routing_res.disease_response
        weather_res = routing_res.weather_response
        crop_res = routing_res.crop_response
        rag_res = routing_res.rag_response

        # 7. Synthesize Response
        answer_parts: List[str] = []
        if disease_res:
            answer_parts.append(
                f"### 🌾 Diagnosis for {crop}\n"
                f"**Identified Issue:** {disease_res.disease} (Confidence: {int(disease_res.confidence * 100)}%, Severity: {disease_res.severity})\n\n"
                f"#### Recommended Immediate Actions:\n"
                f"- **Cultural Control:** {disease_res.treatment.cultural[0].description if disease_res.treatment.cultural else 'Ensure proper field drainage.'}\n"
                f"- **Organic Treatment:** {disease_res.treatment.organic[0].name} ({disease_res.treatment.organic[0].instructions if disease_res.treatment.organic else ''})\n"
                f"- **Chemical Treatment:** {disease_res.treatment.chemical[0].name} ({disease_res.treatment.chemical[0].dosage}) - *Observe {disease_res.treatment.chemical[0].pre_harvest_interval_days}-day PHI*.\n"
            )
        elif crop_res:
            answer_parts.append(
                f"### 🌱 Cultivation Advisory for {crop} ({crop_res.season} Season)\n"
                f"**Agro-Ecological Zone:** {crop_res.agro_ecological_zone}\n\n"
                f"Please follow the Department of Agriculture 4-stage fertilizer and water management guidelines for optimal yields.\n"
            )
        else:
            answer_parts.append(
                f"### 🌾 Agricultural Advisory for {crop} ({request.location.district})\n"
                f"Based on verified guidelines from the Department of Agriculture (DOA), here are the recommended practices for your query.\n"
            )

        if weather_res and weather_res.alerts:
            top_alert = weather_res.alerts[0]
            answer_parts.append(
                f"\n> ⚠️ **Weather Advisory Notice ({top_alert.title})**: {top_alert.recommended_action}\n"
            )

        answer_text = "\n".join(answer_parts).strip()

        # 8. Map sources
        sources: List[SourceItem] = []
        if rag_res and rag_res.sources:
            for i, src in enumerate(rag_res.sources):
                score = rag_res.confidence[i] if (rag_res.confidence and i < len(
                    rag_res.confidence)) else getattr(src, "score", 0.85)
                sources.append(
                    SourceItem(
                        title=src.title,
                        author_organization=getattr(src, "author_organization", None) or getattr(
                            src, "source", "DOA Sri Lanka") or "DOA Sri Lanka",
                        document_id=getattr(src, "document_id", None) or getattr(
                            src, "source_id", "DOA-REF-01") or "DOA-REF-01",
                        section=getattr(
                            src, "section", "") or "General Agricultural Guidelines",
                        confidence_score=round(score, 2),
                        reference_url=getattr(src, "url", None) or getattr(
                            src, "reference_url", None),
                    )
                )

        # 9. Map weather alert
        if weather_res and weather_res.alerts:
            first_alert = weather_res.alerts[0]
            weather_alert = WeatherAlert(
                severity="moderate" if first_alert.severity in [
                    "watch", "advisory"] else "high",
                title=first_alert.title,
                message=first_alert.description,
                impact_warning=first_alert.recommended_action,
                valid_until=first_alert.valid_to,
            )
        else:
            weather_alert = WeatherAlert(
                severity="none",
                title="Normal Conditions",
                message="No severe weather warnings active.",
                impact_warning="Proceed with standard field operations.",
                valid_until=datetime.now(timezone.utc).isoformat(),
            )

        # 10. Record conversation turn
        self.session_manager.add_turn(
            user_id=request.user_id,
            query=request.query,
            answer=answer_text,
            intent=intent,
            language=request.language,
            agents_consulted=agents_consulted,
            session_id=session.session_id,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        metadata = ResponseMetadata(
            session_id=session.session_id,
            user_id=request.user_id,
            intent=intent,
            confidence=round(confidence, 2),
            agents_consulted=agents_consulted,
            language=request.language,
            latency_ms=max(latency_ms, 1),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        return OrchestratorProcessResponse(
            answer=answer_text,
            diagnosis=(
                {
                    "disease_name": disease_res.disease,
                    "severity": disease_res.severity,
                    "confidence": disease_res.confidence,
                    "confidence_label": (
                        "High" if disease_res.confidence >= 0.8
                        else "Medium" if disease_res.confidence >= 0.6 else "Low"
                    ),
                    "symptoms_confirmed": disease_res.symptoms_confirmed,
                    "differential_diagnoses": [
                        item.model_dump() for item in (disease_res.differential_diagnoses or [])
                    ],
                }
                if disease_res else None
            ),
            immediate_treatment=(
                {
                    "urgency": "High Priority",
                    "action_window": "Apply according to the treatment guidance below.",
                    "steps": [
                        {
                            "priority": index,
                            "action": treatment.name if hasattr(treatment, "name") else treatment.practice,
                            "detail": treatment.instructions if hasattr(treatment, "instructions") else treatment.description,
                            "urgency_tag": "Recommended",
                        }
                        for index, treatment in enumerate(
                            list(disease_res.treatment.chemical)
                            + list(disease_res.treatment.organic)
                            + list(disease_res.treatment.cultural),
                            1,
                        )
                    ],
                }
                if disease_res else None
            ),
            prevention=disease_res.prevention if disease_res else [],
            sources=sources,
            weather_alert=weather_alert,
            disclaimer={
                "text": (
                    "This advisory is generated by an AI system to support your decision-making. "
                    "It does not replace professional agricultural extension advice."
                ),
                "helpline": "Agriculture Extension Office: 1920",
            },
            why_explanation={
                "summary": f"The advisory was selected for {crop} using the routed specialist agents and verified knowledge sources.",
                "model_reasoning": f"The orchestrator consulted: {', '.join(agents_consulted) or 'the general advisory path'}.",
                "agents_used": agents_consulted,
                "confidence_breakdown": {"orchestrator": round(confidence, 2)},
            },
            metadata=metadata,
        )


orchestrator_agent = OrchestratorAgent()
