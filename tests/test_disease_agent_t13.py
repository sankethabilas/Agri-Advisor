import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents.disease.agent import DiseaseAgent, match_symptoms, rank_diseases
from knowledge_base.disease_kb import search
from orchestrator.main import app
from orchestrator.schemas import DiseaseDiagnoseRequest


client = TestClient(app)


def request(crop, symptoms, district="Anuradhapura"):
    return DiseaseDiagnoseRequest(
        crop=crop,
        symptoms=symptoms,
        location={"district": district},
    )


def test_rice_yellow_spots_diagnose_as_bacterial_leaf_blight():
    result = DiseaseAgent().diagnose(request("rice", ["yellow spots on leaves"]))
    assert result.disease.startswith("Bacterial Leaf Blight")
    assert 0.0 <= result.confidence <= 1.0
    assert result.severity == "High"


def test_tomato_dark_spots_and_rings_diagnose_as_early_blight():
    result = DiseaseAgent().diagnose(
        request("tomato", ["dark spots with concentric rings"])
    )
    assert result.disease.startswith("Tomato Early Blight")
    assert result.confidence == 1.0
    assert result.severity == "Moderate"
    assert all(
        "does not specify a pre-harvest interval" in treatment.instructions
        for treatment in result.treatment.chemical
    )


def test_unmatched_symptoms_return_no_diagnosis():
    result = DiseaseAgent().diagnose(request("tomato", ["crystalline blue feathers"]))
    assert result.disease == "No diagnosis"
    assert result.confidence == 0.0
    assert result.symptoms_confirmed == []


def test_crop_mismatch_returns_no_diagnosis():
    result = DiseaseAgent().diagnose(request("lettuce", ["dark patches with concentric rings"]))
    assert result.disease == "No diagnosis"


def test_empty_search_symptoms_returns_no_candidates():
    assert search("rice", [], {"district": "Anuradhapura"}) == []


def test_search_excludes_records_outside_requested_location(monkeypatch):
    monkeypatch.setattr(
        "knowledge_base.disease_kb.load_disease_kb",
        lambda: {
            "local_disease": {
                "crop": "rice",
                "symptoms": ["yellowing leaves"],
                "region": ["Badulla"],
            }
        },
    )
    assert search("rice", ["yellowing leaves"], {"district": "Matale"}) == []


def test_paddy_alias_finds_rice_records():
    candidates = search("Paddy", ["yellowing leaves"], {"district": "Anuradhapura"})
    assert candidates
    assert all(candidate["crop"] == "rice" for candidate in candidates)


def test_distinct_tomato_late_blight_symptoms_are_ranked():
    result = DiseaseAgent().diagnose(
        request("tomato", ["water-soaked grey-green spots", "white growth under leaves"])
    )
    assert result.disease.startswith("Tomato Late Blight")


def test_low_confidence_returns_alternatives_and_consultation_guidance():
    result = DiseaseAgent().diagnose(
        request(
            "rice",
            ["yellowing leaves", "purple veins", "silver roots", "blue crystals", "white flowers"],
        )
    )
    assert result.disease == "Uncertain diagnosis"
    assert result.differential_diagnoses
    assert all("consult" in item.distinguishing_factor.lower() for item in result.differential_diagnoses)


def test_matched_symptoms_preserve_farmer_wording():
    candidates = search(
        "tomato",
        ["dark spots with concentric rings"],
        {"district": "Anuradhapura"},
    )
    ranked = rank_diseases(candidates, ["dark spots with concentric rings"])
    assert match_symptoms(["dark spots with concentric rings"], ranked[0]) == [
        "dark spots with concentric rings"
    ]


def test_disease_diagnose_endpoint_returns_documented_rice_response():
    fixture = Path(__file__).parent / "fixtures" / "disease_diagnose_request.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    response = client.post("/api/disease/diagnose", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert set(body["treatment"]) == {"chemical", "organic", "cultural"}
    assert body["prevention"]
    assert body["source"]
    assert body["symptoms_confirmed"]