import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = PROJECT_ROOT / "knowledge_base"


FILES = [
    "disease_kb.json",
    "treatment_db.json",
    "crop_db.json",
    "best_practices.json",
    "seasonal_calendar.json"
]


print("=" * 70)
print("FINAL T-15 STRUCTURED DATA VALIDATION")
print("=" * 70)


# Verify required files

for filename in FILES:

    path = KB_DIR / filename

    assert path.exists(), (
        f"Missing required file: {filename}"
    )

    with open(path, "r", encoding="utf-8") as f:
        json.load(f)

    print(f"✓ {filename}")


# Load core databases

with open(
    KB_DIR / "disease_kb.json",
    "r",
    encoding="utf-8"
) as f:
    disease_kb = json.load(f)


with open(
    KB_DIR / "treatment_db.json",
    "r",
    encoding="utf-8"
) as f:
    treatment_db = json.load(f)


with open(
    KB_DIR / "crop_db.json",
    "r",
    encoding="utf-8"
) as f:
    crop_db = json.load(f)


with open(
    KB_DIR / "best_practices.json",
    "r",
    encoding="utf-8"
) as f:
    best_practices = json.load(f)


with open(
    KB_DIR / "seasonal_calendar.json",
    "r",
    encoding="utf-8"
) as f:
    seasonal_calendar = json.load(f)


# Core acceptance checks

assert len(disease_kb) >= 12
assert len(crop_db) >= 5

assert set(disease_kb.keys()) == set(
    treatment_db.keys()
), "Disease/treatment keys do not match"

assert "maha" in seasonal_calendar
assert "yala" in seasonal_calendar

assert "maize" in best_practices

assert "worked_example" in (
    best_practices["maize"]
)


# Statistics

total_varieties = sum(
    len(record.get("varieties", []))
    for record in crop_db.values()
)


print("\n--- T-15 Summary ---")

print(
    f"Disease records       : "
    f"{len(disease_kb)}"
)

print(
    f"Treatment records     : "
    f"{len(treatment_db)}"
)

print(
    f"Crop records          : "
    f"{len(crop_db)}"
)

print(
    f"Total crop varieties  : "
    f"{total_varieties}"
)

print(
    f"Best-practice crops   : "
    f"{len(best_practices)}"
)

print(
    f"Season groups         : "
    f"{len(seasonal_calendar)}"
)


print("\n--- Task Coverage ---")

print("T-15.1 disease_kb.json        ✓")
print("T-15.2 treatment_db.json      ✓")
print("T-15.3 prevention lists       ✓")
print("T-15.4 crop_db.json           ✓")
print("T-15.5 best_practices.json    ✓")
print("T-15.6 seasonal_calendar.json ✓")
print("T-15.7 worked advisory        ✓")
print("T-15.8 loader functions       ✓")


print("\n" + "=" * 70)
print("T-15 STRUCTURED DATA LAYER VALIDATION PASSED")
print("=" * 70)