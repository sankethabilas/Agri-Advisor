import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CALENDAR_PATH = (
    PROJECT_ROOT / "knowledge_base" / "seasonal_calendar.json"
)


with open(CALENDAR_PATH, "r", encoding="utf-8") as f:
    seasonal_calendar = json.load(f)


print("=" * 65)
print("T-15.6 Seasonal Calendar Validation")
print("=" * 65)


required_seasons = ["maha", "yala"]

for season in required_seasons:
    assert season in seasonal_calendar, (
        f"Missing required season: {season}"
    )

    assert "name" in seasonal_calendar[season]
    assert "description" in seasonal_calendar[season]
    assert "crop_windows" in seasonal_calendar[season]

    assert isinstance(
        seasonal_calendar[season]["crop_windows"],
        dict
    )


print("\nRequired seasons found:")
for season in required_seasons:
    print(f"  - {season}")


total_crop_windows = 0
empty_windows = []


for season_key, season_data in seasonal_calendar.items():

    if "crop_windows" not in season_data:
        continue

    print(f"\n--- {season_data['name']} ---")

    for crop_key, crop_data in season_data["crop_windows"].items():

        assert "planting_window" in crop_data
        assert "notes" in crop_data
        assert "source" in crop_data

        assert isinstance(crop_data["planting_window"], list)
        assert isinstance(crop_data["notes"], list)
        assert isinstance(crop_data["source"], list)

        total_crop_windows += 1

        if not crop_data["planting_window"]:
            empty_windows.append(
                f"{season_key}.{crop_key}"
            )

        print(
            f"{crop_key:20} "
            f"windows: {len(crop_data['planting_window'])}"
        )


print("\n--- Overall Statistics ---")

print(f"Total season/crop records : {total_crop_windows}")
print(f"Empty planting windows    : {len(empty_windows)}")


if empty_windows:
    print("\nEmpty planting-window records:")
    for item in empty_windows:
        print(f"  - {item}")


assert len(
    seasonal_calendar["maha"]["crop_windows"]
) >= 5, "Expected at least 5 Maha crop records"

assert len(
    seasonal_calendar["yala"]["crop_windows"]
) >= 5, "Expected at least 5 Yala crop records"


print("\n" + "=" * 65)
print("T-15.6 seasonal calendar validation passed.")
print("=" * 65)