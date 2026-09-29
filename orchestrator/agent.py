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
from orchestrator.synthesis import ResponseSynthesizer, synthesizer as default_synthesizer
from orchestrator.responsible_ai import ResponsibleAIChecker, responsible_ai_checker as default_responsible_ai_checker


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
        synthesizer: Optional[ResponseSynthesizer] = None,
        responsible_ai: Optional[ResponsibleAIChecker] = None,
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
        self.synthesizer = synthesizer or default_synthesizer
        self.responsible_ai = responsible_ai or default_responsible_ai_checker
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

        # 7. Synthesize Response (Task T-18)
        answer_text = self.synthesizer.synthesize(request, routing_res)

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

        # 10. Execute Responsible AI mechanically (Fairness, PII Redaction, Explainability) - Task T-26
        rai_res = self.responsible_ai.check(
            response_text=answer_text,
            sources=sources,
            confidence=confidence,
            crop=crop,
            district=request.location.district or "General",
            intent=intent,
            agents_consulted=agents_consulted,
        )
        answer_text = rai_res.sanitized_response
        why_explanation = rai_res.explanation

        # 11. Record conversation turn
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
            why_explanation=why_explanation,
            metadata=metadata,
        )


orchestrator_agent = OrchestratorAgent()
