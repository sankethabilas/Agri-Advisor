# Knowledge Base Source Tracking

This file tracks the agricultural knowledge documents planned and created for the Agentic AI Agriculture Advisor.

The table is maintained during knowledge-base curation to prevent duplicate documents, missing sources, incorrect categories, and unsupported information.

## Document Tracking Table

| ID | Crop | Category | Topic | Source | Source URL | Verified | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| R-D-001 | Rice | Disease | Rice Blast | Sri Lanka Department of Agriculture | https://doa.gov.lk/rrdi_ricediseases_riceblast/ | ✅ | Completed | Disease symptoms, favourable conditions and management verified |
| R-D-002 | Rice | Disease | Sheath Blight | Sri Lanka Department of Agriculture | https://doa.gov.lk/rrdi_ricediseases_sheathblight/ | ✅ | Completed | Disease symptoms, favourable conditions and management verified |
| R-D-003 | Rice | Disease | Brown Spot | Sri Lanka Department of Agriculture | https://doa.gov.lk/rrdi_ricediseases_brownspot/ | ✅ | Completed | Disease symptoms, favourable conditions and management verified |
| R-D-004 | Rice | Disease | False Smut | Sri Lanka Department of Agriculture | https://doa.gov.lk/rrdi_ricediseases_falsesmut/ | ✅ | Completed | Disease symptoms, favourable conditions and management verified |
| R-D-005 | Rice | Disease | Leaf Scald | Sri Lanka Department of Agriculture | https://doa.gov.lk/rrdi_ricediseases_leafscald/ | ✅ | Completed | Disease symptoms and management verified |
| R-D-006 | Rice | Disease | Sheath Rot | Sri Lanka Department of Agriculture | https://doa.gov.lk/rrdi_ricediseases_sheathrot/ | ✅ | Completed | Disease symptoms, favourable conditions and management verified |
| R-D-007 | Rice | Disease | Narrow Brown Leaf Spot | Sri Lanka Department of Agriculture | https://doa.gov.lk/rrdi_ricediseases_narrowbrownleafspot/ | ✅ | Completed | Disease symptoms and management verified |
| R-D-008 | Rice | Disease | Bacterial Leaf Blight | Sri Lanka Department of Agriculture | https://doa.gov.lk/rrdi_ricediseases_bacterialleafblight/ | ✅ | Completed | Mandatory disease topic; symptoms and management verified |
| R-D-009 | Rice | Disease | Bakanae | IRRI Rice Diseases Online Resource | https://rice-diseases.irri.org/ | ✅ | Completed | Disease symptoms, transmission and prevention verified |
| R-D-010 | Rice | Disease | Stem Rot | IRRI Rice Diseases Online Resource | https://rice-diseases.irri.org/ | ✅ | Completed | Disease symptoms, inoculum sources and disease development verified |
| R-D-011 | Rice | Disease | Bacterial Leaf Streak | IRRI Rice Diseases Online Resource | https://rice-diseases.irri.org/ | ✅ | Completed | Disease symptoms, conditions, transmission and diagnosis verified |
| R-D-012 | Rice | Disease | Grassy Stunt | IRRI Rice Diseases Online Resource | https://rice-diseases.irri.org/ | ✅ | Completed | Viral disease; symptoms, vector transmission and diagnosis verified |
| R-D-013 | Rice | Disease | Ragged Stunt | IRRI Rice Diseases Online Resource | https://rice-diseases.irri.org/ | ✅ | Completed | Viral disease; symptoms, vector transmission and diagnosis verified |


## Status Legend

| Status | Meaning |
|---|---|
| Planned | Topic identified but JSON document has not been completed |
| In Progress | Source has been reviewed and document is being prepared |
| Completed | JSON document has been created and verified |
| Needs Review | Document requires additional source verification |

## Verification Legend

| Symbol | Meaning |
|---|---|
| ✅ | Source verified |
| ⬜ | Not yet verified |
| ⚠️ | Requires additional verification |

## Document ID Convention

IDs follow this format:

`<CROP>-<CATEGORY>-<NUMBER>`

Examples:

- `R-D-001` → Rice – Disease – 001
- `R-T-001` → Rice – Treatment – 001
- `R-C-001` → Rice – Cultivation – 001
- `T-D-001` → Tomato – Disease – 001
- `M-D-001` → Maize – Disease – 001

### Category Codes

| Code | Category |
|---|---|
| D | Disease |
| T | Treatment |
| C | Cultivation |

### Crop Codes

| Code | Crop |
|---|---|
| R | Rice |
| T | Tomato |
| M | Maize |
| CH | Chilli |
| O | Onion |
