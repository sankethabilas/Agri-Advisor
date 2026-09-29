"""
Tests for Responsible AI Checker: Bias, PII, and Explanation (Task T-26).
Validates Subtasks T-26.1 through T-26.8 & Completion Criteria:
- T-26.1: ResponsibleAIChecker takes response, sources, and confidence
- T-26.2: Bias detection producing 0-1 score across crop, region, and commercial coverage
- T-26.3: Automatic correction when bias score > 0.3 (Rule BR-5)
- T-26.4: Explanation generation in simple non-technical language (Rule BR-10)
- T-26.5: PII detection covering phone numbers, names, and personal locations
- T-26.6: PII redaction and privacy_compliant flag setting (Rule BR-6)
- T-26.7: Insertion into response path immediately before formatting
- T-26.8: Test with deliberately biased response and response containing phone number
"""

import pytest
from starlette.testclient import TestClient

from orchestrator.main import app
from orchestrator.responsible_ai import (
    BIAS_POLICY_THRESHOLD,
    ResponsibleAIChecker,
    responsible_ai_checker,
)
from orchestrator.schemas import (
    Location,
    OrchestratorProcessRequest,
    SourceItem,
)
from orchestrator.security import create_access_token
from orchestrator.session_context import session_manager

client = TestClient(app)


def auth_headers(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


@pytest.fixture(autouse=True)
def clean_sessions():
    session_manager._sessions_by_user.clear()
    session_manager._sessions_by_id.clear()
    yield


# ==============================================================================
# T-26.1: ResponsibleAIChecker Initialization & Basic Operation
# ==============================================================================

def test_t26_1_checker_initialization_and_contract():
    """Verify ResponsibleAIChecker initializes and returns structured outcome."""
    checker = ResponsibleAIChecker()
    sources = [
        SourceItem(
            title="Rice Cultivation Guidelines",
            author_organization="Sri Lanka Department of Agriculture",
            document_id="DOA-RC-01",
            section="Agronomy",
            confidence_score=0.92,
        )
    ]
    raw_response = "Apply 30 kg/acre Urea at 14 days after sowing. Follow standard weeding."
    
    result = checker.check(
        response_text=raw_response,
        sources=sources,
        confidence=0.92,
        crop="Paddy",
        district="Kurunegala",
    )

    assert result.sanitized_response is not None
    assert result.confidence == 0.92
    assert len(result.sources) == 1
    assert 0.0 <= result.bias_score <= 1.0
    assert isinstance(result.privacy_compliant, bool)
    assert isinstance(result.explanation, dict)
    assert "summary" in result.explanation
    assert "model_reasoning" in result.explanation


# ==============================================================================
# T-26.2: Bias Detection Scoring (0 - 1 Score)
# ==============================================================================

def test_t26_2_bias_detection_scoring():
    """Verify bias detection produces 0-1 scores across commercial, regional, and varietal bias."""
    checker = ResponsibleAIChecker()

    # Unbiased standard advice -> 0.0
    unbiased_text = "Apply recommended compost and DOA certified seed paddy for optimal yield in Kurunegala."
    score_unbiased, reasons_unbiased = checker.detect_bias(unbiased_text)
    assert score_unbiased == 0.0
    assert len(reasons_unbiased) == 0

    # Commercial brand exclusivity bias
    commercial_biased_text = "Farmers must exclusively buy ChemMax Brand Super Fungicide. Only purchase this product."
    score_comm, reasons_comm = checker.detect_bias(commercial_biased_text)
    assert score_comm > 0.30
    assert any("commercial" in r.lower() for r in reasons_comm)

    # Regional / smallholder exclusion bias
    regional_biased_text = "This method is only suitable for wet zone and we ignore dry zone farmers in Anuradhapura."
    score_reg, reasons_reg = checker.detect_bias(regional_biased_text)
    assert score_reg > 0.0
    assert any("regional" in r.lower() for r in reasons_reg)

    # Combined heavy bias
    heavy_biased_text = (
        "You must exclusively buy ABC Agrochem. Traditional varieties are useless, only cultivate expensive hybrid. "
        "100% guaranteed zero risk crop failure."
    )
    score_heavy, reasons_heavy = checker.detect_bias(heavy_biased_text)
    assert score_heavy >= 0.50
    assert len(reasons_heavy) >= 2


# ==============================================================================
# T-26.3: Automatic Bias Correction (Rule BR-5, Threshold > 0.3)
# ==============================================================================

def test_t26_3_automatic_bias_correction_when_score_exceeds_threshold():
    """
    Rule BR-5: When bias score exceeds 0.3, the system must automatically correct
    the response, neutralizing restrictive phrasing and appending balanced guidance.
    """
    checker = ResponsibleAIChecker()
    biased_text = (
        "You must exclusively buy AgroCorp Chemical Spray. "
        "Traditional varieties are useless and should never be planted."
    )
    score, reasons = checker.detect_bias(biased_text)
    assert score > BIAS_POLICY_THRESHOLD  # > 0.30

    corrected_text, was_corrected = checker.correct_bias(
        response_text=biased_text,
        bias_score=score,
        bias_reasons=reasons,
        crop="Paddy",
        district="Polonnaruwa",
    )

    assert was_corrected is True
    assert "exclusively buy" not in corrected_text
    assert "traditional varieties are useless" not in corrected_text
    assert "Responsible AI Balanced Advisory Note (Rule BR-5)" in corrected_text
    assert "Polonnaruwa" in corrected_text


def test_t26_3_unbiased_response_remains_unaltered():
    """Verify neutral responses (score <= 0.3) are not altered."""
    checker = ResponsibleAIChecker()
    clean_text = "Maintain 2-3 cm standing water during the tillering stage in Anuradhapura."
    score, reasons = checker.detect_bias(clean_text)
    assert score <= 0.30

    corrected_text, was_corrected = checker.correct_bias(
        response_text=clean_text,
        bias_score=score,
        bias_reasons=reasons,
        crop="Paddy",
        district="Anuradhapura",
    )
    assert was_corrected is False
    assert corrected_text == clean_text


# ==============================================================================
# T-26.4: Non-Technical "Why?" Explanation Generator (Rule BR-10)
# ==============================================================================

def test_t26_4_explanation_generation_in_simple_language():
    """
    Rule BR-10: Explanation must explain why advice was selected in simple, non-technical language.
    """
    checker = ResponsibleAIChecker()
    sources = [
        SourceItem(
            title="Rice Blast Disease Control Guide",
            author_organization="Department of Agriculture Sri Lanka",
            document_id="DOA-DIS-01",
            section="Pathology",
            confidence_score=0.92,
        )
    ]
    expl = checker.generate_explanation(
        response_text="Apply recommended fungicide for blast.",
        sources=sources,
        confidence=0.92,
        crop="Paddy",
        intent="disease_diagnosis",
        agents_consulted=["disease_agent", "weather_agent", "rag_agent"],
    )

    assert "summary" in expl
    assert "Paddy" in expl["summary"]
    assert "model_reasoning" in expl
    assert "confidence_explanation" in expl
    assert "92%" in expl["confidence_explanation"]
    assert "High confidence" in expl["confidence_explanation"]
    assert "evidence_sources" in expl
    assert "Rice Blast Disease Control Guide" in expl["evidence_sources"]
    assert expl["fairness_and_privacy_verified"] is True


# ==============================================================================
# T-26.5 & T-26.6: PII Detection, Redaction, and Privacy Compliance (Rule BR-6)
# ==============================================================================

def test_t26_5_and_t26_6_pii_detection_and_redaction():
    """
    Rule BR-6: Phone numbers, personal names, and private plot addresses must be redacted
    while preserving official government helplines (1920).
    """
    checker = ResponsibleAIChecker()

    text_with_pii = (
        "For personalized assistance, contact Farmer Nimal Bandara at 077-1234567 or +94718889999. "
        "Plot located at No. 45 Temple Road, Kurunegala. "
        "You can also call the official Agriculture Extension Office: 1920."
    )

    sanitized, compliant, detected_types, count = checker.redact_pii(text_with_pii)

    assert compliant is True
    assert count >= 3
    assert "phone_number" in detected_types
    assert "person_name" in detected_types

    # Ensure personal phone numbers are redacted
    assert "077-1234567" not in sanitized
    assert "+94718889999" not in sanitized
    assert "[PHONE REDACTED]" in sanitized

    # Ensure personal name is redacted
    assert "Nimal Bandara" not in sanitized
    assert "[NAME REDACTED]" in sanitized

    # Ensure official government helpline 1920 is preserved intact
    assert "1920" in sanitized
    assert "Agriculture Extension" in sanitized


# ==============================================================================
# T-26.7 & T-26.8: End-to-End Testing with Biased & PII-Laden Queries
# ==============================================================================

def test_t26_8_completion_criteria_deliberate_bias_and_pii_redaction():
    """
    Completion criteria verification:
    1. A response with a bias score above 0.3 is measurably altered.
    2. A response containing a phone number is delivered redacted.
    3. The 'Why?' control returns a readable explanation.
    """
    checker = ResponsibleAIChecker()

    # Create deliberately biased text containing a personal phone number
    problematic_text = (
        "For immediate treatment, you must exclusively buy AgroMax Gold. "
        "Traditional varieties are useless in Kurunegala. "
        "Contact field officer Mr. Sunimal Fernando directly at 071-9876543 for special discounts. "
        "Official helpline: 1920."
    )

    sources = [
        SourceItem(
            title="Sri Lanka Rice Pathology Guide",
            author_organization="Department of Agriculture",
            document_id="DOA-PATH-01",
            section="Crop Protection",
            confidence_score=0.88,
        )
    ]

    result = checker.check(
        response_text=problematic_text,
        sources=sources,
        confidence=0.88,
        crop="Paddy",
        district="Kurunegala",
        intent="disease_diagnosis",
        agents_consulted=["disease_agent", "rag_agent"],
    )

    # 1. Bias > 0.3 is measurably altered
    assert result.bias_detected is True
    assert result.bias_score > 0.30
    assert result.bias_corrected is True
    assert result.sanitized_response != problematic_text
    assert "Responsible AI Balanced Advisory Note (Rule BR-5)" in result.sanitized_response

    # 2. Phone number is delivered redacted
    assert "071-9876543" not in result.sanitized_response
    assert "[PHONE REDACTED]" in result.sanitized_response
    assert "Sunimal Fernando" not in result.sanitized_response
    assert "[NAME REDACTED]" in result.sanitized_response
    assert "1920" in result.sanitized_response
    assert result.privacy_compliant is True

    # 3. 'Why?' explanation returns readable non-technical reasoning
    expl = result.explanation
    assert len(expl["summary"]) > 20
    assert "Paddy" in expl["summary"]
    assert "model_reasoning" in expl
    assert expl["confidence_score"] == 0.88
    assert expl["bias_score"] == result.bias_score
    assert expl["privacy_compliant"] is True


def test_t26_8_full_process_endpoint_rai_integration():
    """Verify live HTTP POST /api/orchestrator/process executes Responsible AI on real responses."""
    user_id = "farmer-rai-test"
    payload = {
        "query": "My paddy crops have yellowing leaf spots in Kurunegala",
        "user_id": user_id,
        "location": {"district": "Kurunegala", "agro_ecological_zone": "IL1a"},
        "crop_context": "Paddy",
        "language": "en",
    }
    resp = client.post("/api/orchestrator/process", json=payload, headers=auth_headers(user_id))
    assert resp.status_code == 200
    data = resp.json()

    # Verify why_explanation structure populated by ResponsibleAIChecker
    why = data["why_explanation"]
    assert why is not None
    assert "summary" in why
    assert "model_reasoning" in why
    assert "evidence_sources" in why
    assert "confidence_explanation" in why
    assert why.get("fairness_and_privacy_verified") is True
    assert "bias_score" in why
    assert "privacy_compliant" in why
    assert why["privacy_compliant"] is True
