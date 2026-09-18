# Knowledge Base Source Tracking

This file tracks the agricultural knowledge documents planned and created for the Agentic AI Agriculture Advisor.

The table is maintained during knowledge-base curation to prevent duplicate documents, missing sources, incorrect categories, and unsupported information.

## Document Tracking Table

| ID | Crop | Category | Topic | Source | Source URL | Verified | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| R-D-001 | Rice | Disease | Bacterial Leaf Blight | Sri Lanka Department of Agriculture | — | ✅ | Planned | Mandatory disease topic |
| R-D-002 | Rice | Disease | Rice Blast | IRRI | — | ✅ | Planned | Disease symptoms and management |
| R-T-001 | Rice | Treatment | Bacterial Leaf Blight – Cultural Management | Sri Lanka Department of Agriculture | — | ✅ | Planned | Management information |
| R-C-001 | Rice | Cultivation | Land Preparation | Sri Lanka Department of Agriculture | — | ⬜ | Planned | Source to be verified |
| T-D-001 | Tomato | Disease | Early Blight | Sri Lanka Department of Agriculture | — | ✅ | Planned | Mandatory disease topic |

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
