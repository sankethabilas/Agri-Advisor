from pathlib import Path
from collections import Counter
import json
import re


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_DIR = PROJECT_ROOT / "knowledge_base"

DOCUMENTS_FILE = KB_DIR / "documents.json"
DISEASE_FILE = KB_DIR / "disease_kb.json"
TREATMENT_FILE = KB_DIR / "treatment_db.json"


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_crop(crop):
    """
    Normalize English/Sinhala crop-name variants so translated
    documents are counted under the same crop.
    """

    if not crop:
        return "unknown"

    value = str(crop).strip().lower()

    aliases = {
        # Chilli
        "chilli": "chilli",
        "chili": "chilli",
        "මිරිස්": "chilli",

        # Maize
        "maize": "maize",
        "බඩඉරිඟු": "maize",
        "බඩ ඉරිඟු": "maize",

        # Rice
        "rice": "rice",
        "paddy": "rice",
        "වී": "rice",

        # Tomato
        "tomato": "tomato",
        "තක්කාලි": "tomato",

        # Peanut / Groundnut
        "peanut": "peanut",
        "groundnut": "peanut",
        "රටකජු": "peanut",

        # Soybean
        "soybean": "soybean",
        "soya bean": "soybean",
        "සෝයා බෝංචි": "soybean",

        # Mungbean
        "mungbean": "mungbean",
        "mung bean": "mungbean",
        "මුං": "mungbean",

        # Cowpea
        "cowpea": "cowpea",
        "කව්පි": "cowpea",

        # Sesame
        "sesame": "sesame",
        "තල": "sesame",

        # Finger millet
        "finger millet": "finger millet",
        "කුරක්කන්": "finger millet",

        # Big onion
        "big onion": "big onion",
        "onion": "big onion",
        "ලොකු ලූනු": "big onion",

        # Legumes
        "legume": "legumes",
        "legumes": "legumes",
        "රනිල බෝග": "legumes",
    }

    return aliases.get(value, value)


def contains_numeric_dosage(text):
    """
    Detect likely numeric dosage/application instructions.
    Used mainly for the structured treatment database where the
    content already comes from the chemical treatment field.
    """

    if not text:
        return False

    patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:g|kg|ml|l)\b",
        r"\b\d+(?:\.\d+)?\s*(?:g|kg|ml|l)\s*/\s*\d+(?:\.\d+)?\s*l\b",
        r"\b\d+(?:\.\d+)?\s*(?:g|kg)\s*/\s*kg\b",
        r"\b\d+(?:\.\d+)?\s*(?:kg|g)\s*/\s*ha\b",
        r"\b\d+(?:\.\d+)?\s*%\s*(?:wp|wg|sc|ec|sl|sp)\b",
    ]

    text = text.lower()

    return any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in patterns
    )


def contains_pesticide_dosage(text):
    """
    Detect likely pesticide/fungicide/insecticide dosage instructions
    in the general RAG corpus.

    This is stricter than contains_numeric_dosage() so ordinary
    fertilizer quantities such as kg/ha are less likely to be counted.
    """

    if not text:
        return False

    text_lower = text.lower()

    dosage_patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:g|kg|ml)\s*/\s*\d+(?:\.\d+)?\s*l\b",
        r"\b\d+(?:\.\d+)?\s*(?:g|kg|ml)\s+per\s+\d+(?:\.\d+)?\s*l\b",
        r"\b\d+(?:\.\d+)?\s*(?:g|kg)\s*/\s*kg\b",
        r"\b\d+(?:\.\d+)?\s*(?:g|ml)\s*/\s*l\b",
    ]

    has_dosage = any(
        re.search(pattern, text_lower, flags=re.IGNORECASE)
        for pattern in dosage_patterns
    )

    formulation_pattern = r"\b(?:wp|wg|sc|ec|sl|sp|dp|gr)\b"

    pesticide_words = [
        "pesticide",
        "fungicide",
        "insecticide",
        "acaricide",
        "herbicide",
        "chemical control",
        "seed treatment",
    ]

    has_chemical_marker = (
        re.search(
            formulation_pattern,
            text_lower,
            flags=re.IGNORECASE,
        )
        is not None
        or any(word in text_lower for word in pesticide_words)
    )

    return has_dosage and has_chemical_marker


def contains_safety_caveat(text):
    """
    Detect explicit chemical-use safety guidance.

    Generic wording such as 'according to recommendations' is not
    treated as a sufficient safety caveat.
    """

    if not text:
        return False

    text = text.lower()

    safety_terms = [
        "follow the product label",
        "follow label directions",
        "follow label instructions",
        "read the product label",
        "use personal protective equipment",
        "personal protective equipment",
        "wear appropriate protective equipment",
        "ppe",
        "pre-harvest interval",
        "pre harvest interval",
        "waiting period",
        "re-entry interval",
        "reentry interval",
        "currently registered",
        "current registration",
        "locally registered",
        "registered for this crop",
        "approved for this crop",
        "consult an agricultural extension officer",
        "consult a local agricultural extension officer",
        "confirm with an agricultural extension officer",

        # Sinhala
        "ආරක්ෂිත සටහන",
        "පුද්ගලික ආරක්ෂක උපකරණ",
        "අස්වනු නෙලීමට පෙර කාලය",
        "පළිබෝධනාශක රෙජිස්ට්‍රාර්",
        "වත්මන් නිෂ්පාදන ලේබලය",
    ]

    return any(term in text for term in safety_terms)


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

documents = load_json(DOCUMENTS_FILE)
diseases = load_json(DISEASE_FILE)
treatments = load_json(TREATMENT_FILE)


print("=" * 70)
print("T-31 KNOWLEDGE BASE QA BASELINE AUDIT")
print("=" * 70)


# ---------------------------------------------------------
# 1. Basic counts
# ---------------------------------------------------------

print("\n1. DATABASE COUNTS")
print("-" * 70)

print(f"Corpus documents       : {len(documents)}")
print(f"Disease records        : {len(diseases)}")
print(f"Treatment records      : {len(treatments)}")


# ---------------------------------------------------------
# 2. Required document fields
# ---------------------------------------------------------

required_document_fields = {
    "id",
    "title",
    "text",
    "crop",
    "category",
    "source",
    "source_id",
    "region",
    "season",
}

missing_document_fields = []

for document in documents:
    missing = [
        field
        for field in required_document_fields
        if field not in document
        or document[field] is None
        or str(document[field]).strip() == ""
    ]

    if missing:
        missing_document_fields.append(
            {
                "id": document.get("id"),
                "missing": missing,
            }
        )


print("\n2. DOCUMENT SCHEMA")
print("-" * 70)

print(f"Documents checked      : {len(documents)}")
print(f"Schema issues          : {len(missing_document_fields)}")

if missing_document_fields:
    for issue in missing_document_fields:
        print(issue)


# ---------------------------------------------------------
# 3. Duplicate IDs
# ---------------------------------------------------------

ids = [document.get("id") for document in documents]

duplicate_ids = [
    document_id
    for document_id, count in Counter(ids).items()
    if count > 1
]

print("\n3. DOCUMENT ID CHECK")
print("-" * 70)

print(f"Duplicate IDs          : {len(duplicate_ids)}")

for duplicate_id in duplicate_ids:
    print(f"  - {duplicate_id}")


# ---------------------------------------------------------
# 4. Crop coverage
# ---------------------------------------------------------

crop_counts = Counter(
    normalize_crop(document.get("crop"))
    for document in documents
)

print("\n4. CROP COVERAGE")
print("-" * 70)

for crop, count in crop_counts.most_common():
    print(f"{crop:<20} {count}")


# ---------------------------------------------------------
# 5. Category coverage
# ---------------------------------------------------------

category_counts = Counter(
    str(document.get("category", "unknown")).strip().lower()
    for document in documents
)

print("\n5. CATEGORY COVERAGE")
print("-" * 70)

for category, count in category_counts.most_common():
    print(f"{category:<30} {count}")


# ---------------------------------------------------------
# 6. Region metadata
# ---------------------------------------------------------

region_counts = Counter(
    str(document.get("region", "unknown")).strip()
    for document in documents
)

print("\n6. REGION METADATA")
print("-" * 70)

for region, count in region_counts.most_common():
    print(f"{region:<35} {count}")


# ---------------------------------------------------------
# 7. Zone references inside document text
# ---------------------------------------------------------

zone_terms = {
    "dry_zone": [
        "dry zone",
        "වියළි කලාප",
    ],
    "wet_zone": [
        "wet zone",
        "තෙත් කලාප",
    ],
    "intermediate_zone": [
        "intermediate zone",
        "අතරමැදි කලාප",
    ],
}

zone_matches = {
    zone: []
    for zone in zone_terms
}

for document in documents:
    text = str(document.get("text", "")).lower()

    for zone, terms in zone_terms.items():
        if any(term.lower() in text for term in terms):
            zone_matches[zone].append(document.get("id"))


print("\n7. AGROCLIMATIC ZONE REFERENCES")
print("-" * 70)

for zone, matches in zone_matches.items():
    print(f"{zone:<25} {len(matches)} documents")


# ---------------------------------------------------------
# 8. Source inventory
# ---------------------------------------------------------

source_counter = Counter()
source_id_counter = Counter()
missing_source_documents = []

for document in documents:
    source = str(document.get("source", "")).strip()
    source_id = str(document.get("source_id", "")).strip()

    if not source or not source_id:
        missing_source_documents.append(document.get("id"))

    if source:
        source_counter[source] += 1

    if source_id:
        source_id_counter[source_id] += 1


print("\n8. SOURCE ATTRIBUTION")
print("-" * 70)

print(f"Unique source names     : {len(source_counter)}")
print(f"Unique source IDs       : {len(source_id_counter)}")
print(f"Missing source records  : {len(missing_source_documents)}")

print("\nSOURCE NAMES:")

for source, count in source_counter.most_common():
    print(f"{count:>4}  {source}")


# ---------------------------------------------------------
# 9. Disease/treatment consistency
# ---------------------------------------------------------

disease_keys = set(diseases.keys())
treatment_keys = set(treatments.keys())

missing_treatments = sorted(disease_keys - treatment_keys)
orphan_treatments = sorted(treatment_keys - disease_keys)


print("\n9. DISEASE / TREATMENT KEY CONSISTENCY")
print("-" * 70)

print(f"Diseases without treatment record : {len(missing_treatments)}")
print(f"Treatments without disease record : {len(orphan_treatments)}")

if missing_treatments:
    print("\nMissing treatment records:")

    for key in missing_treatments:
        print(f"  - {key}")

if orphan_treatments:
    print("\nOrphan treatment records:")

    for key in orphan_treatments:
        print(f"  - {key}")


# ---------------------------------------------------------
# 10. Structured chemical treatment audit
# ---------------------------------------------------------

chemical_records = []
numeric_dosage_records = []
missing_safety_records = []

for key, treatment in treatments.items():
    chemical = treatment.get("chemical", [])

    if not isinstance(chemical, list) or not chemical:
        continue

    chemical_records.append(key)

    combined_text = " ".join(
        str(item)
        for item in chemical
    )

    has_dosage = contains_numeric_dosage(combined_text)

    full_record_text = json.dumps(
        treatment,
        ensure_ascii=False,
    )

    has_safety = contains_safety_caveat(
        full_record_text
    )

    if has_dosage:
        numeric_dosage_records.append(key)

        if not has_safety:
            missing_safety_records.append(key)


print("\n10. CHEMICAL TREATMENT SAFETY AUDIT")
print("-" * 70)

print(
    f"Records with chemical recommendations : "
    f"{len(chemical_records)}"
)

print(
    f"Records with numeric dosage            : "
    f"{len(numeric_dosage_records)}"
)

print(
    f"Numeric dosage without safety caveat   : "
    f"{len(missing_safety_records)}"
)

if missing_safety_records:
    print("\nRecords requiring safety review:")

    for key in missing_safety_records:
        print(f"  - {key}")


# ---------------------------------------------------------
# 11. Corpus-level pesticide dosage audit
# ---------------------------------------------------------

corpus_dosage_documents = []
corpus_missing_safety = []

for document in documents:
    text = str(document.get("text", ""))

    if contains_pesticide_dosage(text):
        corpus_dosage_documents.append(
            document.get("id")
        )

        if not contains_safety_caveat(text):
            corpus_missing_safety.append(
                document.get("id")
            )


print("\n11. CORPUS PESTICIDE DOSAGE AUDIT")
print("-" * 70)

print(
    f"Documents containing pesticide dosage : "
    f"{len(corpus_dosage_documents)}"
)

print(
    f"Dosage documents without safety caveat : "
    f"{len(corpus_missing_safety)}"
)

if corpus_missing_safety:
    print("\nCorpus documents requiring safety review:")

    for document_id in corpus_missing_safety:
        print(f"  - {document_id}")


# ---------------------------------------------------------
# 12. Under-represented crop detection
# ---------------------------------------------------------

print("\n12. CROP COVERAGE REVIEW")
print("-" * 70)

if crop_counts:
    max_count = max(crop_counts.values())

    # A simple baseline rule:
    # less than 25% of the highest-covered crop is flagged.
    threshold = max_count * 0.25

    underrepresented_crops = {
        crop: count
        for crop, count in crop_counts.items()
        if count < threshold
    }

    print(
        f"Highest crop coverage   : "
        f"{max_count} documents"
    )

    print(
        f"Review threshold        : "
        f"< {threshold:.1f} documents"
    )

    print(
        f"Under-represented crops : "
        f"{len(underrepresented_crops)}"
    )

    for crop, count in sorted(
        underrepresented_crops.items(),
        key=lambda item: item[1],
    ):
        print(f"  - {crop}: {count}")

else:
    underrepresented_crops = {}


# ---------------------------------------------------------
# 13. Final baseline status
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("T-31 BASELINE SUMMARY")
print("=" * 70)

print(f"Corpus documents        : {len(documents)}")
print(f"Disease records         : {len(diseases)}")
print(f"Treatment records       : {len(treatments)}")
print(f"Normalized crop groups  : {len(crop_counts)}")
print(f"Unique source names     : {len(source_counter)}")
print(f"Unique source IDs       : {len(source_id_counter)}")
print(f"Missing source records  : {len(missing_source_documents)}")
print(f"Duplicate IDs           : {len(duplicate_ids)}")
print(f"Chemical records        : {len(chemical_records)}")
print(f"Numeric dosage records  : {len(numeric_dosage_records)}")
print(f"Safety review required  : {len(missing_safety_records)}")
print(
    f"Corpus pesticide dosage : "
    f"{len(corpus_dosage_documents)}"
)
print(
    f"Corpus safety review    : "
    f"{len(corpus_missing_safety)}"
)
print(
    f"Under-represented crops : "
    f"{len(underrepresented_crops)}"
)

print("\nAudit complete.")