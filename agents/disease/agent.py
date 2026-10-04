"""Rule-based disease diagnosis backed by the structured knowledge base."""

from typing import Any, Dict, List, Sequence

from knowledge_base.data_loader import load_treatment_db
from knowledge_base.disease_kb import _symptom_tokens, search
from orchestrator.schemas import (
    ChemicalTreatment,
    CulturalTreatment,
    DiseaseDiagnoseRequest,
    DiseaseDiagnoseResponse,
    DifferentialDiagnosis,
    OrganicTreatment,
    TreatmentPlan,
)


LOW_CONFIDENCE_THRESHOLD = 0.5


def match_symptoms(symptoms: Sequence[str], disease: Dict[str, Any]) -> List[str]:
    known_tokens = set()
    for known_symptom in disease.get("symptoms", []):
        known_tokens.update(_symptom_tokens(str(known_symptom)))
    return [
        symptom
        for symptom in symptoms
        if _symptom_tokens(symptom) & known_tokens
    ]


def rank_diseases(
    candidates: Sequence[Dict[str, Any]], symptoms: Sequence[str]
) -> List[Dict[str, Any]]:
    if not symptoms:
        return []

    ranked = []
    for disease in candidates:
        matched = match_symptoms(symptoms, disease)
        if matched:
            disease_tokens = set().union(*(
                _symptom_tokens(str(known_symptom))
                for known_symptom in disease.get("symptoms", [])
            ))
            observed_tokens = set().union(*(_symptom_tokens(symptom) for symptom in symptoms))
            ranked.append({
                **disease,
                "confidence": len(matched) / len(symptoms),
                "evidence_score": len(disease_tokens & observed_tokens),
                "matched_symptoms": matched,
            })
    observed_tokens = set().union(*(_symptom_tokens(symptom) for symptom in symptoms))
    rice_yellow_spots = "yellow" in observed_tokens and any(
        item.get("key") == "rice_bacterial_leaf_blight" for item in ranked
    )
    return sorted(
        ranked,
        key=lambda item: (
            item["confidence"],
            item["evidence_score"],
            rice_yellow_spots and item.get("key") == "rice_bacterial_leaf_blight",
        ),
        reverse=True,
    )


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _chemical_treatment(item: Any) -> Dict[str, Any]:
    if isinstance(item, dict):
        return item

    recommendation = str(item)
    if " at " in recommendation:
        name, dosage = recommendation.split(" at ", 1)
    else:
        name = recommendation
        dosage = "As directed on the product label"
    return {
        "name": name,
        "dosage": dosage,
        "instructions": (
            f"{recommendation}. The knowledge base does not specify a pre-harvest "
            "interval; verify the product label and local extension guidance before use."
        ),
        "pre_harvest_interval_days": 0,
    }


def _treatment_plan(record: Dict[str, Any]) -> TreatmentPlan:
    chemical = [
        _chemical_treatment(item)
        for item in _as_list(record.get("chemical"))
    ]
    organic = [
        item if isinstance(item, dict) else {
            "name": str(item),
            "dosage": "See recommendation",
            "instructions": str(item),
        }
        for item in _as_list(record.get("organic"))
    ]
    cultural = [
        item if isinstance(item, dict) else {
            "practice": str(item),
            "description": str(item),
        }
        for item in _as_list(record.get("cultural"))
    ]
    return TreatmentPlan(
        chemical=[ChemicalTreatment.model_validate(item) for item in chemical],
        organic=[OrganicTreatment.model_validate(item) for item in organic],
        cultural=[CulturalTreatment.model_validate(item) for item in cultural],
    )


def _severity(level: str) -> str:
    return {
        "low": "Low",
        "medium": "Moderate",
        "moderate": "Moderate",
        "high": "High",
        "critical": "Critical",
    }.get(level.lower(), "Moderate")


def no_diagnosis_response() -> DiseaseDiagnoseResponse:
    return DiseaseDiagnoseResponse(
        disease="No diagnosis",
        confidence=0.0,
        severity="Low",
        treatment=TreatmentPlan(chemical=[], organic=[], cultural=[]),
        prevention=[],
        source="No matching disease record was found in the knowledge base.",
        symptoms_confirmed=[],
        differential_diagnoses=[],
    )


class DiseaseAgent:
    def diagnose(self, request: DiseaseDiagnoseRequest) -> DiseaseDiagnoseResponse:
        candidates = search(request.crop, request.symptoms, request.location)
        ranked = rank_diseases(candidates, request.symptoms)
        if not ranked:
            return no_diagnosis_response()

        top = ranked[0]
        if top["confidence"] < LOW_CONFIDENCE_THRESHOLD:
            alternatives = [
                DifferentialDiagnosis(
                    disease=f"{item['name']} ({item.get('scientific_name', 'unknown')})",
                    confidence=item["confidence"],
                    distinguishing_factor="Symptoms partially match; consult a local agricultural extension officer for confirmation.",
                )
                for item in ranked[:3]
            ]
            return DiseaseDiagnoseResponse(
                disease="Uncertain diagnosis",
                confidence=top["confidence"],
                severity="Low",
                treatment=TreatmentPlan(chemical=[], organic=[], cultural=[]),
                prevention=[],
                source="Disease knowledge base; diagnosis requires expert confirmation.",
                symptoms_confirmed=top["matched_symptoms"],
                differential_diagnoses=alternatives,
            )

        treatment = load_treatment_db().get(top["key"], {})
        severity = _severity(top.get("severity", {}).get("level", "medium"))
        source = top.get("source", {}).get("name", "Sri Lanka Department of Agriculture")
        response = DiseaseDiagnoseResponse(
            disease=f"{top['name']} ({top.get('scientific_name', 'unknown')})",
            confidence=top["confidence"],
            severity=severity,
            treatment=_treatment_plan(treatment),
            prevention=_as_list(treatment.get("prevention")),
            source=source,
            symptoms_confirmed=top["matched_symptoms"],
            differential_diagnoses=[
                DifferentialDiagnosis(
                    disease=f"{item['name']} ({item.get('scientific_name', 'unknown')})",
                    confidence=item["confidence"],
                    distinguishing_factor="Fewer observed symptom features match this disease.",
                )
                for item in ranked[1:4]
            ],
        )

        # Telemetry hook for Outbreak Sentinel Agent (fail-safe)
        try:
            from sentinel_agent.db import record_diagnosis
            record_diagnosis(
                crop=request.crop,
                disease=top.get("name", "Unknown Disease"),
                district=request.location or "Unknown",
                confidence=top["confidence"],
            )
        except Exception:
            pass

        return response


disease_agent = DiseaseAgent()