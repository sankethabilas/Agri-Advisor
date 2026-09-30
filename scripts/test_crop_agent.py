import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


from agents.crop.crop_agent import CropAdvisoryAgent


agent = CropAdvisoryAgent()


print("=" * 70)
print("T-19 Crop Advisory Agent Test")
print("=" * 70)


# Test 1 - Maize Maha advisory

result = agent.get_advisory(
    crop="maize",
    location="Sri Lanka",
    season="maha"
)


assert result["success"] is True

assert result["crop"] == "Maize"

assert result["advisory"] is not None


advisory = result["advisory"]


required_sections = [
    "varieties",
    "planting",
    "fertilizer",
    "irrigation",
    "pest_management",
    "harvesting",
    "rotation",
    "sustainability"
]


for section in required_sections:

    assert section in advisory, (
        f"Missing advisory section: {section}"
    )


print("\n✓ All eight advisory sections present")


# Test 2 - Variety recommendation

assert len(
    advisory["varieties"]
) > 0

print(
    f"✓ Variety recommendation passed "
    f"({len(advisory['varieties'])} varieties)"
)


# Test 3 - Planting advice

assert advisory["planting"][
    "planting_window"
]

print("✓ Maha planting window returned")


# Test 4 - Fertilizer


assert advisory["fertilizer"]

print(
    f"✓ Fertilizer guidance returned "
    f"({len(advisory['fertilizer'])} items)"
)


# Test 5 - Irrigation


assert advisory["irrigation"][
    "guidance"
]

print("✓ Irrigation guidance returned")


# Test 6 - Pest management

assert advisory["pest_management"]

print("✓ Pest/disease management returned")


# Test 7 - Harvest

assert advisory["harvesting"][
    "guidance"
]

print("✓ Harvesting advice returned")


# Test 8 - Rotation

assert advisory["rotation"]

print("✓ Rotation recommendations returned")


# Test 9 - Sustainability


assert advisory["sustainability"]

print("✓ Sustainable practices returned")


# Test 10 - Unknown crop


unknown = agent.get_advisory(
    crop="unknown_crop",
    location="Sri Lanka",
    season="maha"
)


assert unknown["success"] is False
assert unknown["advisory"] is None

print("✓ Unknown-crop fallback passed")


print("\n" + "=" * 70)
print("T-19 CROP ADVISORY AGENT TESTS PASSED")
print("=" * 70)