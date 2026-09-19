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
from orchestrator.session_context import SessionManager, session_manager as default_session_manager
from orchestrator.stubs import AgentStubService, stub_service as default_stub_service


class OrchestratorAgent:
    """Central Hub coordinating specialist agents, session state, and advisory synthesis."""

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
        self._disease_agent = disease_agent or self.stubs.get_disease_diagnosis
        self._weather_agent = weather_agent or self.stubs.get_weather_advice
        self._rag_agent = rag_agent or self.stubs.get_rag_retrieve
        self._crop_agent = crop_agent or self.stubs.get_crop_advice

    def classify_intent(self, query: str) -> Tuple[Literal["disease_diagnosis", "weather_inquiry", "crop_cultivation", "general_farming", "mixed"], float]:
        """Classify user intent using domain keyword patterns and confidence estimation."""
        q = query.lower()

        disease_keywords = ["spot", "spots", "yellow", "brown", "blast", "rot", "wilt", "wilting", "lesion", "lesions", "fungus", "fungal", "pest", "caterpillar", "bug", "disease", "symptom", "dying", "blight"]
        weather_keywords = ["weather", "rain", "rainfall", "forecast", "monsoon", "temperature", "temp", "humidity", "flood", "drought", "wind", "storm"]
        crop_keywords = ["variety", "varieties", "fertilizer", "urea", "tsp", "mop", "planting", "sowing", "spacing", "harvest", "harvesting", "cultivation", "cultivate", "maha", "yala", "land preparation", "irrigation", "soil"]

        disease_matches = sum(1 for kw in disease_keywords if kw in q)
        weather_matches = sum(1 for kw in weather_keywords if kw in q)
        crop_matches = sum(1 for kw in crop_keywords if kw in q)

        categories = []
        if disease_matches > 0:
            categories.append("disease_diagnosis")
        if weather_matches > 0:
            categories.append("weather_inquiry")
        if crop_matches > 0:
            categories.append("crop_cultivation")

        if len(categories) > 1:
            return "mixed", 0.92
        elif len(categories) == 1:
            if categories[0] == "disease_diagnosis":
                return "disease_diagnosis", min(0.70 + (disease_matches * 0.1), 0.98)
            elif categories[0] == "weather_inquiry":
                return "weather_inquiry", min(0.70 + (weather_matches * 0.1), 0.98)
            elif categories[0] == "crop_cultivation":
                return "crop_cultivation", min(0.70 + (crop_matches * 0.1), 0.98)

        return "general_farming", 0.75

    def extract_crop_entity(self, query: str, active_context: Optional[str] = None) -> str:
        """Extract crop from query or retain session context."""
        known_crops = ["paddy", "rice", "tomato", "chilli", "chili", "maize", "corn", "brinjal", "eggplant", "tea", "rubber", "coconut", "mung bean", "cowpea", "potato", "onion"]
        q = query.lower()
        for crop in known_crops:
            if crop in q:
                if crop in ["paddy", "rice"]:
                    return "Paddy"
                if crop in ["chilli", "chili"]:
                    return "Chilli"
                if crop in ["corn", "maize"]:
                    return "Maize"
                return crop.capitalize()
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

        # 2. Extract intent and crop context
        intent, confidence = self.classify_intent(request.query)
        crop = self.extract_crop_entity(request.query, active_context=session.active_crop or request.crop_context)
        session.active_crop = crop

        agents_consulted: List[str] = []

        # 3. Query Weather Agent
        weather_req = WeatherAdviceRequest(
            location=request.location,
            crop=crop,
        )
        weather_res: WeatherAdviceResponse = self._weather_agent(weather_req)
        agents_consulted.append("weather_agent")

        # 4. Query RAG Agent for grounded citations
        rag_req = RagRetrieveRequest(
            query=request.query,
            top_k=3,
            crop_filter=crop,
        )
        rag_res: RagRetrieveResponse = self._rag_agent(rag_req)
        agents_consulted.append("rag_agent")

        # 5. Query Disease Agent if relevant
        disease_res: Optional[DiseaseDiagnoseResponse] = None
        if intent in ["disease_diagnosis", "mixed"]:
            disease_req = DiseaseDiagnoseRequest(
                crop=crop,
                symptoms=[request.query],
                location=request.location,
                season="Maha",
            )
            disease_res = self._disease_agent(disease_req)
            agents_consulted.append("disease_agent")
            if disease_res and disease_res.disease not in session.confirmed_diseases:
                session.confirmed_diseases.append(disease_res.disease)

        # 6. Query Crop Agent if relevant
        crop_res: Optional[CropAdviceResponse] = None
        if intent in ["crop_cultivation", "mixed"]:
            crop_req = CropAdviceRequest(
                crop=crop,
                location=request.location,
                season="Maha",
                soil_type="Reddish Brown Earths (RBE)",
            )
            crop_res = self._crop_agent(crop_req)
            agents_consulted.append("crop_agent")

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

        if weather_res.alerts:
            top_alert = weather_res.alerts[0]
            answer_parts.append(
                f"\n> ⚠️ **Weather Advisory Notice ({top_alert.title})**: {top_alert.recommended_action}\n"
            )

        answer_text = "\n".join(answer_parts).strip()

        # 8. Map sources
        sources: List[SourceItem] = []
        for i, src in enumerate(rag_res.sources):
            score = rag_res.confidence[i] if i < len(rag_res.confidence) else 0.85
            sources.append(
                SourceItem(
                    title=src.title,
                    author_organization=src.author_organization,
                    document_id=src.document_id,
                    section=src.section,
                    confidence_score=round(score, 2),
                    reference_url=src.url,
                )
            )

        # 9. Map weather alert
        if weather_res.alerts:
            first_alert = weather_res.alerts[0]
            weather_alert = WeatherAlert(
                severity="moderate" if first_alert.severity in ["watch", "advisory"] else "high",
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
            sources=sources,
            weather_alert=weather_alert,
            metadata=metadata,
        )


orchestrator_agent = OrchestratorAgent()
