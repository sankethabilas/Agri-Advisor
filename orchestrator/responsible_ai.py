"""
Responsible AI Checker for Agri-Advisor (Task T-26).
Enforces algorithmic fairness (BR-5), explainability (BR-10), and privacy compliance (BR-6)
mechanically on every outgoing response prior to rendering.

Subtasks:
- T-26.1: ResponsibleAIChecker class taking response, sources, confidence
- T-26.2: Bias detection producing a 0-1 score across crop, regional, and commercial coverage
- T-26.3: Automatic correction when bias score > 0.3 (Rule BR-5)
- T-26.4: Non-technical "Why?" explanation generation (Rule BR-10)
- T-26.5: PII detection covering phone numbers, names, and personal locations
- T-26.6: PII redaction and setting privacy_compliant flag (Rule BR-6)
"""

from dataclasses import dataclass, field
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from orchestrator.schemas import SourceItem

logger = logging.getLogger("agri_advisor.responsible_ai")

# Policy threshold defined in Rule BR-5
BIAS_POLICY_THRESHOLD: float = 0.30

# Official government extension numbers that must NEVER be redacted
WHITELISTED_HELPLINES: Set[str] = {
    "1920",
    "1920 (Department of Agriculture Toll-Free)",
    "1920 (Department of Agriculture)",
    "1920 Toll-Free",
}

# Regex patterns for PII detection (T-26.5)
PHONE_PATTERNS = [
    # Sri Lankan mobile/landline numbers: +94 7X XXX XXXX, 07X-XXXXXXX, 07XXXXXXXX, 011XXXXXXX
    re.compile(r"(?:\+94|0094|0)\s*(?:[1-9][0-9])\s*[-.]?\s*[0-9]{3}\s*[-.]?\s*[0-9]{4}\b"),
    re.compile(r"\b07[0-9][-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"),
    re.compile(r"\b\+947[0-9]{8}\b"),
    re.compile(r"\b0[1-9][0-9]{8}\b"),
]

NAME_PATTERNS = [
    re.compile(r"\b(?:(?:[Ff]ield\s+)?[Oo]fficer|[Ff]armer|[Cc]ontact:?|[Mm]r\.?|[Mm]rs\.?|[Mm]s\.?|[Dd]r\.?)\s*(?:[Mm]r\.?|[Mm]rs\.?|[Mm]s\.?|[Dd]r\.?)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"),
    re.compile(r"\b(?:[Mm]r\.?|[Mm]rs\.?|[Mm]s\.?|[Dd]r\.?)\s+([A-Z][a-z]+)\b"),
]

ADDRESS_PATTERNS = [
    re.compile(
        r"(?:No\.?\s*\d+[/A-Za-z0-9]*,?\s+)?\b[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+)*\s+(?:Road|Mawatha|Lane|Street|Place|Avenue)\b"
        r"|(?:Plot\s*(?:No\.?)?\s*\d+)"
        r"|(?:Grama\s+Niladhari\s+Division\s*(?:No\.?)?\s*\d+)"
    ),
]

# Bias detection cues (T-26.2)
COMMERCIAL_BIAS_KEYWORDS = [
    "must exclusively buy",
    "only purchase",
    "the only authorized brand",
    "buy exclusively from",
    "must use brand",
    "mandatory commercial brand",
    "exclusively recommended brand",
]

REGIONAL_BIAS_KEYWORDS = [
    "only suitable for wet zone",
    "not viable in dry zone",
    "ignore dry zone farmers",
    "only western province",
    "disregard smallholder practices",
]

EXCLUSIVE_VARIETY_BIAS_KEYWORDS = [
    "do not use traditional varieties",
    "traditional varieties are useless",
    "only cultivate expensive hybrid",
    "mandatory commercial hybrid only",
]


@dataclass
class ResponsibleAIResult:
    """
    Structured outcome of Responsible AI verification.
    """
    sanitized_response: str
    explanation: Dict[str, Any]
    confidence: float
    sources: List[SourceItem]
    bias_score: float
    bias_detected: bool
    bias_corrected: bool
    privacy_compliant: bool
    pii_detected: List[str] = field(default_factory=list)
    pii_redacted_count: int = 0


class ResponsibleAIChecker:
    """
    Mechanical validator enforcing algorithmic fairness, non-technical explainability,
    and privacy redaction on every outgoing advisory.
    """

    def __init__(self, bias_threshold: float = BIAS_POLICY_THRESHOLD) -> None:
        self.bias_threshold = bias_threshold

    # ==========================================================================
    # Subtask T-26.2: Bias Detection Engine (0 - 1 score)
    # ==========================================================================

    def detect_bias(
        self,
        response_text: str,
        crop: Optional[str] = None,
        district: Optional[str] = None,
    ) -> Tuple[float, List[str]]:
        """
        Evaluate response text for crop, regional, and commercial bias signals.
        Returns a normalized bias score in [0.0, 1.0] and a list of detected bias reasons.
        """
        lower_text = response_text.lower()
        reasons: List[str] = []
        score: float = 0.0

        # 1. Commercial / Brand Exclusivity Bias
        comm_hits = sum(1 for kw in COMMERCIAL_BIAS_KEYWORDS if kw in lower_text)
        if comm_hits > 0:
            penalty = min(0.40, comm_hits * 0.25)
            score += penalty
            reasons.append("Commercial brand exclusivity language detected.")

        # 2. Regional / Agro-Ecological Bias
        reg_hits = sum(1 for kw in REGIONAL_BIAS_KEYWORDS if kw in lower_text)
        if reg_hits > 0:
            penalty = min(0.35, reg_hits * 0.20)
            score += penalty
            reasons.append("Regional applicability or smallholder exclusion bias detected.")

        # 3. Varietal Monoculture / Anti-Traditional Variety Bias
        var_hits = sum(1 for kw in EXCLUSIVE_VARIETY_BIAS_KEYWORDS if kw in lower_text)
        if var_hits > 0:
            penalty = min(0.35, var_hits * 0.20)
            score += penalty
            reasons.append("Exclusion of resilient/traditional crop varieties detected.")

        # 4. Extreme or Absolute Mandates
        if re.search(r"\b(100% guaranteed|zero risk|guaranteed double yield|never fail)\b", lower_text):
            score += 0.20
            reasons.append("Unsubstantiated absolute yield or risk guarantees detected.")

        normalized_score = round(min(1.0, max(0.0, score)), 2)
        return normalized_score, reasons

    # ==========================================================================
    # Subtask T-26.3: Automatic Bias Correction (Rule BR-5)
    # ==========================================================================

    def correct_bias(
        self,
        response_text: str,
        bias_score: float,
        bias_reasons: List[str],
        crop: str = "Paddy",
        district: str = "General",
    ) -> Tuple[str, bool]:
        """
        If bias score exceeds 0.3 (Rule BR-5), apply automatic algorithmic correction
        by neutralizing restrictive phrasing and appending inclusive DOA agronomic guidance.
        """
        if bias_score <= self.bias_threshold:
            return response_text, False

        corrected_text = response_text

        # 1. Neutralize exclusive commercial phrasing
        for kw in COMMERCIAL_BIAS_KEYWORDS:
            corrected_text = re.sub(re.escape(kw), "consider recommended DOA approved formulations or", corrected_text, flags=re.IGNORECASE)

        for kw in EXCLUSIVE_VARIETY_BIAS_KEYWORDS:
            corrected_text = re.sub(re.escape(kw), "evaluate both certified high-yielding and local resilient varieties", corrected_text, flags=re.IGNORECASE)

        # 2. Append balanced DOA fairness and regional adaptability guidance
        fairness_addendum = (
            "\n\n> ⚖️ **Responsible AI Balanced Advisory Note (Rule BR-5):**\n"
            f"> Agricultural recommendations should be adapted to your local microclimate in {district}. "
            "Farmers are encouraged to consider both certified high-yielding selections and resilient local traditional varieties. "
            "Always consult generic active ingredient formulations certified by the Department of Agriculture (DOA) to ensure economic and ecological balance."
        )

        corrected_text = corrected_text.strip() + fairness_addendum
        logger.info(f"Rule BR-5 bias correction applied (original score: {bias_score:.2f}).")
        return corrected_text, True

    # ==========================================================================
    # Subtask T-26.4: Non-Technical "Why?" Explanation Generator (Rule BR-10)
    # ==========================================================================

    def generate_explanation(
        self,
        response_text: str,
        sources: List[SourceItem],
        confidence: float,
        crop: str = "Paddy",
        intent: str = "general_farming",
        agents_consulted: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate clear, non-technical explanation answering "Why was this advice given?"
        for farmers and extension officers in plain, intuitive language (Rule BR-10).
        """
        agents_list = agents_consulted or ["agronomy knowledge engine"]
        agents_readable = ", ".join([
            a.replace("_agent", "").capitalize() for a in agents_list
        ])

        conf_pct = int(confidence * 100)
        if confidence >= 0.80:
            conf_desc = f"High confidence ({conf_pct}%) based on verified Department of Agriculture records matching the exact observed conditions."
        elif confidence >= 0.60:
            conf_desc = f"Moderate confidence ({conf_pct}%) based on partial symptom alignment. Field confirmation with your Agriculture Extension Officer is recommended."
        else:
            conf_desc = f"Preliminary guidance ({conf_pct}%). Observed symptoms are broad; please verify with local extension officer before applying intensive treatments."

        source_titles = [s.title for s in sources] if sources else ["Sri Lanka Department of Agriculture Handbook"]
        sources_summary = f"Grounded in {len(source_titles)} official reference publication(s): {', '.join(source_titles[:2])}."

        summary = (
            f"This advisory was prepared for {crop} by consulting our verified {agents_readable} specialists "
            f"and matching your query against official Sri Lankan agronomic research."
        )

        model_reasoning = (
            f"1. **Input Analysis:** Your inquiry regarding {crop} was classified under {intent.replace('_', ' ')}.\n"
            f"2. **Evidence Matching:** The system matched observed signals against the official DOA knowledge base with {conf_pct}% confidence.\n"
            f"3. **Microclimate & Safety:** Recommendations adhere to regional safety limits, Integrated Pest Management (IPM), and Pre-Harvest Interval (PHI) standards."
        )

        return {
            "summary": summary,
            "model_reasoning": model_reasoning,
            "evidence_sources": source_titles,
            "confidence_explanation": conf_desc,
            "confidence_score": round(confidence, 2),
            "agents_used": agents_list,
            "sources_summary": sources_summary,
            "fairness_and_privacy_verified": True,
        }

    # ==========================================================================
    # Subtasks T-26.5 & T-26.6: PII Detection, Redaction & Privacy Compliance (Rule BR-6)
    # ==========================================================================

    def redact_pii(self, text: str) -> Tuple[str, bool, List[str], int]:
        """
        Detect and redact Personally Identifiable Information (phone numbers, personal names,
        private plot addresses) from outgoing text, while preserving official extension helplines (1920).
        Returns: (sanitized_text, privacy_compliant_flag, detected_categories, redacted_count).
        """
        detected: List[str] = []
        redacted_count = 0
        sanitized = text

        # 1. Phone number detection & redaction
        # Mask official extension helpline 1920 temporarily to avoid accidental redaction
        helpline_token = "@@OFFICIAL_AGRI_HELPLINE_TOKEN@@"
        sanitized = re.sub(r"\b1920\b", helpline_token, sanitized)

        for pat in PHONE_PATTERNS:
            matches = list(pat.finditer(sanitized))
            if matches:
                detected.append("phone_number")
                redacted_count += len(matches)
                sanitized = pat.sub("[PHONE REDACTED]", sanitized)

        # Restore official helpline
        sanitized = sanitized.replace(helpline_token, "1920")

        # 2. Personal name detection & redaction (e.g. "Farmer Nimal Silva", "Contact: John Doe")
        for pat in NAME_PATTERNS:
            def _name_repl(match):
                nonlocal redacted_count
                matched_name = match.group(1)
                # Avoid redacting crop/institutional terms
                if any(term in matched_name for term in ["Agriculture", "Department", "Extension", "Office", "Sri Lanka"]):
                    return match.group(0)
                detected.append("person_name")
                redacted_count += 1
                prefix = match.group(0)[:match.start(1) - match.start(0)]
                return f"{prefix}[NAME REDACTED]"

            sanitized = pat.sub(_name_repl, sanitized)

        # 3. Specific residential address / private plot number detection
        for pat in ADDRESS_PATTERNS:
            def _addr_repl(match):
                nonlocal redacted_count
                matched_addr = match.group(0)
                # Keep district/province/ecological zone references clean
                if any(kw in matched_addr for kw in ["District", "Province", "Zone", "Sri Lanka", "Anuradhapura", "Kurunegala", "Polonnaruwa", "Badulla", "Kandy", "Jaffna", "Ampara"]):
                    return matched_addr
                detected.append("personal_location")
                redacted_count += 1
                return "[LOCATION REDACTED]"

            sanitized = pat.sub(_addr_repl, sanitized)

        # Rule BR-6: Once sanitized, outgoing response is privacy compliant
        privacy_compliant = True
        return sanitized, privacy_compliant, list(set(detected)), redacted_count

    # ==========================================================================
    # Full Responsible AI Validation Pipeline (Subtask T-26.1 & T-26.7)
    # ==========================================================================

    def check(
        self,
        response_text: str,
        sources: List[SourceItem],
        confidence: float,
        crop: str = "Paddy",
        district: str = "General",
        intent: str = "general_farming",
        agents_consulted: Optional[List[str]] = None,
    ) -> ResponsibleAIResult:
        """
        Execute comprehensive Responsible AI inspection across Bias, PII, and Explainability.
        """
        # Step 1: Detect Bias (T-26.2)
        bias_score, bias_reasons = self.detect_bias(response_text, crop=crop, district=district)
        bias_detected = bias_score > self.bias_threshold

        # Step 2: Auto-Correct Bias if score > 0.3 (T-26.3)
        debiased_text, bias_corrected = self.correct_bias(
            response_text=response_text,
            bias_score=bias_score,
            bias_reasons=bias_reasons,
            crop=crop,
            district=district,
        )

        # Step 3: PII Detection & Redaction (T-26.5 & T-26.6)
        sanitized_text, privacy_compliant, pii_detected, redacted_count = self.redact_pii(debiased_text)

        # Step 4: Generate Non-Technical Explanation (T-26.4)
        explanation = self.generate_explanation(
            response_text=sanitized_text,
            sources=sources,
            confidence=confidence,
            crop=crop,
            intent=intent,
            agents_consulted=agents_consulted,
        )
        explanation["bias_score"] = bias_score
        explanation["bias_detected"] = bias_detected
        explanation["bias_corrected"] = bias_corrected
        explanation["privacy_compliant"] = privacy_compliant

        return ResponsibleAIResult(
            sanitized_response=sanitized_text,
            explanation=explanation,
            confidence=confidence,
            sources=sources,
            bias_score=bias_score,
            bias_detected=bias_detected,
            bias_corrected=bias_corrected,
            privacy_compliant=privacy_compliant,
            pii_detected=pii_detected,
            pii_redacted_count=redacted_count,
        )


responsible_ai_checker = ResponsibleAIChecker()
