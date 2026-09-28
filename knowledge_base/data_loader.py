import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_DIR = Path(__file__).resolve().parent


# Internal JSON loader

def _load_json(filename: str) -> Dict[str, Any]:
    """
    Load a JSON file from the knowledge_base directory.
    """

    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Knowledge-base file not found: {file_path}"
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {filename}: {exc}"
        ) from exc


# Main database loaders

def load_disease_kb() -> Dict[str, Any]:
    """Load structured disease information."""
    return _load_json("disease_kb.json")


def load_treatment_db() -> Dict[str, Any]:
    """Load disease treatment and prevention information."""
    return _load_json("treatment_db.json")


def load_crop_db() -> Dict[str, Any]:
    """Load crop varieties and suitability information."""
    return _load_json("crop_db.json")


def load_best_practices() -> Dict[str, Any]:
    """Load crop cultivation best practices."""
    return _load_json("best_practices.json")


def load_seasonal_calendar() -> Dict[str, Any]:
    """Load Maha, Yala and year-round planting windows."""
    return _load_json("seasonal_calendar.json")


# Disease helpers

def get_disease(
    disease_key: str
) -> Optional[Dict[str, Any]]:
    """
    Return one disease using its exact disease key.
    """

    disease_kb = load_disease_kb()

    return disease_kb.get(
        disease_key.strip().lower()
    )


def get_diseases_by_crop(
    crop: str
) -> Dict[str, Dict[str, Any]]:
    """
    Return all diseases matching a crop.
    """

    disease_kb = load_disease_kb()

    crop_normalized = crop.strip().lower()

    return {
        key: disease
        for key, disease in disease_kb.items()
        if disease.get(
            "crop",
            ""
        ).strip().lower() == crop_normalized
    }


def get_diseases_by_region(
    region: str
) -> Dict[str, Dict[str, Any]]:
    """
    Return diseases whose region list contains the requested region.
    """

    disease_kb = load_disease_kb()

    region_normalized = region.strip().lower()

    matches = {}

    for key, disease in disease_kb.items():

        disease_regions = [
            str(value).strip().lower()
            for value in disease.get("region", [])
        ]

        if region_normalized in disease_regions:
            matches[key] = disease

    return matches

# Treatment helpers


def get_treatment(
    disease_key: str
) -> Optional[Dict[str, Any]]:
    """
    Return treatment and prevention information
    for an exact disease key.
    """

    treatment_db = load_treatment_db()

    return treatment_db.get(
        disease_key.strip().lower()
    )


def get_disease_with_treatment(
    disease_key: str
) -> Optional[Dict[str, Any]]:
    """
    Return disease information and its corresponding
    treatment record together.
    """

    disease = get_disease(disease_key)

    if disease is None:
        return None

    treatment = get_treatment(disease_key)

    return {
        "key": disease_key,
        "disease": disease,
        "treatment": treatment
    }


# Crop helpers

def get_crop(
    crop: str
) -> Optional[Dict[str, Any]]:
    """
    Return crop variety information.
    """

    crop_db = load_crop_db()

    return crop_db.get(
        crop.strip().lower()
    )


def get_crop_varieties(
    crop: str
) -> List[Dict[str, Any]]:
    """
    Return all available varieties for a crop.
    """

    crop_record = get_crop(crop)

    if not crop_record:
        return []

    return crop_record.get(
        "varieties",
        []
    )


def get_varieties_by_region(
    crop: str,
    region: str
) -> List[Dict[str, Any]]:
    """
    Return crop varieties suitable for the supplied region.

    Entries marked Sri Lanka are treated as generally
    applicable nationally.
    """

    varieties = get_crop_varieties(crop)

    region_normalized = region.strip().lower()

    matches = []

    for variety in varieties:

        regions = [
            str(item).strip().lower()
            for item in variety.get(
                "region",
                []
            )
        ]

        if (
            region_normalized in regions
            or "sri lanka" in regions
        ):
            matches.append(variety)

    return matches


def get_varieties_by_season(
    crop: str,
    season: str
) -> List[Dict[str, Any]]:
    """
    Return varieties suitable for a requested season.
    """

    varieties = get_crop_varieties(crop)

    season_normalized = season.strip().lower()

    matches = []

    for variety in varieties:

        seasons = [
            str(item).strip().lower()
            for item in variety.get(
                "season",
                []
            )
        ]

        if (
            season_normalized in seasons
            or "general" in seasons
        ):
            matches.append(variety)

    return matches


# Best-practice helpers

def get_best_practices(
    crop: str
) -> Optional[Dict[str, Any]]:
    """
    Return all cultivation best practices for a crop.
    """

    best_practices = load_best_practices()

    return best_practices.get(
        crop.strip().lower()
    )


def get_practice_category(
    crop: str,
    category: str
) -> List[Any]:
    """
    Return one best-practice category such as:
    planting, fertilizer, irrigation, harvesting, etc.
    """

    record = get_best_practices(crop)

    if not record:
        return []

    value = record.get(
        category.strip().lower(),
        []
    )

    if isinstance(value, list):
        return value

    return []


def get_worked_example(
    crop: str
) -> Optional[Dict[str, Any]]:
    """
    Return a worked advisory example where available.
    """

    record = get_best_practices(crop)

    if not record:
        return None

    return record.get("worked_example")


# Seasonal-calendar helpers

def get_season(
    season: str
) -> Optional[Dict[str, Any]]:
    """
    Return one seasonal-calendar record.
    """

    seasonal_calendar = load_seasonal_calendar()

    return seasonal_calendar.get(
        season.strip().lower()
    )


def get_planting_window(
    crop: str,
    season: str
) -> List[str]:
    """
    Return planting windows for a crop and season.
    """

    season_data = get_season(season)

    if not season_data:
        return []

    crop_windows = season_data.get(
        "crop_windows",
        {}
    )

    crop_data = crop_windows.get(
        crop.strip().lower()
    )

    if not crop_data:
        return []

    return crop_data.get(
        "planting_window",
        []
    )


# Convenience summary

def get_database_summary() -> Dict[str, Any]:
    """
    Return basic statistics for all structured databases.
    """

    disease_kb = load_disease_kb()
    treatment_db = load_treatment_db()
    crop_db = load_crop_db()
    best_practices = load_best_practices()
    seasonal_calendar = load_seasonal_calendar()

    total_varieties = sum(
        len(crop.get("varieties", []))
        for crop in crop_db.values()
    )

    return {
        "diseases": len(disease_kb),
        "treatment_records": len(treatment_db),
        "crops": len(crop_db),
        "crop_varieties": total_varieties,
        "best_practice_crops": len(best_practices),
        "season_groups": len(seasonal_calendar)
    }


# Manual test
if __name__ == "__main__":

    print("Structured data summary:")
    print(get_database_summary())

    print("\nRice disease count:")
    print(len(get_diseases_by_crop("rice")))

    print("\nRice blast:")
    print(get_disease("rice_blast"))

    print("\nRice blast treatment:")
    print(get_treatment("rice_blast"))

    print("\nMaize varieties:")
    for variety in get_crop_varieties("maize"):
        print("-", variety["name"])

    print("\nMaize Maha planting window:")
    print(get_planting_window("maize", "maha"))

    print("\nMaize worked example:")
    print(get_worked_example("maize"))