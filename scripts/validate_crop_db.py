import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CROP_DB_PATH = PROJECT_ROOT / "knowledge_base" / "crop_db.json"


with open(CROP_DB_PATH, "r", encoding="utf-8") as f:
    crop_db = json.load(f)


print("=" * 60)
print("T-15.4 Crop Database Validation")
print("=" * 60)


print(f"\nTotal crops: {len(crop_db)}")


total_varieties = 0

for crop_key, crop_data in crop_db.items():

    assert "crop" in crop_data, (
        f"{crop_key} is missing 'crop'"
    )

    assert "varieties" in crop_data, (
        f"{crop_key} is missing 'varieties'"
    )

    assert isinstance(crop_data["varieties"], list), (
        f"{crop_key}.varieties must be a list"
    )

    variety_count = len(crop_data["varieties"])
    total_varieties += variety_count

    print(
        f"{crop_data['crop']:15} : "
        f"{variety_count} varieties"
    )

    for variety in crop_data["varieties"]:

        required_fields = [
            "name",
            "region",
            "season",
            "suitability_reasons",
            "source"
        ]

        for field in required_fields:
            assert field in variety, (
                f"{crop_key} variety is missing: {field}"
            )

        assert isinstance(variety["region"], list)
        assert isinstance(variety["season"], list)
        assert isinstance(variety["suitability_reasons"], list)


print(f"\nTotal varieties: {total_varieties}")


assert len(crop_db) >= 5, (
    f"Expected at least 5 crops, found {len(crop_db)}"
)


print("\n" + "=" * 60)
print("T-15.4 crop database validation passed.")
print("=" * 60)