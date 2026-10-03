from pathlib import Path
from datetime import datetime
import json
import shutil


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_DIR = PROJECT_ROOT / "knowledge_base"

DOCUMENTS_FILE = KB_DIR / "documents.json"
BACKUP_DIR = PROJECT_ROOT / "backups" / "t31"


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


def make_backup():
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        BACKUP_DIR
        / f"documents_before_verified_corrections_{timestamp}.json"
    )

    shutil.copy2(
        DOCUMENTS_FILE,
        backup_path,
    )

    print(f"Backup created: {backup_path}")


# ---------------------------------------------------------
# Verified corrections
# ---------------------------------------------------------

CORRECTIONS = {

    # -----------------------------------------------------
    # Big Onion
    # Current DOA guidance:
    # Thiram 80%         5 g/kg
    # Captan 80%         4 g/kg
    # Captan 50%         6 g/kg
    # Thiophanate methyl 50% + Thiram 30% WP  4 g/kg
    # -----------------------------------------------------

    "O-C-005-EN": {
        "old": (
            "The source recommends seed treatment before sowing "
            "using either Thiram 80% at 4–4.5 g per kg of seed "
            "or Thiophanate methyl 50% + Thiram 30% WP at "
            "4 g per kg of seed."
        ),
        "new": (
            "Current Department of Agriculture guidance recommends "
            "seed treatment before sowing using Thiram 80% at "
            "5 g per kg of seed, Captan 80% at 4 g per kg of seed, "
            "Captan 50% at 6 g per kg of seed, or Thiophanate "
            "methyl 50% + Thiram 30% WP at 4 g per kg of seed."
        ),
    },

    "O-C-005-SI": {
        "old": (
            "බී ලූණු බීජ වපුරීමට පෙර බීජ ප්‍රතිකාර කිරීම සඳහා "
            "Thiram 80% 4–4.5 g/kg බීජ හෝ Thiophanate methyl "
            "50% + Thiram 30% WP 4 g/kg බීජ භාවිතා කරන බව "
            "මූලාශ්‍රයේ සඳහන් වේ."
        ),
        "new": (
            "බී ලූණු බීජ වපුරීමට පෙර බීජ කිලෝග්‍රෑම් 1කට "
            "Thiram 80% 5 g, Captan 80% 4 g, Captan 50% 6 g "
            "හෝ Thiophanate methyl 50% + Thiram 30% WP 4 g "
            "යොදා බීජ ප්‍රතිකාර කිරීම වත්මන් කෘෂිකර්ම "
            "දෙපාර්තමේන්තු මාර්ගෝපදේශයේ සඳහන් වේ."
        ),
    },

    # -----------------------------------------------------
    # Mungbean
    # Current DOA guidance:
    # Captan                         3 g/kg
    # Thiram                         2 g/kg
    # Thiram + Thiophanate methyl    2 g/kg
    # -----------------------------------------------------

    "MG-C-002-EN": {
        "old": (
            "To protect mungbean from fungal diseases, the seeds "
            "should be treated by mixing 4 g of a suitable "
            "fungicide with 1 kg of seed."
        ),
        "new": (
            "To protect mungbean from fungal diseases, current "
            "Department of Agriculture guidance recommends treating "
            "1 kg of seed with Captan at 3 g, Thiram at 2 g, "
            "or Thiram + Thiophanate methyl at 2 g."
        ),
    },

    "MG-C-002-SI": {
        "old": (
            "මුං බෝගය දිලීර රෝගවලින් ආරක්ෂා කර ගැනීම සඳහා "
            "සුදුසු දිලීරනාශකයකින් බීජ කිලෝග්‍රෑම් 1 කට "
            "ග්‍රෑම් 4 ක් මිශ්‍ර කර බීජ ප්‍රතිකාර කළ යුතුය."
        ),
        "new": (
            "මුං බීජ දිලීර රෝගවලින් ආරක්ෂා කිරීම සඳහා "
            "බීජ කිලෝග්‍රෑම් 1කට Captan 3 g, Thiram 2 g "
            "හෝ Thiram + Thiophanate methyl 2 g යොදා "
            "බීජ ප්‍රතිකාර කිරීම වත්මන් කෘෂිකර්ම "
            "දෙපාර්තමේන්තු මාර්ගෝපදේශයේ සඳහන් වේ."
        ),
    },
}


# ---------------------------------------------------------
# Apply corrections
# ---------------------------------------------------------

def apply_corrections(documents):

    documents_by_id = {
        document.get("id"): document
        for document in documents
    }

    updated = []
    failed = []

    for document_id, correction in CORRECTIONS.items():

        document = documents_by_id.get(document_id)

        if document is None:
            failed.append(
                (document_id, "document not found")
            )
            continue

        text = document.get("text", "")

        old_text = correction["old"]
        new_text = correction["new"]

        if old_text not in text:
            failed.append(
                (
                    document_id,
                    "expected old text not found",
                )
            )
            continue

        # Only replace the verified recommendation.
        # Existing T-31 safety note remains untouched.
        document["text"] = text.replace(
            old_text,
            new_text,
            1,
        )

        updated.append(document_id)

    return updated, failed


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 72)
    print("T-31 VERIFIED KNOWLEDGE BASE CORRECTIONS")
    print("=" * 72)

    documents = load_json(
        DOCUMENTS_FILE
    )

    print(
        f"\nLoaded documents : {len(documents)}"
    )

    print("\nCreating local backup...")
    make_backup()

    updated, failed = apply_corrections(
        documents
    )

    if failed:
        print("\nERROR: Some corrections could not be applied.")

        for document_id, reason in failed:
            print(
                f"  - {document_id}: {reason}"
            )

        print(
            "\nNo changes were saved because the correction "
            "set was not applied completely."
        )

        return

    save_json(
        DOCUMENTS_FILE,
        documents,
    )

    print("\nCorrections applied successfully:")

    for document_id in updated:
        print(f"  - {document_id}")

    print("\n" + "=" * 72)
    print("CORRECTION SUMMARY")
    print("=" * 72)

    print(
        f"Documents corrected : {len(updated)}"
    )

    print("\nBig Onion:")
    print("  Thiram 80%                         -> 5 g/kg")
    print("  Captan 80%                         -> 4 g/kg")
    print("  Captan 50%                         -> 6 g/kg")
    print(
        "  Thiophanate methyl 50% + "
        "Thiram 30% WP -> 4 g/kg"
    )

    print("\nMungbean:")
    print("  Captan                             -> 3 g/kg")
    print("  Thiram                             -> 2 g/kg")
    print(
        "  Thiram + Thiophanate methyl       -> 2 g/kg"
    )

    print(
        "\nExisting T-31 chemical safety notes "
        "were preserved."
    )

    print("\nT-31 verified corrections complete.")


if __name__ == "__main__":
    main()