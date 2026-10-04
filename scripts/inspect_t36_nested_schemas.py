import json
from pathlib import Path
from collections import defaultdict


KB = Path("knowledge_base")


def load(name):
    with open(KB / name, "r", encoding="utf-8") as f:
        return json.load(f)


def show_dict_schema(title, objects):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    fields = defaultdict(set)

    for obj in objects:
        if not isinstance(obj, dict):
            continue

        for key, value in obj.items():
            fields[key].add(type(value).__name__)

    for key in sorted(fields):
        print(
            f"{key:<30} {sorted(fields[key])}"
        )


# ---------------------------------------------------------
# disease_kb.json
# ---------------------------------------------------------

diseases = load("disease_kb.json")

show_dict_schema(
    "disease_kb.severity",
    [
        record["severity"]
        for record in diseases.values()
        if isinstance(record.get("severity"), dict)
    ],
)

show_dict_schema(
    "disease_kb.source",
    [
        record["source"]
        for record in diseases.values()
        if isinstance(record.get("source"), dict)
    ],
)


# ---------------------------------------------------------
# treatment_db.json
# ---------------------------------------------------------

treatments = load("treatment_db.json")

print("\n" + "=" * 80)
print("treatment_db list element types")
print("=" * 80)

for field in [
    "chemical",
    "organic",
    "cultural",
    "prevention",
]:
    types = set()

    non_empty = 0

    for record in treatments.values():
        values = record.get(field, [])

        if values:
            non_empty += 1

        for item in values:
            types.add(type(item).__name__)

    print(
        f"{field:<20} "
        f"element types={sorted(types)} "
        f"non-empty records={non_empty}"
    )


# ---------------------------------------------------------
# crop_db.json
# ---------------------------------------------------------

crops = load("crop_db.json")

varieties = []

for record in crops.values():
    varieties.extend(
        item
        for item in record.get("varieties", [])
        if isinstance(item, dict)
    )

show_dict_schema(
    "crop_db.varieties[]",
    varieties,
)

source_objects = []

for variety in varieties:
    source = variety.get("source")

    if isinstance(source, dict):
        source_objects.append(source)

show_dict_schema(
    "crop_db.varieties[].source",
    source_objects,
)


# ---------------------------------------------------------
# best_practices.json
# ---------------------------------------------------------

best = load("best_practices.json")

bp_sources = []

for record in best.values():
    bp_sources.extend(
        item
        for item in record.get("source", [])
        if isinstance(item, dict)
    )

show_dict_schema(
    "best_practices.source[]",
    bp_sources,
)

worked_examples = [
    record["worked_example"]
    for record in best.values()
    if isinstance(record.get("worked_example"), dict)
]

show_dict_schema(
    "best_practices.worked_example",
    worked_examples,
)

for field in [
    "planting",
    "fertilizer",
    "irrigation",
    "pest_disease_management",
    "harvesting",
    "rotation",
    "sustainability",
]:
    types = set()
    non_empty = 0

    for record in best.values():
        values = record.get(field, [])

        if values:
            non_empty += 1

        for item in values:
            types.add(type(item).__name__)

    print(
        f"{field:<30} "
        f"element types={sorted(types)} "
        f"non-empty records={non_empty}"
    )


# ---------------------------------------------------------
# seasonal_calendar.json
# ---------------------------------------------------------

calendar = load("seasonal_calendar.json")

window_objects = []

for season in calendar.values():

    windows = season.get(
        "crop_windows",
        {},
    )

    for crop_name, window in windows.items():

        if isinstance(window, dict):
            window_objects.append(window)

show_dict_schema(
    "seasonal_calendar.crop_windows.<crop>",
    window_objects,
)

calendar_sources = []

for window in window_objects:

    source = window.get("source", [])

    if isinstance(source, list):
        calendar_sources.extend(
            item
            for item in source
            if isinstance(item, dict)
        )

show_dict_schema(
    "seasonal_calendar crop-window source[]",
    calendar_sources,
)