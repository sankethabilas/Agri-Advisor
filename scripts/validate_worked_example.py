import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

BEST_PRACTICES_PATH = (
    PROJECT_ROOT / "knowledge_base" / "best_practices.json"
)

CROP_DB_PATH = (
    PROJECT_ROOT / "knowledge_base" / "crop_db.json"
)


with open(BEST_PRACTICES_PATH, "r", encoding="utf-8") as f:
    best_practices = json.load(f)

with open(CROP_DB_PATH, "r", encoding="utf-8") as f:
    crop_db = json.load(f)


print("=" * 65)
print("T-15.7 Worked Example Validation")
print("=" * 65)


assert "maize" in best_practices, (
    "Maize best-practices record not found"
)

assert "worked_example" in best_practices["maize"], (
    "Maize worked example not found"
)


example = best_practices["maize"]["worked_example"]


required_fields = [
    "title",
    "scenario",
    "recommended_varieties",
    "planting",
    "fertilizer_schedule",
    "irrigation",
    "weed_and_crop_management",
    "harvesting",
    "expected_yield",
    "source_ids"
]


for field in required_fields:
    assert field in example, (
        f"Worked example missing field: {field}"
    )


# --------------------------------------------------
# Validate scenario
# --------------------------------------------------

assert example["scenario"]["crop"] == "Maize"
assert example["scenario"]["season"] == "Maha"


# --------------------------------------------------
# Validate varieties against crop_db
# --------------------------------------------------

available_varieties = {
    variety["name"]
    for variety in crop_db["maize"]["varieties"]
}

example_varieties = {
    variety["name"]
    for variety in example["recommended_varieties"]
}


missing_varieties = (
    example_varieties - available_varieties
)

assert not missing_varieties, (
    f"Worked example varieties not found in crop_db: "
    f"{sorted(missing_varieties)}"
)


# --------------------------------------------------
# Validate advisory sections
# --------------------------------------------------

assert len(example["recommended_varieties"]) >= 1
assert len(example["fertilizer_schedule"]) >= 1
assert len(example["irrigation"]) >= 1
assert len(example["harvesting"]) >= 1
assert len(example["source_ids"]) >= 1


print("\nScenario")
print("Crop   :", example["scenario"]["crop"])
print("Region :", example["scenario"]["region"])
print("Season :", example["scenario"]["season"])

print(
    "\nRecommended varieties:",
    len(example["recommended_varieties"])
)

for variety in example["recommended_varieties"]:
    print("  -", variety["name"])


print(
    "Fertilizer stages     :",
    len(example["fertilizer_schedule"])
)

print(
    "Irrigation practices  :",
    len(example["irrigation"])
)

print(
    "Harvest practices     :",
    len(example["harvesting"])
)

print(
    "Sources               :",
    len(example["source_ids"])
)


print("\n" + "=" * 65)
print("T-15.7 worked example validation passed.")
print("=" * 65)