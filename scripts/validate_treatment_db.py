import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DISEASE_KB_PATH = PROJECT_ROOT / "knowledge_base" / "disease_kb.json"
TREATMENT_DB_PATH = PROJECT_ROOT / "knowledge_base" / "treatment_db.json"


# Load files

with open(DISEASE_KB_PATH, "r", encoding="utf-8") as f:
    disease_kb = json.load(f)

with open(TREATMENT_DB_PATH, "r", encoding="utf-8") as f:
    treatment_db = json.load(f)


# Record counts

print("=" * 60)
print("T-15.2 / T-15.3 Treatment Database Validation")
print("=" * 60)

print(f"\nDisease records   : {len(disease_kb)}")
print(f"Treatment records : {len(treatment_db)}")


# Check matching keys

disease_keys = set(disease_kb.keys())
treatment_keys = set(treatment_db.keys())

missing = disease_keys - treatment_keys
extra = treatment_keys - disease_keys


print("\n--- Key Matching ---")

if missing:
    print(f"Missing treatment records: {len(missing)}")
    for key in sorted(missing):
        print(f"  - {key}")
else:
    print("Missing treatment records: 0")


if extra:
    print(f"Unexpected treatment records: {len(extra)}")
    for key in sorted(extra):
        print(f"  - {key}")
else:
    print("Unexpected treatment records: 0")


# Validate structure

required_fields = [
    "disease",
    "chemical",
    "organic",
    "cultural",
    "prevention",
    "source"
]

array_fields = [
    "chemical",
    "organic",
    "cultural",
    "prevention"
]


for key, record in treatment_db.items():

    for field in required_fields:
        assert field in record, (
            f"{key} is missing required field: {field}"
        )

    for field in array_fields:
        assert isinstance(record[field], list), (
            f"{key}.{field} must be a list"
        )


# Count empty arrays

empty_counts = {
    "chemical": 0,
    "organic": 0,
    "cultural": 0,
    "prevention": 0
}

non_empty_counts = {
    "chemical": 0,
    "organic": 0,
    "cultural": 0,
    "prevention": 0
}

fully_empty_records = []


for key, record in treatment_db.items():

    for field in array_fields:
        if len(record[field]) == 0:
            empty_counts[field] += 1
        else:
            non_empty_counts[field] += 1

    if all(len(record[field]) == 0 for field in array_fields):
        fully_empty_records.append(key)


# Display coverage statistics

print("\n--- Treatment Coverage ---")

for field in array_fields:
    print(
        f"{field.capitalize():12} "
        f"Filled: {non_empty_counts[field]:2} | "
        f"Empty: {empty_counts[field]:2}"
    )


print("\n--- Completely Empty Treatment Records ---")

print(
    "Records where chemical, organic, cultural "
    "and prevention are all empty:",
    len(fully_empty_records)
)

if fully_empty_records:
    for key in sorted(fully_empty_records):
        print(f"  - {key}")
else:
    print("None")


# Overall empty-array count

total_possible_arrays = len(treatment_db) * len(array_fields)
total_empty_arrays = sum(empty_counts.values())
total_filled_arrays = total_possible_arrays - total_empty_arrays

print("\n--- Overall Array Statistics ---")

print(f"Total treatment arrays : {total_possible_arrays}")
print(f"Filled arrays          : {total_filled_arrays}")
print(f"Empty arrays           : {total_empty_arrays}")

if total_possible_arrays > 0:
    empty_percentage = (
        total_empty_arrays / total_possible_arrays
    ) * 100

    print(f"Empty percentage       : {empty_percentage:.2f}%")


# Final validation

assert len(disease_kb) == len(treatment_db), (
    f"Record count mismatch: "
    f"{len(disease_kb)} diseases vs "
    f"{len(treatment_db)} treatments"
)

assert not missing, (
    f"{len(missing)} disease records have no treatment record"
)

assert not extra, (
    f"{len(extra)} treatment records have no matching disease"
)


print("\n" + "=" * 60)
print("T-15.2 and T-15.3 treatment database validation passed.")
print("=" * 60)