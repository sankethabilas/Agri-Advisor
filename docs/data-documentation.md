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

The RAG component uses ChromaDB as a persistent local vector database for semantic retrieval.

The indexing implementation is located at:

```text
scripts/index_knowledge_base.py
```

## 5.1 Persistent Storage

The project initializes ChromaDB using:

```python
chromadb.PersistentClient(...)
```

The vector database is stored locally under:

```text
<project-root>/chroma_store
```

The path is constructed as:

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHROMA_STORE_PATH = PROJECT_ROOT / "chroma_store"
```

Using `PersistentClient` means the indexed vector data remains available after the indexing process or application terminates.

The main source corpus is loaded from:

```text
knowledge_base/documents.json
```

---

## 5.2 ChromaDB Collection

The knowledge-base collection is created or opened using:

```python
collection = chroma_client.get_or_create_collection(
    name="agri_knowledge_base",
    embedding_function=embedding_function
)
```

Therefore, the collection name is:

```text
agri_knowledge_base
```

`get_or_create_collection()` allows the application to reuse the existing collection when it is already present.

---

## 5.3 Embedding Model

The project uses the Sentence Transformers model:

```text
all-MiniLM-L6-v2
```

It is configured through ChromaDB using:

```python
embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
```

The embedding model converts natural-language agricultural content into numerical vector representations.

These vectors allow semantically related queries and documents to be compared even when they do not contain exactly the same words.

---

## 5.4 Embedding Text Construction

The raw `text` field from `documents.json` is not embedded by itself.

Before embedding, the indexer creates a metadata-enriched representation containing:

```text
Title
Crop
Category
Region
Season
Content
```

The format is:

```text
Title: <title>
Crop: <crop>
Category: <category>
Region: <region>
Season: <season>
Content: <document text>
```

This is produced by:

```python
build_embedding_text(document)
```

The purpose is to make crop, category, region and seasonal information available to the semantic representation instead of relying only on the body text.

For example, conceptually:

```text
Title: Rice Blast
Crop: rice
Category: disease
Region: Sri Lanka
Season: general
Content: Rice blast is a fungal disease...
```

The metadata-enriched text is used only to generate the embedding.

The original `text` field from the source document is stored separately as the ChromaDB document and is what is returned to the RAG layer.

---

## 5.5 Stored ChromaDB Record Structure

Each indexed knowledge-base document consists conceptually of:

```text
ChromaDB record
├── id
├── embedding
├── document
└── metadata
```

### ID

The ChromaDB ID is taken directly from:

```text
documents.json → id
```

The indexer converts it to a string:

```python
ids.append(str(document["id"]))
```

Document IDs must therefore remain unique.

### Document

The stored document body is:

```python
document["text"]
```

This preserves the original agricultural knowledge text separately from the metadata-enriched text used to construct the embedding.

### Embedding

The embedding is generated from:

```python
build_embedding_text(document)
```

using:

```text
all-MiniLM-L6-v2
```

### Metadata

Each ChromaDB record stores the following metadata:

| Metadata Field | Source |
|---|---|
| `title` | `document["title"]` |
| `crop` | `document["crop"]` |
| `category` | `document["category"]` |
| `language` | `document["language"]` |
| `source` | `document["source"]` |
| `source_id` | `document["source_id"]` |
| `region` | `document["region"]` |
| `season` | `document["season"]` |
| `index_version` | Static index-version identifier |

The current index version is:

```text
t23_metadata_enriched_v1
```

Default values are also provided by the indexer for selected metadata fields:

```text
language  → en
source_id → document id if source_id is absent
region    → Sri Lanka
season    → general
```

---

## 5.6 Indexing Process

The indexing process follows these stages:

```text
knowledge_base/documents.json
             ↓
        Load JSON
             ↓
     Read each document
             ↓
Build metadata-enriched text
             ↓
Generate MiniLM embeddings
             ↓
Remove stale ChromaDB records
             ↓
     Upsert current records
             ↓
 Verify indexed document count
```

### Step 1 — Load the Corpus

The indexer reads:

```text
knowledge_base/documents.json
```

using UTF-8:

```python
json.load(...)
```

UTF-8 is required because the corpus can contain multilingual content including Sinhala text.

---

### Step 2 — Prepare IDs, Documents and Metadata

For every source document, the indexer prepares:

```text
ids
texts
embedding_texts
metadatas
```

Where:

```text
ids             = unique document IDs
texts           = original document text
embedding_texts = metadata-enriched retrieval text
metadatas       = structured metadata
```

---

### Step 3 — Remove Stale Documents

Before inserting the current corpus, the indexer retrieves the IDs already stored in ChromaDB:

```python
existing = collection.get()
```

It then compares them with the IDs currently present in `documents.json`.

Conceptually:

```text
stale IDs =
existing ChromaDB IDs
-
current documents.json IDs
```

Any stale records are deleted:

```python
collection.delete(ids=stale_ids)
```

This prevents deleted knowledge-base records from remaining searchable in the vector database.

---

### Step 4 — Generate Embeddings

Embeddings are generated for all metadata-enriched document texts using:

```python
embeddings = embedding_function(embedding_texts)
```

The generated vectors correspond to the current contents of the JSON corpus.

---

### Step 5 — Upsert Documents

Documents are written using:

```python
collection.upsert(...)
```

The indexer provides:

```text
ids
embeddings
documents
metadatas
```

`upsert` means:

```text
ID does not exist → INSERT
ID already exists → UPDATE
```

Therefore, re-running the indexer updates existing records rather than creating duplicate records with the same ID.

---

## 5.7 Index Synchronization

The combination of:

```text
stale-record deletion
+
upsert
```

keeps the persistent ChromaDB collection synchronized with the current `documents.json` corpus.

This handles three common update cases:

| Change in `documents.json` | Indexing Behaviour |
|---|---|
| New ID added | Inserted into ChromaDB |
| Existing ID modified | Existing ChromaDB record updated |
| Existing ID removed | Stale ChromaDB record deleted |

---

## 5.8 Index Integrity Check

At the end of indexing, the script compares:

```text
number of documents in documents.json
```

with:

```text
collection.count()
```

If the counts differ, indexing fails with:

```python
ValueError(
    "ChromaDB document count does not match documents.json."
)
```

This provides a basic integrity check that every current source document is represented in the vector store.

During the final T-31 re-indexing:

```text
Source document count   : 303
ChromaDB document count : 303
```

Therefore, the source corpus and vector-store document counts were synchronized.

---

## 5.9 Running the Indexer

From the project root, rebuild or update the vector index using:

```bash
python scripts/index_knowledge_base.py
```

The expected final output includes:

```text
Loaded 303 documents ...
No stale indexed documents found.

Indexing complete.
Source document count : 303
ChromaDB document count: 303
```

The exact stale-document message may differ if records were removed from `documents.json`.

---

# 6. Retrieval Pipeline

The RAG retrieval implementation is primarily located in:

```text
agents/rag/agent.py
agents/rag/keyword_search.py
```

The retrieval layer combines semantic vector retrieval with metadata filtering, similarity thresholds, keyword fallback, hybrid re-ranking, exact-title rescue and an unfiltered semantic retry.

The overall retrieval flow is:

```text
Farmer query
      ↓
Query encoding
      ↓
Semantic ChromaDB search
      ↓
Optional crop/category filters
      ↓
Top-K candidates
      ↓
L2 distance → similarity
      ↓
Minimum-score filtering
      ↓
Is semantic confidence sufficient?
      │
      ├── No
      │    ↓
      │ Keyword fallback
      │    ↓
      │ Hybrid keyword + semantic ranking
      │
      └── Yes
           ↓
        Exact-title rescue check
              ↓
If crop-filtered retrieval still has no source
              ↓
      Unfiltered semantic retry
              ↓
        Build source objects
              ↓
         Build RAG context
              ↓
       RagRetrieveResponse
```

---

## 6.1 Query Encoding

The retrieval process begins in:

```python
RAGAgent.retrieve(...)
```

The farmer's natural-language query is converted into an embedding by:

```python
query_embedding = self.encode_query(request.query)
```

`encode_query()` uses the same Sentence Transformer embedding function used during indexing:

```text
all-MiniLM-L6-v2
```

Conceptually:

```text
"My tomato plants have late blight"
                ↓
      all-MiniLM-L6-v2
                ↓
        numerical vector
```

Using the same embedding model for indexed documents and incoming queries allows ChromaDB to compare them in the same vector space.

---

## 6.2 Semantic Search

The encoded query is passed to:

```python
self.search(...)
```

The semantic search receives:

```text
query embedding
top_k
optional crop filter
optional category filter
```

The ChromaDB query uses:

```python
collection.query(
    query_embeddings=query_embedding,
    n_results=top_k,
    ...
)
```

The `search()` method has a default:

```text
top_k = 3
```

However, during API retrieval the actual value is taken from:

```text
request.top_k
```

Therefore, the API request controls the number of semantic candidates requested.

---

## 6.3 Crop Filtering

Semantic retrieval supports optional crop filtering.

The system first normalizes crop aliases using:

```python
normalize_crop_filter(...)
```

Current aliases include:

```text
paddy         → rice / Rice / paddy / Paddy
rice          → rice / Rice / paddy / Paddy

chilli        → chilli / Chilli / chili / Chili
chili         → chilli / Chilli / chili / Chili

tomato        → tomato / Tomato

maize         → maize / Maize / corn / Corn
corn          → maize / Maize / corn / Corn

mungbean      → mungbean / Mungbean / mung bean / Mung Bean

cowpea        → cowpea / Cowpea

finger millet → finger millet / Finger Millet / finger_millet
```

For crops not explicitly listed in the alias map, the system generates several capitalization variants.

When multiple variants exist, ChromaDB filtering uses:

```text
$in
```

For example, conceptually:

```json
{
  "crop": {
    "$in": [
      "rice",
      "Rice",
      "paddy",
      "Paddy"
    ]
  }
}
```

This improves retrieval when farmers use crop synonyms such as `paddy` instead of `rice`.

---

## 6.4 Category Filtering

An optional category filter may also be supplied.

The system creates lowercase, capitalized and title-case variants.

Conceptually:

```text
disease
Disease
```

The filter is applied through ChromaDB metadata using `$in`.

If both crop and category filters are supplied, they are combined using:

```text
$and
```

Therefore, a request such as:

```text
crop = tomato
category = disease
```

restricts the semantic search to records matching both criteria.

---

## 6.5 Top-K Retrieval

The number of candidates requested from ChromaDB is controlled by:

```text
request.top_k
```

The `search()` method defaults to:

```text
3
```

if called directly without another value.

Conceptually:

```text
Query
 ↓
ChromaDB
 ↓
Top 3 candidates
```

The returned candidates include:

```text
IDs
documents
metadata
distances
```

These results are then converted into source objects and confidence values.

---

## 6.6 L2 Distance to Similarity Conversion

ChromaDB returns distance values.

The RAG agent records its vector distance metric as:

```text
l2
```

The system converts the L2 distance into a normalized similarity value using:

```python
similarity = 1.0 - (distance / 2.0)
```

The result is clamped to:

```text
0.0 ≤ similarity ≤ 1.0
```

This is implemented by:

```python
distance_to_similarity(...)
```

Conceptually:

```text
lower L2 distance
      ↓
higher similarity
```

For example:

```text
distance = 0.30

similarity =
1 - (0.30 / 2)

= 0.85
```

A higher similarity therefore represents a stronger semantic match.

---

## 6.7 Semantic Result Filtering

Semantic results are converted into RAG source objects using:

```python
build_sources(...)
```

Each candidate must meet:

```text
request.min_score
```

Results below this minimum similarity are discarded.

Conceptually:

```text
similarity >= min_score
        ↓
       keep

similarity < min_score
        ↓
      discard
```

The method also creates a corresponding confidence list.

---

## 6.8 Semantic Source Structure

Each accepted semantic result is converted into a source object containing fields including:

```text
id
document_id
title
section
content
crop
category
language
source
source_id
author_organization
region
season
score
```

The score is the normalized semantic similarity rounded to four decimal places.

The source attribution is taken primarily from the metadata stored in ChromaDB.

---

## 6.9 Top Semantic Similarity

The system separately records the similarity of the highest-ranked semantic result using:

```python
get_top_similarity(...)
```

The value is stored in:

```python
self.last_top_similarity
```

This value is used to determine whether semantic retrieval is confident enough or whether keyword fallback should be triggered.

---

## 6.10 Semantic Fallback Threshold

The RAG agent has a default fallback threshold of:

```text
0.60
```

configured as:

```python
fallback_threshold=0.60
```

However, the effective threshold also respects the request's minimum score:

```python
effective_fallback_threshold = max(
    self.fallback_threshold,
    request.min_score
)
```

Therefore:

```text
effective fallback threshold
=
max(0.60, request.min_score)
```

For example:

```text
request.min_score = 0.50
effective threshold = 0.60
```

while:

```text
request.min_score = 0.70
effective threshold = 0.70
```

---

## 6.11 When Keyword Fallback Is Triggered

Keyword fallback is triggered when either:

```text
1. No acceptable semantic sources remain
```

or:

```text
2. Top semantic similarity
   <
   effective fallback threshold
```

This is implemented conceptually as:

```text
fallback_required =
    no semantic sources
    OR
    semantic confidence too low
```

When triggered, retrieval changes from:

```text
semantic
```

to:

```text
keyword_fallback
```

if keyword results are available.

The retrieval method is recorded in:

```python
self.last_retrieval_method
```

---

## 6.12 Keyword Query Normalization

Keyword search begins by normalizing text using:

```python
normalize_text(...)
```

The process:

1. converts the string to lowercase,
2. replaces non-alphanumeric characters with spaces,
3. collapses repeated whitespace, and
4. removes leading and trailing spaces.

Conceptually:

```text
"Tomato Late-Blight!"
        ↓
"tomato late blight"
```

---

## 6.13 Keyword Tokenization

The normalized query is tokenized using:

```python
tokenize(...)
```

Common English stop words are removed.

Examples include:

```text
a
an
the
is
are
of
to
in
for
with
and
my
how
what
```

Tokens of one character or less are also discarded.

Conceptually:

```text
"My tomato has late blight"
              ↓
["tomato", "late", "blight"]
```

---

## 6.14 Keyword Scoring

Each document receives a keyword relevance score.

The scoring system uses several components.

### Title Token Overlap

Each matching query/title token contributes:

```text
+4.0
```

This gives title matches the strongest basic token weight.

Example:

```text
query tokens:
tomato, late, blight

title:
Tomato Late Blight
```

produces strong title overlap.

### Body-Text Token Overlap

Each matching query/body token contributes:

```text
+1.0
```

Body matches therefore matter, but title matches receive greater weight.

### Exact Title Phrase Bonus

If the normalized full document title appears inside the query:

```text
+10.0
```

is added.

For example:

```text
Query:
"My tomato plants have tomato late blight"

Title:
"Tomato Late Blight"
```

receives the exact-title bonus.

### Partial Title Phrase Bonus

The searcher also detects multi-word portions of a title inside the query.

When a matching title phrase is found, the bonus is based on phrase length:

```text
number of words × 3.0
```

This helps distinguish diseases with related names.

For example:

```text
Late Blight
```

should favour:

```text
Tomato Late Blight
```

over:

```text
Tomato Early Blight
```

when the farmer explicitly mentions `late blight`.

### Crop Presence Bonus

If the crop name appears as a query token:

```text
+2.0
```

### Category Presence Bonus

If the category appears as a query token:

```text
+1.0
```

---

## 6.15 Keyword Result Selection

Documents with:

```text
keyword score <= 0
```

are discarded.

Remaining candidates are sorted by:

```text
keyword_score descending
```

and only:

```text
top_k
```

results are returned.

---

## 6.16 Keyword Metadata Filtering

Keyword search also supports:

```text
crop_filter
category_filter
```

The implementation performs case-insensitive exact-value comparison.

For example:

```text
document crop = tomato
crop filter   = Tomato
```

matches after both values are converted to lowercase.

Unlike semantic search, the current keyword search implementation does not apply the semantic crop alias map.

Therefore:

```text
semantic filter:
paddy → rice
```

is supported, while keyword fallback expects the stored crop value to match the supplied crop filter directly.

This is a known implementation limitation.

---

## 6.17 Hybrid Keyword + Semantic Re-Ranking

Keyword fallback does not rely on the raw keyword score alone.

After keyword candidates are found, the RAG agent generates an embedding for each candidate's document text.

It then calculates cosine similarity between:

```text
query embedding
```

and:

```text
candidate document embedding
```

using:

```python
cosine_similarity(...)
```

The raw keyword score is first normalized relative to the highest keyword score:

```text
keyword relevance
=
candidate keyword score
/
maximum keyword score
```

A hybrid confidence score is then calculated:

```text
fallback confidence
=
0.70 × keyword relevance
+
0.30 × semantic similarity
```

Therefore, fallback ranking gives:

```text
70% weight → keyword relevance
30% weight → semantic similarity
```

The candidates are re-sorted by this final fallback confidence.

This makes the fallback system hybrid rather than purely keyword-based.

---

## 6.18 Keyword Fallback Source Construction

Keyword candidates are converted into the same general source structure used by semantic retrieval.

Fields include:

```text
id
document_id
title
section
content
crop
category
language
source
source_id
author_organization
region
season
score
```

The final `score` is the hybrid fallback confidence rather than the original keyword score.

This allows semantic and keyword results to use a consistent response structure.

---

## 6.19 Exact-Title Rescue

A second keyword mechanism is used when semantic retrieval is already confident enough that normal fallback was not triggered.

This mechanism is:

```python
keyword_title_rescue(...)
```

Its purpose is to correct cases where semantic similarity returns a reasonable but incorrect top result even though the farmer explicitly mentions a known disease or document title.

The rescue process:

```text
High-confidence semantic result
           ↓
Run keyword search
           ↓
Normalize farmer query
           ↓
Normalize top keyword title
           ↓
Check whether title phrase is explicitly in query
           ↓
Compare semantic top ID with keyword top ID
           ↓
If different, replace semantic ranking
```

---

## 6.20 Title-Matching Rules

The rescue mechanism first checks the full normalized document title.

For example:

```text
Tomato Late Blight
```

It may also remove a crop prefix.

For example:

```text
Tomato Late Blight
        ↓
Late Blight
```

The shortened phrase must contain at least two words.

The rescue is only accepted when the multi-word phrase occurs directly in the normalized query.

This reduces the chance that an unrelated keyword result replaces a valid semantic result.

---

## 6.21 Exact-Title Rescue Trigger

Exact-title rescue runs only when:

```text
normal keyword fallback was NOT required
```

and:

```text
semantic sources exist
```

If the rescued top document differs from the semantic top document, the keyword ranking replaces the semantic ranking.

The retrieval method is then recorded as:

```text
keyword_title_rescue
```

---

## 6.22 Unfiltered Semantic Retry

There is an additional recovery mechanism for strict crop filtering.

If no sources remain after retrieval and a crop filter was supplied, the RAG agent performs another semantic search with:

```text
crop_filter = None
```

The category filter is retained.

Conceptually:

```text
Filtered semantic search
        ↓
No usable source
        ↓
Remove crop restriction
        ↓
Retry semantic search
```

If this retry succeeds, the retrieval method is recorded as:

```text
semantic_unfiltered
```

The purpose is to return grounded agricultural information rather than an empty response when an overly strict crop filter prevents retrieval.

---

## 6.23 Retrieval Method Tracking

The RAG agent records the retrieval strategy used for the most recent request through:

```python
self.last_retrieval_method
```

Possible values in the current implementation include:

```text
semantic
keyword_fallback
keyword_title_rescue
semantic_unfiltered
```

It also records:

```python
self.last_top_similarity
```

which contains the top semantic similarity observed during retrieval.

These values are useful for testing and diagnosing retrieval behaviour.

---

## 6.24 Context Construction

After final sources have been selected, they are converted into an LLM-ready context using:

```python
build_context(...)
```

Each passage is formatted as:

```text
[Document Title]
Document content
```

Multiple passages are separated by blank lines.

Conceptually:

```text
[Rice Leaf Scald]
<retrieved passage>

[Rice Brown Spot]
<retrieved passage>
```

This context can then be passed to the generation layer while retaining structured source information separately.

---

## 6.25 Retrieval Response

The final result is returned as:

```text
RagRetrieveResponse
```

It contains:

```text
context
sources
confidence
metadata
```

The response metadata includes:

```text
total_chunks_retrieved
query_embedding_model
vector_distance_metric
execution_time_ms
```

The current values include:

```text
query_embedding_model  : all-MiniLM-L6-v2
vector_distance_metric : l2
```

Execution time is measured using:

```python
time.perf_counter()
```

and returned in milliseconds.

---

## 6.26 Retrieval Pipeline Summary

The complete current retrieval strategy can be summarized as:

```text
1. Receive farmer query
2. Encode query with all-MiniLM-L6-v2
3. Apply optional crop/category metadata filters
4. Retrieve top-K candidates from ChromaDB
5. Convert L2 distance to similarity
6. Remove candidates below request.min_score
7. Measure top semantic similarity
8. Trigger keyword fallback if semantic confidence is insufficient
9. Hybrid-rank keyword fallback results using:
      70% keyword relevance
      30% semantic similarity
10. If semantic confidence was already high, check exact-title rescue
11. If crop filtering still leaves no source, retry without crop filter
12. Construct source objects
13. Construct RAG context
14. Return context, sources, confidence and retrieval metadata
```

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