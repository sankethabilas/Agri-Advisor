# Agri-Advisor Data Layer Documentation

## 1. Data Layer Overview

The Agri-Advisor data layer combines structured JSON knowledge bases with a ChromaDB vector store.

The structured JSON files store disease information, treatment recommendations, crop varieties, best practices, and seasonal cultivation guidance. The `documents.json` corpus contains source-attributed text documents used by the Retrieval-Augmented Generation (RAG) component.

The main data flow is:

```text
Structured agricultural sources
        ↓
JSON knowledge-base files
        ↓
documents.json
        ↓
SentenceTransformer embeddings
        ↓
ChromaDB vector store
        ↓
RAG retrieval
        ↓
Source-attributed advisory context
```

The final verified RAG corpus currently contains **303 documents**.

---

## 2. Knowledge Base Files

The project uses the following JSON data files under `knowledge_base/`.

| File | Top-level structure | Records | Purpose |
|---|---|---:|---|
| `documents.json` | List | 303 | Main source-attributed corpus used for semantic RAG retrieval |
| `disease_kb.json` | Dictionary | 51 | Structured disease information used by the Disease Agent |
| `treatment_db.json` | Dictionary | 51 | Chemical, organic, cultural and preventive treatment guidance |
| `crop_db.json` | Dictionary | 5 | Structured crop variety information |
| `best_practices.json` | Dictionary | 5 | Crop advisory practices such as planting, fertilizer and irrigation |
| `seasonal_calendar.json` | Dictionary | 3 | Maha, Yala and year-round crop planting windows |

Other files in the `knowledge_base/` directory include:

```text
data_loader.py
disease_kb.py
sources.md
source_tracking.md
```

`data_loader.py` and `disease_kb.py` are Python implementation files rather than JSON data sources.

`source_tracking.md` contains source/provenance tracking information and is useful when maintaining or verifying the knowledge base.

---

# 3. JSON Data Schemas

## 3.1 `documents.json`

### Purpose

`documents.json` is the main corpus used by the RAG component.

Each record represents one source-attributed agricultural knowledge document that can be embedded and stored in ChromaDB.

### Top-Level Structure

```text
list[document]
```

Final record count:

```text
303 documents
```

### Document Schema

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Unique identifier for the document |
| `title` | string | Yes | Human-readable document title |
| `text` | string | Yes | Full searchable text used during retrieval |
| `crop` | string | Yes | Crop associated with the document |
| `category` | string | Yes | Knowledge category such as disease, pest, cultivation or fertilizer |
| `language` | string | Yes | Language code such as `en` or `si` |
| `source_id` | string | Yes | Stable identifier for the source or source record |
| `source` | string | Yes | Human-readable source attribution |
| `region` | string | Yes | Geographic applicability |
| `season` | string | Yes | Seasonal applicability |

All **303 records** contain all ten required fields.

### Example

```json
{
  "id": "R-D-001",
  "title": "Rice Blast",
  "text": "Rice blast is a fungal disease of rice caused by Magnaporthe grisea...",
  "crop": "rice",
  "category": "disease",
  "language": "en",
  "source_id": "R-D-001",
  "source": "Sri Lanka Department of Agriculture - Rice Blast",
  "region": "Sri Lanka",
  "season": "general"
}
```

### Important Notes

The `text` field is the primary natural-language content used for semantic retrieval.

The remaining fields provide metadata that can be used for filtering, attribution, classification, and result presentation.

`id` values must remain unique because they are also used when storing documents in the vector database.

---

## 3.2 `disease_kb.json`

### Purpose

`disease_kb.json` stores structured disease records used by the Disease Agent for symptom matching, disease identification, ranking and source attribution.

### Top-Level Structure

```text
dict[disease_key → disease_record]
```

Final record count:

```text
51 diseases
```

Example top-level keys include:

```text
rice_blast
rice_sheath_blight
rice_brown_spot
rice_false_smut
rice_leaf_scald
```

### Disease Schema

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Stable disease/document identifier |
| `name` | string | Yes | Human-readable disease name |
| `scientific_name` | string | Yes | Scientific name of the causal organism |
| `disease_type` | string | Yes | Disease category such as fungal, bacterial or viral |
| `crop` | string | Yes | Crop affected by the disease |
| `symptoms` | list[string] | Yes | Symptoms used for disease matching |
| `severity` | object | Yes | Structured severity information |
| `region` | list[string] | Yes | Geographic regions where the disease information applies |
| `source` | object | Yes | Source attribution |

### `severity` Object

The `severity` field is an object containing:

| Field | Type | Description |
|---|---|---|
| `level` | string | Severity classification |
| `basis` | string | Explanation or basis for the assigned severity |

Example:

```json
{
  "level": "high",
  "basis": "derived from documented disease impact"
}
```

### `source` Object

The source object contains:

| Field | Type | Description |
|---|---|---|
| `source_id` | string | Stable source identifier |
| `name` | string | Human-readable source name |

Example:

```json
{
  "source_id": "R-D-001",
  "name": "Sri Lanka Department of Agriculture - Rice Blast"
}
```

### `symptoms`

The `symptoms` field is:

```text
list[string]
```

Example:

```json
[
  "spindle-shaped leaf spots",
  "brown or reddish-brown lesion margins",
  "ashy lesion centres"
]
```

### `region`

The `region` field is:

```text
list[string]
```

Example:

```json
[
  "Sri Lanka"
]
```

---

## 3.3 `treatment_db.json`

### Purpose

`treatment_db.json` stores disease-management recommendations corresponding to diseases defined in `disease_kb.json`.

The database contains **51 treatment records**, matching the 51 disease records.

### Top-Level Structure

```text
dict[disease_key → treatment_record]
```

The dictionary keys correspond to disease keys such as:

```text
rice_blast
rice_sheath_blight
rice_brown_spot
```

### Treatment Schema

| Field | Type | Required | Description |
|---|---|---|---|
| `disease` | string | Yes | Human-readable disease name |
| `chemical` | list[string] | Yes | Chemical treatment recommendations |
| `organic` | list[string] | Yes | Organic treatment recommendations |
| `cultural` | list[string] | Yes | Cultural management practices |
| `prevention` | list[string] | Yes | Preventive practices |
| `source` | object | Yes | Source attribution |
| `safety_caveat` | string | No | Current pesticide-registration and product-label safety guidance |

### Treatment List Types

All four treatment categories contain strings:

```text
chemical   → list[string]
organic    → list[string]
cultural   → list[string]
prevention → list[string]
```

Final non-empty record counts are:

```text
chemical non-empty records   : 21
organic non-empty records    : 8
cultural non-empty records   : 33
prevention non-empty records : 37
```

### `source` Object

```json
{
  "source_id": "R-D-001",
  "name": "Sri Lanka Department of Agriculture - Rice Blast"
}
```

The source object contains:

| Field | Type |
|---|---|
| `source_id` | string |
| `name` | string |

### `safety_caveat`

The `safety_caveat` field is optional.

It currently exists in:

```text
21 / 51 records
```

These are records containing chemical recommendations that require explicit pesticide safety guidance.

The caveat instructs users to follow current Sri Lankan pesticide registration and product-label information, including:

- dosage,
- personal protective equipment,
- re-entry interval,
- pre-harvest interval, and
- current Department of Agriculture / Registrar of Pesticides guidance.

---

## 3.4 `crop_db.json`

### Purpose

`crop_db.json` stores structured crop-variety recommendations used by the Crop Advisory Agent.

### Top-Level Structure

```text
dict[crop_key → crop_record]
```

Current structured crop count:

```text
5 crops
```

Current crop keys are:

```text
rice
chilli
maize
finger_millet
mungbean
```

### Crop Schema

| Field | Type | Required | Description |
|---|---|---|---|
| `crop` | string | Yes | Human-readable crop name |
| `varieties` | list[object] | Yes | List of recommended crop varieties |

### Variety Schema

Each variety object contains:

| Field | Type | Description |
|---|---|---|
| `name` | string | Variety name |
| `region` | list | Regions where the variety is suitable |
| `season` | list | Suitable cultivation seasons |
| `suitability_reasons` | list | Reasons the variety is recommended |
| `source` | object | Source attribution |

The structure is conceptually:

```text
crop_db
└── <crop>
    ├── crop
    └── varieties[]
        ├── name
        ├── region
        ├── season
        ├── suitability_reasons
        └── source
```

### Variety Source Object

The nested source object contains:

| Field | Type |
|---|---|
| `source_id` | string |
| `name` | string |

Example structure:

```json
{
  "source_id": "R-D-001",
  "name": "Sri Lanka Department of Agriculture - Rice Blast"
}
```

---

## 3.5 `best_practices.json`

### Purpose

`best_practices.json` stores structured crop-management recommendations used by the Crop Advisory Agent.

These recommendations cover multiple stages of crop cultivation.

### Top-Level Structure

```text
dict[crop_key → best_practice_record]
```

Current record count:

```text
5 crops
```

Current top-level crop keys include:

```text
rice
tomato
chilli
maize
mungbean
```

### Best-Practice Schema

| Field | Type | Required | Description |
|---|---|---|---|
| `crop` | string | Yes | Crop name |
| `planting` | list[string] | Yes | Planting guidance |
| `fertilizer` | list[string] | Yes | Fertilizer guidance |
| `irrigation` | list[string] | Yes | Irrigation guidance |
| `pest_disease_management` | list[string] | Yes | Pest and disease management practices |
| `harvesting` | list[string] | Yes | Harvesting recommendations |
| `rotation` | list[string] | Yes | Crop-rotation recommendations |
| `sustainability` | list[string] | Yes | Sustainable farming practices |
| `source` | list[object] | Yes | Source attribution records |
| `worked_example` | object | No | Detailed worked crop-advisory example |

### Final Non-Empty Counts

```text
planting                    : 3/5
fertilizer                  : 5/5
irrigation                  : 4/5
pest_disease_management     : 4/5
harvesting                  : 3/5
rotation                    : 3/5
sustainability              : 4/5
```

The fields remain present even when their lists are empty.

### Source Objects

Each source object contains:

```text
source_id: string
name: string
```

Example:

```json
{
  "source_id": "R-D-001",
  "name": "Sri Lanka Department of Agriculture - Rice Blast"
}
```

---

### Optional `worked_example`

The `worked_example` field currently appears in one crop record.

Its structure is:

```text
worked_example
├── title
├── scenario
├── planting
├── recommended_varieties
├── fertilizer_schedule
├── irrigation
├── harvesting
├── weed_and_crop_management
├── expected_yield
├── source_ids
└── note
```

### `scenario` Object

The scenario object contains:

| Field | Type |
|---|---|
| `crop` | string |
| `region` | string |
| `season` | string |

Example:

```json
{
  "crop": "Maize",
  "region": "Sri Lanka",
  "season": "Maha"
}
```

### `planting` Object

The planting object contains:

| Field | Type | Description |
|---|---|---|
| `window` | string | Recommended planting period |
| `seed_requirement` | string | Seed quantity requirement |
| `spacing` | string | Planting spacing |
| `expected_population` | string | Expected plant population |

Example structure:

```json
{
  "window": "Late September to early October",
  "seed_requirement": "Approximately 15–20 kg per hectare",
  "spacing": "60 cm × 30 cm with one plant per planting point",
  "expected_population": "Approximately 55,555 plants per hectare"
}
```

### `recommended_varieties`

This field contains:

```text
list[object]
```

Each object contains:

| Field | Type |
|---|---|
| `name` | string |
| `type` | string |
| `maturity` | string |
| `expected_yield` | string |

Example:

```json
{
  "name": "Bhadra",
  "type": "open-pollinated",
  "maturity": "105–110 days",
  "expected_yield": "approximately 4 tonnes per hectare"
}
```

### `fertilizer_schedule`

This field contains:

```text
list[object]
```

Each object contains:

| Field | Type |
|---|---|
| `stage` | string |
| `timing` | string |
| `application` | list[string] |

Example:

```json
{
  "stage": "Basal",
  "timing": "Before planting or within 10–14 days after planting",
  "application": [
    "75 kg/ha urea",
    "100 kg/ha concentrated superphosphate",
    "50 kg/ha muriate of potash"
  ]
}
```

### Remaining Worked-Example Fields

The following fields contain lists of strings:

```text
irrigation
harvesting
weed_and_crop_management
```

The worked example also contains:

```text
expected_yield: string
source_ids: list
note: string
```

---

## 3.6 `seasonal_calendar.json`

### Purpose

`seasonal_calendar.json` stores crop planting windows and seasonal cultivation guidance.

### Top-Level Structure

```text
dict[season_key → season_record]
```

Current top-level season records are:

```text
maha
yala
year_round
```

Final record count:

```text
3 season records
```

### Season Schema

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Human-readable season name |
| `description` | string | No | Description of the season |
| `crop_windows` | object | Yes | Crop-specific seasonal planting information |

The `description` field is currently present in two of the three season records.

### `crop_windows` Structure

Each crop key inside `crop_windows` maps to a crop-window object.

Example conceptual structure:

```text
season
└── crop_windows
    ├── rice
    ├── chilli
    ├── cowpea
    ├── finger_millet
    ├── maize
    └── tomato
```

Each crop-window object contains:

| Field | Type | Description |
|---|---|---|
| `planting_window` | list | Recommended planting periods |
| `notes` | list | Additional seasonal guidance |
| `source` | list[object] | Source attribution |

### Crop-Window Source Objects

Each source object contains:

| Field | Type |
|---|---|
| `source_id` | string |
| `name` | string |

Example:

```json
{
  "source_id": "SOURCE-ID",
  "name": "Source publication name"
}
```

---

# 4. Relationships Between Data Files

The structured data files serve different but related purposes.

```text
disease_kb.json
      │
      │ disease key
      ▼
treatment_db.json

crop_db.json
      │
      ├── crop varieties
      │
best_practices.json
      │
      ├── cultivation guidance
      │
seasonal_calendar.json
      │
      └── seasonal guidance

                ↓

documents.json

                ↓

ChromaDB vector index
```

### Disease and Treatment Relationship

`disease_kb.json` and `treatment_db.json` use matching disease keys.

For example:

```text
rice_blast
```

may be used as the top-level key in both files.

The T-31 validation confirmed:

```text
Diseases without treatment record : 0
Treatments without disease record : 0
```

Therefore, all 51 structured disease records have corresponding treatment records.

### Structured Data vs RAG Corpus

The structured files are primarily used by specialized agents such as the Disease Agent and Crop Advisory Agent.

`documents.json` is the text corpus used by the RAG Agent.

The RAG corpus contains more documents than the structured databases because it also stores:

- disease descriptions,
- pests,
- cultivation guidance,
- fertilizer guidance,
- irrigation guidance,
- variety information,
- regional information,
- harvest and storage guidance,
- bilingual documents,
- source-specific reference material.

---

# 5. ChromaDB Vector Store

> This section will be completed after inspecting the current implementation in `scripts/index_knowledge_base.py`.

Topics to document:

- ChromaDB client type
- persistent store path
- collection name
- embedding model
- document IDs
- stored metadata
- embedding text construction
- indexing behaviour
- stale-document handling
- idempotent re-indexing

---

# 6. Retrieval Pipeline

> This section will be completed after inspecting `agents/rag/agent.py` and `agents/rag/keyword_search.py`.

Topics to document:

- query preprocessing
- query encoding
- semantic search
- top-K retrieval
- metadata filtering
- distance-to-similarity conversion
- confidence ranking
- unfiltered retry
- keyword fallback
- hybrid ranking
- exact-title rescue
- final context/source construction

---

# 7. Knowledge Base Source Publications

> This section will be completed from the verified T-31 source registry and `source_tracking.md`.

The final T-31 audit recorded:

```text
Unique literal source names : 17
Unique source IDs           : 90
Missing source records      : 0
```

Major verified source families include:

- Department of Agriculture, Sri Lanka
- Horticultural Crops Research and Development Institute (HORDI)
- Rice Research and Development Institute (RRDI)
- Field Crops Research and Development Institute (FCRDI)
- Office of the Registrar of Pesticides (ROP)
- International Rice Research Institute (IRRI)

---

# 8. Knowledge Base Update Procedure

> This section will be completed after confirming the current indexing implementation.

The intended update workflow is:

```text
Edit or add source-backed JSON data
        ↓
validate JSON structure
        ↓
run knowledge-base QA
        ↓
re-index ChromaDB
        ↓
run retrieval tests
        ↓
run regression tests
```

---

# 9. Re-indexing Procedure

The final re-indexing command will be documented from the current indexing implementation.

The command currently used during T-31 was:

```bash
python scripts/index_knowledge_base.py
```

The final T-31 indexing result was:

```text
Source document count  : 303
ChromaDB document count: 303
```

---

# 10. Adding a New Disease

> A complete worked developer procedure will be added after documenting the final indexing and retrieval implementation.

The completed guide will cover:

1. adding the disease to `disease_kb.json`,
2. adding management recommendations to `treatment_db.json`,
3. adding source-attributed RAG documents to `documents.json`,
4. adding pesticide safety guidance when applicable,
5. validating the data,
6. re-indexing ChromaDB,
7. testing retrieval, and
8. running the full regression suite.

---

# 11. Coverage Statistics

Final T-31 knowledge-base statistics:

```text
Corpus documents       : 303
Disease records        : 51
Treatment records      : 51
Normalized crop groups : 12
Unique source names    : 17
Unique source IDs      : 90
Missing source records : 0
Duplicate IDs          : 0
```

## Crop Coverage

| Crop | Documents |
|---|---:|
| Chilli | 64 |
| Maize | 40 |
| Legumes | 35 |
| Big Onion | 34 |
| Finger Millet | 24 |
| Soybean | 22 |
| Sesame | 16 |
| Mungbean | 16 |
| Cowpea | 15 |
| Tomato | 14 |
| Rice | 13 |
| Peanut | 10 |

All 12 crop groups have non-zero coverage.

Sesame coverage was improved during T-31 from:

```text
4 documents → 16 documents
```

## Regional Coverage

Final region metadata included:

```text
Sri Lanka                           296 documents
general                               5 documents
Dry and Intermediate Zones, Sri Lanka 2 documents
```

Detected agroclimatic references included:

```text
Dry Zone          : 8 documents
Wet Zone          : 5 documents
Intermediate Zone : 8 documents
```

All three major Sri Lankan agroclimatic zones required by T-31 are represented.

## Chemical Safety Coverage

Final safety audit:

```text
Records with chemical recommendations : 21
Records with numeric dosage            : 10
Numeric dosage without safety caveat   : 0

Corpus pesticide dosage documents      : 15
Dosage documents without safety caveat : 0
```

---

# 12. Validation and Testing

The following scripts are used to validate the knowledge-base and retrieval layers:

```text
scripts/audit_t31_kb.py
scripts/index_knowledge_base.py
scripts/test_retrieval.py
scripts/test_rag_quality.py
scripts/test_t23_fallback.py
```

Additional JSON-specific validation scripts include:

```text
scripts/validate_best_practices.py
scripts/validate_crop_db.py
scripts/validate_disease_kb.py
scripts/validate_seasonal_calendar.py
scripts/validate_treatment_db.py
```

After the final T-31 knowledge-base changes, the complete project regression suite was executed using:

```bash
python -m pytest -v
```

Final result:

```text
216 tests collected
216 passed
0 failed
1 deprecation warning
```

The warning was related to Starlette `TestClient` / `httpx` compatibility and did not affect test success.

---

# 13. Known Data-Layer Limitations

The current data layer has several known limitations.

1. Crop coverage is not perfectly balanced. Peanut, Rice, Tomato and Cowpea have fewer documents than higher-coverage crops such as Chilli and Maize.

2. Most corpus documents use broad `Sri Lanka` region metadata instead of detailed agroclimatic-zone metadata.

3. Source names are valid but not fully normalized because publication-specific, year-specific and Sinhala/English labels are retained for provenance.

4. Pesticide recommendations can change over time. Current Sri Lankan registration and product-label instructions must take precedence over historical recommendations stored in the knowledge base.

5. `test_rag_quality.py` requires manual relevance review for its 15-query benchmark rather than automatically calculating the final relevance score.

---

# 14. Current Documentation Status

The JSON schema portion of T-36 is complete.

```text
T-36.1 JSON schemas                  COMPLETE
T-36.2 ChromaDB documentation        PENDING
T-36.3 Retrieval documentation       PENDING
T-36.4 Source publication list       PENDING
T-36.5 Re-index/update procedure     PARTIAL
T-36.6 Coverage statistics           COMPLETE
```

The next implementation files to inspect are:

```text
scripts/index_knowledge_base.py
agents/rag/agent.py
agents/rag/keyword_search.py
```

These files will be used to complete the remaining ChromaDB, retrieval, fallback and maintenance sections.