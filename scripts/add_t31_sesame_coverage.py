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
        / f"documents_before_sesame_coverage_{timestamp}.json"
    )

    shutil.copy2(
        DOCUMENTS_FILE,
        backup_path,
    )

    print(f"Backup created: {backup_path}")


# ---------------------------------------------------------
# Verified Sesame Documents
#
# Source:
# Sri Lanka Department of Agriculture
# Field Crops - Sesame
# ---------------------------------------------------------

NEW_DOCUMENTS = [

    # =====================================================
    # 1. Climate and Soil
    # =====================================================

    {
        "id": "SS-C-001-EN",
        "title": "Climate and Soil Requirements for Sesame",
        "text": (
            "Sesame (Sesamum indicum L.) is suitable for cultivation "
            "in the Dry and Intermediate Zones of Sri Lanka. The "
            "optimum temperature range is approximately 25–30°C. "
            "Light rainfall is beneficial during early growth, "
            "germination, flowering and pod development, while heavy "
            "rain can adversely affect crop growth. Fertile, "
            "well-drained, light-textured sandy loam soil is preferred. "
            "Poorly drained and saline soils are unsuitable, while "
            "well-drained uplands are particularly suitable."
        ),
        "crop": "Sesame",
        "category": "Climate and Soil",
        "language": "en",
        "source": "Department of Agriculture, Sri Lanka",
        "source_id": "SS-C-001",
        "region": "Dry and Intermediate Zones, Sri Lanka",
        "season": "general",
    },

    {
        "id": "SS-C-001-SI",
        "title": "තල වගාව සඳහා දේශගුණික හා පාංශු අවශ්‍යතා",
        "text": (
            "තල (Sesamum indicum L.) ශ්‍රී ලංකාවේ වියළි හා අතරමැදි "
            "කලාපවල සාර්ථකව වගා කළ හැකිය. වගාව සඳහා ප්‍රශස්ත "
            "උෂ්ණත්ව පරාසය සෙල්සියස් අංශක 25–30 පමණ වේ. "
            "මුල් වර්ධන අවධියේ, බීජ ප්‍රරෝහණයේ, මල් පිපීමේ සහ "
            "කරල් වර්ධනය වන අවධියේ මඳ වැසි හිතකර වන අතර තද වැසි "
            "බෝග වර්ධනයට අහිතකර වේ. සාරවත්, හොඳින් ජලය බැස යන "
            "වැලිමය ලෝම පස වඩාත් සුදුසු අතර ජලවහනය දුර්වල හෝ "
            "ලවණ සහිත පස සුදුසු නොවේ."
        ),
        "crop": "තල",
        "category": "Climate and Soil",
        "language": "si",
        "source": "ශ්‍රී ලංකා කෘෂිකර්ම දෙපාර්තමේන්තුව",
        "source_id": "SS-C-001",
        "region": "Dry and Intermediate Zones, Sri Lanka",
        "season": "general",
    },

    # =====================================================
    # 2. Varieties, Seed Requirement and Spacing
    # =====================================================

    {
        "id": "SS-C-002-EN",
        "title": "Recommended Sesame Varieties, Seed Requirement and Spacing",
        "text": (
            "Recommended sesame varieties include Uma, Malee and "
            "ANKSE3. Uma matures in approximately 70–75 days with a "
            "potential yield of about 1,600–1,700 kg per hectare. "
            "Malee matures in approximately 80–85 days with a "
            "potential yield of about 1,700–1,800 kg per hectare. "
            "ANKSE3 matures in approximately 90–100 days with a "
            "potential yield of about 1,400–1,500 kg per hectare. "
            "Seed requirement is approximately 7 kg per hectare for "
            "broadcasting and 5 kg per hectare for row seeding. "
            "For row planting, spacing of approximately 30 cm between "
            "rows and 15 cm between plants is recommended."
        ),
        "crop": "Sesame",
        "category": "Variety",
        "language": "en",
        "source": "Department of Agriculture, Sri Lanka",
        "source_id": "SS-C-002",
        "region": "Sri Lanka",
        "season": "general",
    },

    {
        "id": "SS-C-002-SI",
        "title": "තල නිර්දේශිත ප්‍රභේද, බීජ අවශ්‍යතාවය සහ පරතරය",
        "text": (
            "තල සඳහා නිර්දේශිත ප්‍රභේද අතර උමා, මලී සහ ANKSE3 "
            "ඇතුළත් වේ. උමා ප්‍රභේදය දින 70–75 පමණ කාලයකින් "
            "පරිණත වන අතර හෙක්ටයාරයකට කිලෝග්‍රෑම් 1,600–1,700 "
            "පමණ විභව අස්වැන්නක් ලබා දිය හැකිය. මලී දින 80–85 "
            "පමණ සහ ANKSE3 දින 90–100 පමණ කාලයකින් පරිණත වේ. "
            "විසුරුවා වැපිරීම සඳහා හෙක්ටයාරයකට බීජ කිලෝග්‍රෑම් "
            "7 ක් පමණද පේළි ක්‍රමයට සිටුවීම සඳහා කිලෝග්‍රෑම් "
            "5 ක් පමණද අවශ්‍ය වේ. පේළි අතර සෙ.මී. 30 ක් සහ "
            "පැළ අතර සෙ.මී. 15 ක් පමණ පරතරයක් පවත්වා ගත යුතුය."
        ),
        "crop": "තල",
        "category": "Variety",
        "language": "si",
        "source": "ශ්‍රී ලංකා කෘෂිකර්ම දෙපාර්තමේන්තුව",
        "source_id": "SS-C-002",
        "region": "Sri Lanka",
        "season": "general",
    },

    # =====================================================
    # 3. Land Preparation and Sowing
    # =====================================================

    {
        "id": "SS-C-003-EN",
        "title": "Sesame Land Preparation and Sowing Time",
        "text": (
            "Land preparation should preferably be carried out with "
            "the rains to improve water-use efficiency. Weeds and "
            "healthy crop residues may be incorporated into the soil "
            "during ploughing, followed by preparation of a fine tilth. "
            "Drainage channels should be provided to prevent water "
            "accumulation. Raised beds or ridges can also improve "
            "drainage. Sesame can be planted from mid-March to early "
            "April for the Yala season and from mid-September to "
            "October for the Maha season. Where the previous sesame "
            "crop was seriously affected by disease, sesame should "
            "not immediately be replanted in the same field."
        ),
        "crop": "Sesame",
        "category": "Land Preparation",
        "language": "en",
        "source": "Department of Agriculture, Sri Lanka",
        "source_id": "SS-C-003",
        "region": "Sri Lanka",
        "season": "Maha and Yala",
    },

    {
        "id": "SS-C-003-SI",
        "title": "තල සඳහා බිම් සැකසීම සහ වගා කාලය",
        "text": (
            "ජල භාවිත කාර්යක්ෂමතාව වැඩි කිරීම සඳහා වර්ෂාව සමඟ "
            "බිම් සැකසීම සුදුසු වේ. වල් පැළෑටි සහ නිරෝගී බෝග "
            "අවශේෂ පසට යට කර පස සියුම්ව සකස් කළ යුතුය. වැඩි "
            "ජලය රැඳී නොසිටීමට නිසි ජලවහන කානු සකස් කළ යුතු "
            "අතර උස් පාත්ති හෝ ඇලි වැටි ක්‍රමයද භාවිතා කළ හැකිය. "
            "යල කන්නයට මාර්තු මැද සිට අප්‍රේල් මුල දක්වාත් "
            "මහ කන්නයට සැප්තැම්බර් මැද සිට ඔක්තෝබර් දක්වාත් "
            "බීජ සිටුවීම සුදුසු වේ. පෙර තල වගාව දැඩි රෝග "
            "ආසාදනයකට ලක්වූ ඉඩමක වහාම නැවත තල වගා කිරීම "
            "සුදුසු නොවේ."
        ),
        "crop": "තල",
        "category": "Land Preparation",
        "language": "si",
        "source": "ශ්‍රී ලංකා කෘෂිකර්ම දෙපාර්තමේන්තුව",
        "source_id": "SS-C-003",
        "region": "Sri Lanka",
        "season": "Maha and Yala",
    },

    # =====================================================
    # 4. Weed and Water Management
    # =====================================================

    {
        "id": "SS-C-004-EN",
        "title": "Sesame Weed and Water Management",
        "text": (
            "The first month after establishment is the critical "
            "period for weed control in sesame. Weeding is recommended "
            "during thinning at approximately two weeks after sowing "
            "and again at about four weeks. Row planting makes weed "
            "management easier. Adequate soil moisture should be "
            "maintained until germination. If soil moisture is low, "
            "irrigation may be supplied approximately every four days "
            "during the first three weeks and thereafter approximately "
            "every 10–12 days until the seeds mature."
        ),
        "crop": "Sesame",
        "category": "Water and Weed Management",
        "language": "en",
        "source": "Department of Agriculture, Sri Lanka",
        "source_id": "SS-C-004",
        "region": "Sri Lanka",
        "season": "general",
    },

    {
        "id": "SS-C-004-SI",
        "title": "තල වගාවේ වල් මර්දනය සහ ජල සම්පාදනය",
        "text": (
            "තල වගාවේ මුල් මාසය වල් පැළෑටි පාලනය සඳහා ඉතා "
            "වැදගත් වේ. බීජ සිටුවා සති දෙකකදී පැළ තුනී කරන "
            "අවස්ථාවේදී සහ සති හතරකදී නැවත වල් මර්දනය කිරීම "
            "නිර්දේශ කර ඇත. බීජ ප්‍රරෝහණය වන තෙක් පසේ ප්‍රමාණවත් "
            "තෙතමනය පවත්වා ගත යුතුය. පසේ තෙතමනය අඩු නම් පළමු "
            "සති තුන තුළ දින හතරකට වරක් පමණද ඉන් පසුව බීජ "
            "පරිණත වන තෙක් දින 10–12 කට වරක් පමණද ජලය "
            "සැපයිය හැකිය."
        ),
        "crop": "තල",
        "category": "Water and Weed Management",
        "language": "si",
        "source": "ශ්‍රී ලංකා කෘෂිකර්ම දෙපාර්තමේන්තුව",
        "source_id": "SS-C-004",
        "region": "Sri Lanka",
        "season": "general",
    },

    # =====================================================
    # 5. Nutrient Management
    # =====================================================

    {
        "id": "SS-F-001-EN",
        "title": "Sesame Organic Nutrient Management",
        "text": (
            "Organic fertilizer is important for maintaining soil "
            "fertility in sesame cultivation. The Department of "
            "Agriculture recommends approximately 6.5 tonnes of "
            "well-decomposed compost per hectare or approximately "
            "3.5 tonnes of cattle manure per hectare during land "
            "preparation or before seed establishment. Soil testing "
            "every three to four seasons is recommended to identify "
            "soil nutrient status and other soil problems."
        ),
        "crop": "Sesame",
        "category": "Fertilizer",
        "language": "en",
        "source": "Department of Agriculture, Sri Lanka",
        "source_id": "SS-F-001",
        "region": "Sri Lanka",
        "season": "general",
    },

    {
        "id": "SS-F-001-SI",
        "title": "තල වගාවේ කාබනික පෝෂක කළමනාකරණය",
        "text": (
            "තල වගාවේ පාංශු සාරවත්භාවය පවත්වා ගැනීම සඳහා "
            "කාබනික පොහොර භාවිතය වැදගත් වේ. හොඳින් දිරාපත් වූ "
            "කොම්පෝස්ට් හෙක්ටයාරයකට ටොන් 6.5 ක් පමණ හෝ ගොම "
            "පොහොර හෙක්ටයාරයකට ටොන් 3.5 ක් පමණ බිම් සැකසීමේදී "
            "හෝ බීජ සිටුවීමට පෙර පසට මිශ්‍ර කිරීම නිර්දේශ කර ඇත. "
            "පසෙහි පෝෂක තත්ත්වය සහ අනෙකුත් පාංශු ගැටලු හඳුනා "
            "ගැනීම සඳහා කන්න 3–4 කට වරක් පාංශු පරීක්ෂාවක් "
            "සිදු කිරීම සුදුසු වේ."
        ),
        "crop": "තල",
        "category": "Fertilizer",
        "language": "si",
        "source": "ශ්‍රී ලංකා කෘෂිකර්ම දෙපාර්තමේන්තුව",
        "source_id": "SS-F-001",
        "region": "Sri Lanka",
        "season": "general",
    },

    # =====================================================
    # 6. Harvest and Storage
    # =====================================================

    {
        "id": "SS-C-005-EN",
        "title": "Sesame Harvesting, Drying and Storage",
        "text": (
            "Sesame is ready for harvesting when the lower leaves "
            "become yellow and the lower pods turn brown and are close "
            "to splitting. The whole plant should be cut near the base "
            "and bundles should be kept upright in shade for about "
            "seven days so that leaves fall and upper pods mature. "
            "Seeds should be collected over a tarpaulin or similar "
            "surface to avoid contamination. The seed should be dried "
            "to approximately 8% moisture and stored in clean polysack "
            "bags under dry and pest-proof conditions."
        ),
        "crop": "Sesame",
        "category": "Harvest and Storage",
        "language": "en",
        "source": "Department of Agriculture, Sri Lanka",
        "source_id": "SS-C-005",
        "region": "Sri Lanka",
        "season": "general",
    },

    {
        "id": "SS-C-005-SI",
        "title": "තල අස්වනු නෙලීම, වියළීම සහ ගබඩා කිරීම",
        "text": (
            "පහළ පත්‍ර කහ පැහැයට හැරී පහළ කරල් දුඹුරු පැහැයට "
            "හැරී පිපිරීමට ආසන්න වන විට තල අස්වනු නෙලීමට සුදුසුය. "
            "සම්පූර්ණ ශාකය පාදයෙන් කපා මිටි බැඳ කරල් ඉහළට සිටින "
            "සේ සෙවනේ දින හතක් පමණ තැබිය යුතුය. බීජවලට වැලි "
            "හෝ වෙනත් අපද්‍රව්‍ය මිශ්‍ර වීම වැළැක්වීම සඳහා "
            "අතුරුණුවක් හෝ ටාපෝලින් භාවිතා කළ යුතුය. බීජ "
            "තෙතමනය සියයට 8 ක් පමණ වන තෙක් වියළා පිරිසිදු "
            "පොලිසැක් මලුවල බහා වියළි සහ පළිබෝධවලින් ආරක්ෂිත "
            "ස්ථානයක ගබඩා කළ යුතුය."
        ),
        "crop": "තල",
        "category": "Harvest and Storage",
        "language": "si",
        "source": "ශ්‍රී ලංකා කෘෂිකර්ම දෙපාර්තමේන්තුව",
        "source_id": "SS-C-005",
        "region": "Sri Lanka",
        "season": "general",
    },
]


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 72)
    print("T-31 SESAME COVERAGE IMPROVEMENT")
    print("=" * 72)

    documents = load_json(DOCUMENTS_FILE)

    existing_ids = {
        document.get("id")
        for document in documents
    }

    conflicts = [
        document["id"]
        for document in NEW_DOCUMENTS
        if document["id"] in existing_ids
    ]

    if conflicts:
        print("\nERROR: These document IDs already exist:")

        for document_id in conflicts:
            print(f"  - {document_id}")

        print("\nNo changes saved.")
        return

    print(f"\nDocuments before : {len(documents)}")

    make_backup()

    documents.extend(NEW_DOCUMENTS)

    save_json(
        DOCUMENTS_FILE,
        documents,
    )

    print(
        f"Documents added  : {len(NEW_DOCUMENTS)}"
    )

    print(
        f"Documents after  : {len(documents)}"
    )

    print("\nAdded Sesame documents:")

    for document in NEW_DOCUMENTS:
        print(
            f"  - {document['id']}: "
            f"{document['title']}"
        )

    print("\nT-31 sesame coverage improvement complete.")


if __name__ == "__main__":
    main()