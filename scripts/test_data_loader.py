import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


from knowledge_base.data_loader import (
    load_disease_kb,
    load_treatment_db,
    load_crop_db,
    load_best_practices,
    load_seasonal_calendar,
    get_disease,
    get_treatment,
    get_diseases_by_crop,
    get_crop_varieties,
    get_varieties_by_region,
    get_best_practices,
    get_planting_window,
    get_worked_example,
    get_database_summary
)


print("=" * 65)
print("T-15.8 Structured Data Loader Test")
print("=" * 65)


# --------------------------------------------------
# Load all files
# --------------------------------------------------

disease_kb = load_disease_kb()
treatment_db = load_treatment_db()
crop_db = load_crop_db()
best_practices = load_best_practices()
calendar = load_seasonal_calendar()


assert disease_kb
assert treatment_db
assert crop_db
assert best_practices
assert calendar


print("\nAll five JSON files loaded successfully.")


# --------------------------------------------------
# Disease lookup
# --------------------------------------------------

rice_blast = get_disease("rice_blast")

assert rice_blast is not None
assert rice_blast["crop"].lower() == "rice"

print("Disease exact-key lookup passed.")


# --------------------------------------------------
# Treatment lookup
# --------------------------------------------------

rice_blast_treatment = get_treatment(
    "rice_blast"
)

assert rice_blast_treatment is not None

print("Treatment lookup passed.")


# --------------------------------------------------
# Crop filtering
# --------------------------------------------------

rice_diseases = get_diseases_by_crop(
    "rice"
)

assert len(rice_diseases) > 0

print(
    f"Rice disease filtering passed "
    f"({len(rice_diseases)} records)."
)


# --------------------------------------------------
# Crop database
# --------------------------------------------------

maize_varieties = get_crop_varieties(
    "maize"
)

assert len(maize_varieties) > 0

print(
    f"Maize variety lookup passed "
    f"({len(maize_varieties)} varieties)."
)


# --------------------------------------------------
# Regional variety lookup
# --------------------------------------------------

chilli_north = get_varieties_by_region(
    "chilli",
    "Northern Province"
)

assert len(chilli_north) > 0

print(
    "Regional variety lookup passed."
)


# --------------------------------------------------
# Best practices
# --------------------------------------------------

maize_practices = get_best_practices(
    "maize"
)

assert maize_practices is not None
assert maize_practices["planting"]

print("Best-practice lookup passed.")


# --------------------------------------------------
# Seasonal calendar
# --------------------------------------------------

maize_maha = get_planting_window(
    "maize",
    "maha"
)

assert len(maize_maha) > 0

print(
    "Seasonal planting-window lookup passed."
)


# --------------------------------------------------
# Worked example
# --------------------------------------------------

maize_example = get_worked_example(
    "maize"
)

assert maize_example is not None
assert (
    maize_example["scenario"]["season"]
    == "Maha"
)

print("Worked-example lookup passed.")


# --------------------------------------------------
# Summary
# --------------------------------------------------

summary = get_database_summary()

print("\n--- Database Summary ---")

for key, value in summary.items():
    print(f"{key:25}: {value}")


assert summary["diseases"] >= 50
assert summary["treatment_records"] == summary["diseases"]
assert summary["crops"] >= 5


print("\n" + "=" * 65)
print("T-15.8 loader tests passed.")
print("=" * 65)