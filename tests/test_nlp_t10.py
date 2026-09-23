"""
Tests for Agri-Advisor NLP Layer (Task T-10).
Validates Intent Classification, Named Entity Recognition (NER), Vocabulary Coverage,
and benchmark accuracy on the 60+ labelled farmer queries dataset.
"""

import json
from pathlib import Path
import pytest

from orchestrator.nlp import (
    CROP_VOCABULARY,
    DISTRICTS,
    EntityExtractor,
    IntentClassifier,
    NLPAnalyzer,
    SYMPTOM_PHRASES,
    analyze_query,
    handle_general_query,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def nlp():
    return NLPAnalyzer()


# ============================================================================
# T-10 Completion Criteria Verification
# ============================================================================

def test_t10_completion_criteria(nlp):
    """
    Completion criteria: "My rice has yellow spots on the leaves" returns:
    - intent: disease_diagnosis
    - crop: Paddy (or rice)
    - symptoms: contains 'yellow spots'
    """
    query = "My rice has yellow spots on the leaves"
    result = nlp.analyze_query(query)

    assert result.intent == "disease_diagnosis", f"Expected disease_diagnosis, got {result.intent}"
    assert result.entities.crop == "Paddy", f"Expected crop 'Paddy', got {result.entities.crop}"
    assert any("yellow spots" in s for s in result.entities.symptoms), (
        f"Expected 'yellow spots' in symptoms, got {result.entities.symptoms}"
    )
    assert result.confidence >= 0.70, f"Confidence too low: {result.confidence}"


# ============================================================================
# T-10.3 & T-10.4: Entity Extraction Tests
# ============================================================================

def test_crop_extraction():
    extractor = EntityExtractor()
    assert extractor.extract_crop("Can I plant tomato in Matale?") == "Tomato"
    assert extractor.extract_crop("Rice crop is turning yellow") == "Paddy"
    assert extractor.extract_crop("Harvesting green gram in dry zone") == "Mung Bean"
    assert extractor.extract_crop("How to grow chilli under irrigation") == "Chilli"
    assert extractor.extract_crop("Maize varieties for Maha season") == "Maize"
    assert extractor.extract_crop("Best fertilizer for tea plantations") == "Tea"


def test_symptom_extraction():
    extractor = EntityExtractor()
    symptoms = extractor.extract_symptoms("Tomato leaves have dark brown spots and severe wilting")
    assert "brown spots" in symptoms
    assert "wilting" in symptoms

    symptoms_paddy = extractor.extract_symptoms("Bacterial blight and root rot observed in paddy")
    assert any("blight" in s for s in symptoms_paddy)
    assert "root rot" in symptoms_paddy


def test_location_and_district_extraction():
    extractor = EntityExtractor()
    loc, district, region = extractor.extract_location("Will it rain tomorrow in Anuradhapura dry zone?")
    assert district == "Anuradhapura"
    assert region == "Dry Zone"

    loc_kandy, district_kandy, _ = extractor.extract_location("Heavy thunderstorm expected in Kandy")
    assert district_kandy == "Kandy"


def test_season_and_stage_extraction():
    extractor = EntityExtractor()
    assert extractor.extract_season("Fertilizer plan for Maha season") == "Maha"
    assert extractor.extract_season("Yala cultivation guidelines") == "Yala"

    assert extractor.extract_growth_stage("Water management during tillering stage") == "Tillering"
    assert extractor.extract_growth_stage("Paddy flowering and panicle initiation") == "Panicle Initiation"


# ============================================================================
# T-10.6: General Query Fallback Handler
# ============================================================================

def test_handle_general_query():
    query = "How do I contact the local agriculture officer?"
    result = analyze_query(query)
    fallback = handle_general_query(query, result)

    assert fallback["intent"] == "general_query"
    assert "1920" in fallback["helpline"]
    assert len(fallback["suggested_topics"]) > 0


# ============================================================================
# T-10.2 & T-10.7: Benchmark Evaluation on 60+ Labelled Dataset
# ============================================================================

def test_intent_classification_accuracy_on_labelled_dataset(nlp):
    """
    Evaluates intent accuracy across 60+ curated farmer queries in labelled_queries_60.json.
    Target accuracy: >= 90%.
    """
    dataset_path = FIXTURES_DIR / "labelled_queries_60.json"
    assert dataset_path.exists(), f"Dataset file not found at {dataset_path}"

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    assert len(dataset) >= 60, f"Expected at least 60 queries, got {len(dataset)}"

    correct = 0
    total = len(dataset)
    failures = []

    for item in dataset:
        q = item["query"]
        expected_intent = item["expected_intent"]
        result = nlp.analyze_query(q)

        # Allow flexible matching if mixed_query shares expected component or exact match
        if result.intent == expected_intent:
            correct += 1
        else:
            failures.append({
                "id": item.get("id"),
                "query": q,
                "expected": expected_intent,
                "predicted": result.intent,
                "confidence": result.confidence,
                "scores": result.intent_scores,
            })

    accuracy = (correct / total) * 100
    print(f"\n=======================================================")
    print(f" T-10 NLP Intent Classification Accuracy Benchmark")
    print(f" Total Queries Tested : {total}")
    print(f" Correct Predictions  : {correct}")
    print(f" Overall Accuracy     : {accuracy:.2f}%")
    print(f"=======================================================")

    if failures:
        print("\nMisclassified Examples:")
        for f in failures:
            print(f" - [{f['id']}] '{f['query']}' | Expected: {f['expected']} -> Predicted: {f['predicted']}")

    # Ensure high accuracy threshold (>= 90%)
    assert accuracy >= 90.0, f"Intent accuracy {accuracy:.2f}% is below required 90% threshold."
