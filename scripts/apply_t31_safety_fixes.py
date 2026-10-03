from pathlib import Path
from datetime import datetime
import json
import re
import shutil


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_DIR = PROJECT_ROOT / "knowledge_base"

DOCUMENTS_FILE = KB_DIR / "documents.json"
TREATMENT_FILE = KB_DIR / "treatment_db.json"

BACKUP_DIR = PROJECT_ROOT / "backups" / "t31"


# ---------------------------------------------------------
# Standard safety caveats
# ---------------------------------------------------------

SAFETY_EN = (
    "Safety note: Use only pesticides currently registered in Sri Lanka "
    "for the crop and target pest or disease. Follow the current product "
    "label for dosage, personal protective equipment (PPE), re-entry "
    "interval and pre-harvest interval (PHI). If this stored recommendation "
    "conflicts with the current product label or current Department of "
    "Agriculture / Registrar of Pesticides guidance, follow the current "
    "official guidance."
)


SAFETY_SI = (
    "ආරක්ෂිත සටහන: මෙම බෝගය සහ අදාළ පළිබෝධ හෝ රෝගය සඳහා "
    "ශ්‍රී ලංකාවේ දැනට ලියාපදිංචි පළිබෝධනාශක පමණක් භාවිතා කරන්න. "
    "මාත්‍රාව, පුද්ගලික ආරක්ෂක උපකරණ (PPE), නැවත ඇතුළුවීමේ කාලය "
    "සහ අස්වනු නෙලීමට පෙර කාලය (PHI) සඳහා වත්මන් නිෂ්පාදන "
    "ලේබලය අනුගමනය කරන්න. මෙම ගබඩා කර ඇති නිර්දේශය වත්මන් "
    "නිෂ්පාදන ලේබලය හෝ කෘෂිකර්ම දෙපාර්තමේන්තුව / පළිබෝධනාශක "
    "රෙජිස්ට්‍රාර්ගේ වත්මන් මාර්ගෝපදේශ සමඟ නොගැලපේ නම් "
    "වත්මන් නිල මාර්ගෝපදේශය අනුගමනය කරන්න."
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write("\n")


def make_backups():
    """
    Create timestamped backups before editing the KB.
    """

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    documents_backup = (
        BACKUP_DIR
        / f"documents_before_safety_{timestamp}.json"
    )

    treatment_backup = (
        BACKUP_DIR
        / f"treatment_db_before_safety_{timestamp}.json"
    )

    shutil.copy2(
        DOCUMENTS_FILE,
        documents_backup,
    )

    shutil.copy2(
        TREATMENT_FILE,
        treatment_backup,
    )

    print("Backups created:")
    print(f"  - {documents_backup}")
    print(f"  - {treatment_backup}")


# ---------------------------------------------------------
# Safety detection
# ---------------------------------------------------------

def already_has_safety_caveat(text):
    """
    Detect whether a record already contains an explicit
    safety caveat.
    """

    if not text:
        return False

    text_lower = str(text).lower()

    english_terms = [
        "safety note:",
        "follow the current product label",
        "personal protective equipment",
        "pre-harvest interval",
        "pre harvest interval",
        "re-entry interval",
        "reentry interval",
        "currently registered in sri lanka",
        "registrar of pesticides",
    ]

    sinhala_terms = [
        "ආරක්ෂිත සටහන",
        "පුද්ගලික ආරක්ෂක උපකරණ",
        "අස්වනු නෙලීමට පෙර කාලය",
        "පළිබෝධනාශක රෙජිස්ට්‍රාර්",
        "වත්මන් නිෂ්පාදන ලේබලය",
    ]

    return (
        any(term in text_lower for term in english_terms)
        or any(term in str(text) for term in sinhala_terms)
    )


def contains_chemical_instruction(text):
    """
    Detect likely pesticide/fungicide/insecticide/herbicide
    instructions in general KB documents.

    The function intentionally avoids classifying ordinary
    fertilizer rates as pesticide instructions.
    """

    if not text:
        return False

    text_lower = str(text).lower()

    # Common pesticide formulation codes.
    formulation_pattern = (
        r"\b\d*(?:\.\d+)?\s*%?\s*"
        r"(?:wp|wg|sc|ec|sl|sp|dp|gr|cs|od)\b"
    )

    has_formulation = (
        re.search(
            formulation_pattern,
            text_lower,
            flags=re.IGNORECASE,
        )
        is not None
    )

    chemical_terms = [
        "pesticide",
        "fungicide",
        "insecticide",
        "herbicide",
        "acaricide",
        "chemical control",
        "seed treatment",
        "soil treatment",

        # Common active ingredients already found in the KB.
        "captan",
        "thiram",
        "mancozeb",
        "maneb",
        "carbendazim",
        "chlorothalonil",
        "propiconazole",
        "tebuconazole",
        "thiophanate",
        "metalaxyl",
        "pyraclostrobin",
        "metiram",
        "propineb",
        "bitertanol",
        "abamectin",
        "imidacloprid",
        "acephate",
        "chlorfluazuron",
        "tebufenozide",
        "sulfur 80",
        "sulphur 80",
    ]

    has_chemical_term = any(
        term in text_lower
        for term in chemical_terms
    )

    # Sinhala terms commonly indicating pesticide use.
    sinhala_terms = [
        "කෘමිනාශක",
        "දිලීරනාශක",
        "වල්නාශක",
        "පළිබෝධනාශක",
        "බීජ ප්‍රතිකාර",
    ]

    has_sinhala_chemical_term = any(
        term in str(text)
        for term in sinhala_terms
    )

    # Application/dosage signals.
    application_patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:g|kg|ml|l)\b",
        r"\bapply\b",
        r"\bapplication\b",
        r"\bspray\b",
        r"\btreat(?:ed|ing|ment)?\b",
        r"\bcontrol\b",
        r"\bmix(?:ed|ing)?\b",
        r"\bper\s+(?:kg|litre|liter|hectare)\b",
    ]

    has_application_signal = any(
        re.search(
            pattern,
            text_lower,
            flags=re.IGNORECASE,
        )
        for pattern in application_patterns
    )

    sinhala_application_terms = [
        "යෙදිය",
        "යොදන්න",
        "මිශ්‍ර",
        "ඉසින්න",
        "ප්‍රතිකාර",
        "පාලනය",
    ]

    has_sinhala_application = any(
        term in str(text)
        for term in sinhala_application_terms
    )

    chemical_marker = (
        has_formulation
        or has_chemical_term
        or has_sinhala_chemical_term
    )

    application_marker = (
        has_application_signal
        or has_sinhala_application
    )

    return chemical_marker and application_marker


# ---------------------------------------------------------
# Update treatment_db.json
# ---------------------------------------------------------

def update_treatment_database(treatments):
    """
    Add a safety_caveat field to every treatment record
    that contains chemical recommendations.
    """

    updated_records = []
    already_safe_records = []

    for key, record in treatments.items():

        chemical = record.get(
            "chemical",
            [],
        )

        if not isinstance(chemical, list):
            continue

        if not chemical:
            continue

        existing_caveat = record.get(
            "safety_caveat",
            "",
        )

        if already_has_safety_caveat(
            existing_caveat
        ):
            already_safe_records.append(key)
            continue

        record["safety_caveat"] = SAFETY_EN

        updated_records.append(key)

    return (
        updated_records,
        already_safe_records,
    )


# ---------------------------------------------------------
# Update documents.json
# ---------------------------------------------------------

def update_documents(documents):
    """
    Append a safety note to corpus documents containing
    chemical application instructions.
    """

    updated_documents = []
    already_safe_documents = []

    for document in documents:

        text = str(
            document.get(
                "text",
                "",
            )
        )

        if not contains_chemical_instruction(text):
            continue

        document_id = document.get(
            "id",
            "UNKNOWN"
        )

        if already_has_safety_caveat(text):
            already_safe_documents.append(
                document_id
            )
            continue

        language = str(
            document.get(
                "language",
                "en",
            )
        ).lower()

        if language == "si":
            safety_note = SAFETY_SI
        else:
            safety_note = SAFETY_EN

        document["text"] = (
            text.rstrip()
            + "\n\n"
            + safety_note
        )

        updated_documents.append(
            document_id
        )

    return (
        updated_documents,
        already_safe_documents,
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 72)
    print("T-31 CHEMICAL SAFETY FIX")
    print("=" * 72)

    print("\nLoading knowledge base...")

    treatments = load_json(
        TREATMENT_FILE
    )

    documents = load_json(
        DOCUMENTS_FILE
    )

    print(
        f"Treatment records : {len(treatments)}"
    )

    print(
        f"Corpus documents  : {len(documents)}"
    )

    print("\nCreating backups...")

    make_backups()

    # -----------------------------------------------------
    # Structured treatments
    # -----------------------------------------------------

    (
        updated_treatments,
        already_safe_treatments,
    ) = update_treatment_database(
        treatments
    )

    # -----------------------------------------------------
    # RAG documents
    # -----------------------------------------------------

    (
        updated_documents,
        already_safe_documents,
    ) = update_documents(
        documents
    )

    # -----------------------------------------------------
    # Save changes
    # -----------------------------------------------------

    save_json(
        TREATMENT_FILE,
        treatments,
    )

    save_json(
        DOCUMENTS_FILE,
        documents,
    )

    # -----------------------------------------------------
    # Report
    # -----------------------------------------------------

    print("\n" + "=" * 72)
    print("STRUCTURED TREATMENT DATABASE")
    print("=" * 72)

    print(
        f"Safety caveats added : "
        f"{len(updated_treatments)}"
    )

    print(
        f"Already safe         : "
        f"{len(already_safe_treatments)}"
    )

    if updated_treatments:

        print(
            "\nUpdated treatment records:"
        )

        for key in updated_treatments:
            print(f"  - {key}")

    print("\n" + "=" * 72)
    print("RAG CORPUS DOCUMENTS")
    print("=" * 72)

    print(
        f"Safety notes added   : "
        f"{len(updated_documents)}"
    )

    print(
        f"Already safe         : "
        f"{len(already_safe_documents)}"
    )

    if updated_documents:

        print(
            "\nUpdated corpus documents:"
        )

        for document_id in updated_documents:
            print(f"  - {document_id}")

    print("\n" + "=" * 72)
    print("T-31 SAFETY FIX COMPLETE")
    print("=" * 72)

    print(
        "\nNo pesticide names or dosage values "
        "were changed by this script."
    )

    print(
        "Only safety caveats were added."
    )


if __name__ == "__main__":
    main()