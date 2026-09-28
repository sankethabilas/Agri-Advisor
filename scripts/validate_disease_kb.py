import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DISEASE_KB_PATH = PROJECT_ROOT / "knowledge_base" / "disease_kb.json"


with open(DISEASE_KB_PATH, "r", encoding="utf-8") as f:
    disease_kb = json.load(f)


print("Total diseases:", len(disease_kb))

crops = sorted(set(d["crop"] for d in disease_kb.values()))

print("Crops:", crops)
print("Crop count:", len(crops))


assert len(disease_kb) >= 50, (
    f"Expected 50 diseases, found {len(disease_kb)}"
)

assert len(crops) >= 5, (
    f"Expected at least 5 crops, found {len(crops)}"
)


print("T-15.1 disease coverage passed.")