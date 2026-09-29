"""Search helpers for structured disease knowledge-base records."""

from typing import Any, Dict, Iterable, List

from knowledge_base.data_loader import load_disease_kb


def _location_name(location: Any) -> str:
    if isinstance(location, dict):
        return str(location.get("district", "")).strip().lower()
    return str(getattr(location, "district", location or "")).strip().lower()


def search(crop: str, symptoms: Iterable[str], location: Any) -> List[Dict[str, Any]]:
    """Filter disease records by crop, observed symptoms, and region."""
    crop_name = crop.strip().lower()
    crop_name = {"paddy": "rice"}.get(crop_name, crop_name)
    region = _location_name(location)
    observed = [str(symptom).strip().lower() for symptom in symptoms if str(symptom).strip()]
    candidates = []

    for key, disease in load_disease_kb().items():
        if str(disease.get("crop", "")).strip().lower() != crop_name:
            continue

        regions = [str(item).strip().lower() for item in disease.get("region", [])]
        if region and region not in regions and "sri lanka" not in regions:
            continue

        if not observed or not any(
            any(_symptom_tokens(query) & _symptom_tokens(known) for known in disease.get("symptoms", []))
            for query in observed
        ):
            continue

        candidates.append({"key": key, **disease})

    return candidates


_STOP_WORDS = {"a", "an", "and", "at", "by", "for", "in", "of", "on", "the", "to", "with"}
_ALIASES = {
    "yellowing": "yellow",
    "spots": "lesion",
    "spot": "lesion",
    "patches": "lesion",
    "patch": "lesion",
    "lesions": "lesion",
    "leaves": "leaf",
    "rings": "ring",
}
_GENERIC_SYMPTOM_TOKENS = {"fruit", "leaf", "lesion", "plant", "seed", "stem", "vein"}


def _symptom_tokens(value: str) -> set[str]:
    tokens = set()
    for token in value.lower().replace("-", " ").split():
        token = "".join(character for character in token if character.isalpha())
        if not token or token in _STOP_WORDS:
            continue
        token = _ALIASES.get(token, token)
        if token.endswith("s") and len(token) > 4:
            token = token[:-1]
        if token not in _GENERIC_SYMPTOM_TOKENS:
            tokens.add(token)
    return tokens