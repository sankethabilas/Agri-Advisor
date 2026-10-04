from types import SimpleNamespace

import pytest

import agents.disease.agent as disease_module
from agents.disease.agent import (
    DiseaseAgent,
    LOW_CONFIDENCE_THRESHOLD,
    match_symptoms,
    no_diagnosis_response,
    rank_diseases,
)


# ============================================================
# T-27.4.1
# Symptom matching
# ============================================================

def test_match_symptoms_returns_matching_symptoms():

    disease = {
        "name": "Test Disease",
        "symptoms": [
            "yellow leaves",
            "brown lesions",
        ],
    }

    observed = [
        "yellow leaves",
        "healthy roots",
    ]

    matched = match_symptoms(
        observed,
        disease,
    )

    assert "yellow leaves" in matched

    assert "healthy roots" not in matched


# ============================================================
# T-27.4.2
# Ranking prefers higher symptom confidence
# ============================================================

def test_rank_diseases_prefers_higher_confidence():

    candidates = [
        {
            "key": "disease_a",
            "name": "Disease A",
            "symptoms": [
                "yellow leaves",
            ],
        },
        {
            "key": "disease_b",
            "name": "Disease B",
            "symptoms": [
                "yellow leaves",
                "brown lesions",
            ],
        },
    ]

    symptoms = [
        "yellow leaves",
        "brown lesions",
    ]

    ranked = rank_diseases(
        candidates,
        symptoms,
    )

    assert len(ranked) == 2

    assert (
        ranked[0]["key"]
        == "disease_b"
    )

    assert (
        ranked[0]["confidence"]
        > ranked[1]["confidence"]
    )


# ============================================================
# T-27.4.3
# Ranking confidence calculation
# ============================================================

def test_rank_diseases_calculates_confidence():

    candidates = [
        {
            "key": "test_disease",
            "name": "Test Disease",
            "symptoms": [
                "yellow leaves",
            ],
        }
    ]

    symptoms = [
        "yellow leaves",
        "purple roots",
    ]

    ranked = rank_diseases(
        candidates,
        symptoms,
    )

    assert len(ranked) == 1

    assert (
        ranked[0]["confidence"]
        == pytest.approx(0.5)
    )


# ============================================================
# T-27.4.4
# Tie case
# ============================================================

def test_rank_diseases_handles_tie_stably():

    candidates = [
        {
            "key": "disease_first",
            "name": "Disease First",
            "symptoms": [
                "brown spots",
            ],
        },
        {
            "key": "disease_second",
            "name": "Disease Second",
            "symptoms": [
                "brown spots",
            ],
        },
    ]

    symptoms = [
        "brown spots",
    ]

    ranked = rank_diseases(
        candidates,
        symptoms,
    )

    assert len(ranked) == 2

    assert (
        ranked[0]["confidence"]
        == ranked[1]["confidence"]
    )

    assert (
        ranked[0]["evidence_score"]
        == ranked[1]["evidence_score"]
    )

    # Python sorting is stable, so an exact tie
    # preserves the original candidate order.
    assert (
        ranked[0]["key"]
        == "disease_first"
    )

    assert (
        ranked[1]["key"]
        == "disease_second"
    )


# ============================================================
# T-27.4.5
# Special rice yellow-spots tie-breaking rule
# ============================================================

def test_rank_diseases_prioritizes_bacterial_leaf_blight_for_rice_yellow_spots():

    candidates = [
        {
            "key": "other_rice_disease",
            "name": "Other Rice Disease",
            "symptoms": [
                "yellow spots",
            ],
        },
        {
            "key": "rice_bacterial_leaf_blight",
            "name": "Bacterial Leaf Blight",
            "symptoms": [
                "yellow spots",
            ],
        },
    ]

    symptoms = [
        "yellow spots",
    ]

    ranked = rank_diseases(
        candidates,
        symptoms,
    )

    assert (
        ranked[0]["key"]
        == "rice_bacterial_leaf_blight"
    )


# ============================================================
# T-27.4.6
# No symptoms
# ============================================================

def test_rank_diseases_returns_empty_when_no_symptoms():

    candidates = [
        {
            "key": "test_disease",
            "name": "Test Disease",
            "symptoms": [
                "yellow leaves",
            ],
        }
    ]

    ranked = rank_diseases(
        candidates,
        [],
    )

    assert ranked == []


# ============================================================
# T-27.5.1
# BR-7 no-diagnosis response
# ============================================================

def test_no_diagnosis_response_is_safe():

    response = no_diagnosis_response()

    assert (
        response.disease
        == "No diagnosis"
    )

    assert response.confidence == 0.0

    assert response.severity == "Low"

    assert (
        response.symptoms_confirmed
        == []
    )

    assert (
        response.differential_diagnoses
        == []
    )

    assert (
        response.treatment.chemical
        == []
    )

    assert (
        response.treatment.organic
        == []
    )

    assert (
        response.treatment.cultural
        == []
    )


# ============================================================
# T-27.5.2
# Zero-candidate diagnosis path
# ============================================================

def test_diagnose_returns_no_diagnosis_when_no_candidates(
    monkeypatch
):

    agent = DiseaseAgent()

    monkeypatch.setattr(
        disease_module,
        "search",
        lambda crop, symptoms, location: [],
    )

    request = SimpleNamespace(
        crop="rice",
        symptoms=[
            "completely unknown symptom"
        ],
        location="Anuradhapura",
    )

    response = agent.diagnose(
        request
    )

    assert (
        response.disease
        == "No diagnosis"
    )

    assert response.confidence == 0.0

    assert (
        response.treatment.chemical
        == []
    )

    assert (
        response.differential_diagnoses
        == []
    )


# ============================================================
# T-27.5.3
# BR-8 low-confidence diagnosis
# ============================================================

def test_low_confidence_returns_uncertain_diagnosis(
    monkeypatch
):

    agent = DiseaseAgent()

    candidates = [
        {
            "key": "test_disease",
            "name": "Test Disease",
            "scientific_name":
                "Testus diseaseus",
            "symptoms": [
                "yellow leaves",
            ],
            "severity": {
                "level": "medium"
            },
        }
    ]

    monkeypatch.setattr(
        disease_module,
        "search",
        lambda crop, symptoms, location:
            candidates,
    )

    request = SimpleNamespace(
        crop="rice",
        symptoms=[
            "yellow leaves",
            "purple roots",
            "white powder",
        ],
        location="Anuradhapura",
    )

    response = agent.diagnose(
        request
    )

    assert (
        response.confidence
        < LOW_CONFIDENCE_THRESHOLD
    )

    assert (
        response.disease
        == "Uncertain diagnosis"
    )

    assert response.severity == "Low"

    # Safety requirement:
    # do not recommend treatments when
    # diagnosis confidence is too low.
    assert (
        response.treatment.chemical
        == []
    )

    assert (
        response.treatment.organic
        == []
    )

    assert (
        response.treatment.cultural
        == []
    )

    assert (
        len(
            response.differential_diagnoses
        )
        >= 1
    )


# ============================================================
# T-27.5.4
# Low-confidence alternatives contain consultation advice
# ============================================================

def test_low_confidence_recommends_expert_confirmation(
    monkeypatch
):

    agent = DiseaseAgent()

    candidates = [
        {
            "key": "candidate_one",
            "name": "Candidate One",
            "scientific_name":
                "Candidateus one",
            "symptoms": [
                "yellow leaves",
            ],
        }
    ]

    monkeypatch.setattr(
        disease_module,
        "search",
        lambda crop, symptoms, location:
            candidates,
    )

    request = SimpleNamespace(
        crop="rice",
        symptoms=[
            "yellow leaves",
            "purple roots",
            "white powder",
        ],
        location="Anuradhapura",
    )

    response = agent.diagnose(
        request
    )

    assert (
        response.disease
        == "Uncertain diagnosis"
    )

    assert (
        len(
            response.differential_diagnoses
        )
        > 0
    )

    guidance = (
        response
        .differential_diagnoses[0]
        .distinguishing_factor
        .lower()
    )

    assert "consult" in guidance

    assert (
        "extension officer"
        in guidance
    )