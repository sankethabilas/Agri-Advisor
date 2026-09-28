import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BEST_PRACTICES_PATH = (
    PROJECT_ROOT / "knowledge_base" / "best_practices.json"
)


with open(BEST_PRACTICES_PATH, "r", encoding="utf-8") as f:
    best_practices = json.load(f)


required_fields = [
    "crop",
    "planting",
    "fertilizer",
    "irrigation",
    "pest_disease_management",
    "harvesting",
    "rotation",
    "sustainability",
    "source"
]

practice_fields = [
    "planting",
    "fertilizer",
    "irrigation",
    "pest_disease_management",
    "harvesting",
    "rotation",
    "sustainability"
]


print("=" * 65)
print("T-15.5 Best Practices Validation")
print("=" * 65)

print(f"\nTotal crops: {len(best_practices)}")


empty_counts = {field: 0 for field in practice_fields}
filled_counts = {field: 0 for field in practice_fields}

completely_empty_crops = []


for crop_key, record in best_practices.items():

    print(f"\nChecking: {crop_key}")

    for field in required_fields:
        assert field in record, (
            f"{crop_key} missing required field: {field}"
        )

    for field in practice_fields:

        assert isinstance(record[field], list), (
            f"{crop_key}.{field} must be a list"
        )

        if record[field]:
            filled_counts[field] += 1
        else:
            empty_counts[field] += 1

    if all(
        len(record[field]) == 0
        for field in practice_fields
    ):
        completely_empty_crops.append(crop_key)


print("\n--- Best Practice Coverage ---")

for field in practice_fields:
    print(
        f"{field:25} "
        f"Filled: {filled_counts[field]:2} | "
        f"Empty: {empty_counts[field]:2}"
    )


print("\n--- Completely Empty Crops ---")

if completely_empty_crops:
    for crop in completely_empty_crops:
        print(f"  - {crop}")
else:
    print("None")


total_arrays = len(best_practices) * len(practice_fields)
total_empty = sum(empty_counts.values())
total_filled = total_arrays - total_empty


print("\n--- Overall Statistics ---")

print(f"Total crops            : {len(best_practices)}")
print(f"Practice categories    : {len(practice_fields)}")
print(f"Total practice arrays  : {total_arrays}")
print(f"Filled arrays          : {total_filled}")
print(f"Empty arrays           : {total_empty}")

if total_arrays:
    print(
        f"Empty percentage       : "
        f"{(total_empty / total_arrays) * 100:.2f}%"
    )


assert len(best_practices) >= 5, (
    f"Expected at least 5 crops, found {len(best_practices)}"
)


print("\n" + "=" * 65)
print("T-15.5 best practices validation passed.")
print("=" * 65)