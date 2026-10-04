import json
from pathlib import Path
from collections import Counter


KB_DIR = Path("knowledge_base")

FILES = [
    "documents.json",
    "disease_kb.json",
    "treatment_db.json",
    "crop_db.json",
    "best_practices.json",
    "seasonal_calendar.json",
]


def type_name(value):
    if value is None:
        return "null"
    return type(value).__name__


def shorten(value, limit=100):
    text = repr(value)
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def inspect_nested(value):
    if isinstance(value, list):
        if not value:
            return "list[empty]"

        element_types = sorted(
            {type_name(item) for item in value}
        )

        info = f"list[{', '.join(element_types)}]"

        dict_items = [
            item for item in value
            if isinstance(item, dict)
        ]

        if dict_items:
            nested_keys = sorted(
                {
                    key
                    for item in dict_items
                    for key in item.keys()
                }
            )

            info += f" -> dict keys: {nested_keys}"

        return info

    if isinstance(value, dict):
        return f"dict keys: {sorted(value.keys())}"

    return type_name(value)


for filename in FILES:

    path = KB_DIR / filename

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    print("\n" + "=" * 80)
    print(filename)
    print("=" * 80)

    print("Top-level type :", type(data).__name__)
    print("Top-level count:", len(data))

    if isinstance(data, list):
        records = data

    elif isinstance(data, dict):
        records = list(data.values())

        print(
            "Sample top-level keys:",
            list(data.keys())[:5],
        )

    else:
        print("Unsupported structure.")
        continue

    dict_records = [
        record
        for record in records
        if isinstance(record, dict)
    ]

    print("Dictionary records:", len(dict_records))

    all_fields = sorted(
        {
            field
            for record in dict_records
            for field in record.keys()
        }
    )

    print("\nFIELDS")
    print("-" * 80)

    for field in all_fields:

        values = [
            record[field]
            for record in dict_records
            if field in record
        ]

        presence = len(values)

        types = Counter(
            type_name(value)
            for value in values
        )

        required = (
            "YES"
            if presence == len(dict_records)
            else "NO"
        )

        example = values[0] if values else None

        print(f"\nField: {field}")
        print(
            f"  Present : {presence}/{len(dict_records)}"
        )
        print(
            f"  Required: {required}"
        )
        print(
            f"  Types   : {dict(types)}"
        )
        print(
            f"  Shape   : {inspect_nested(example)}"
        )
        print(
            f"  Example : {shorten(example)}"
        )