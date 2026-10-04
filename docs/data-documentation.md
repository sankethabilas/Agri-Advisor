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

Knowledge-base provenance is maintained in:

```text
knowledge_base/source_tracking.md
```

The tracking table records:

```text
Document ID
Crop
Category
Topic
Source
Source URL
Verification status
Completion status
Notes
```

The current source-tracking registry contains **17 distinct source-resource and URL combinations**.

> Note: Some resources are individual web pages, while others are larger guides or crop-specific publications. For Google Drive sources, the tracking file records the source organization and document URL but does not provide a formal publication title. Descriptive crop-based names are therefore used below rather than inventing titles.

---

## 7.1 Sri Lanka Department of Agriculture — RRDI Rice Disease Resources

The Rice Research and Development Institute (RRDI) pages are used for verified Sri Lankan rice-disease information.

| No. | Resource | Organization | URL |
|---:|---|---|---|
| 1 | Rice Blast | Sri Lanka Department of Agriculture | `https://doa.gov.lk/rrdi_ricediseases_riceblast/` |
| 2 | Sheath Blight | Sri Lanka Department of Agriculture | `https://doa.gov.lk/rrdi_ricediseases_sheathblight/` |
| 3 | Brown Spot | Sri Lanka Department of Agriculture | `https://doa.gov.lk/rrdi_ricediseases_brownspot/` |
| 4 | False Smut | Sri Lanka Department of Agriculture | `https://doa.gov.lk/rrdi_ricediseases_falsesmut/` |
| 5 | Leaf Scald | Sri Lanka Department of Agriculture | `https://doa.gov.lk/rrdi_ricediseases_leafscald/` |
| 6 | Sheath Rot | Sri Lanka Department of Agriculture | `https://doa.gov.lk/rrdi_ricediseases_sheathrot/` |
| 7 | Narrow Brown Leaf Spot | Sri Lanka Department of Agriculture | `https://doa.gov.lk/rrdi_ricediseases_narrowbrownleafspot/` |
| 8 | Bacterial Leaf Blight | Sri Lanka Department of Agriculture | `https://doa.gov.lk/rrdi_ricediseases_bacterialleafblight/` |

These resources support source IDs including:

```text
R-D-001
R-D-002
R-D-003
R-D-004
R-D-005
R-D-006
R-D-007
R-D-008
```

They contain disease symptoms, favourable conditions and management information.

---

## 7.2 IRRI Rice Diseases Online Resource

| No. | Resource | Organization | URL |
|---:|---|---|---|
| 9 | Rice Diseases Online Resource | International Rice Research Institute (IRRI) | `https://rice-diseases.irri.org/` |

This resource is used for rice disease records including:

```text
R-D-009  Bakanae
R-D-010  Stem Rot
R-D-011  Bacterial Leaf Streak
R-D-012  Grassy Stunt
R-D-013  Ragged Stunt
```

The source provides information such as:

- disease symptoms,
- transmission,
- disease development,
- vectors,
- prevention, and
- diagnosis.

---

## 7.3 HORDI Tomato Resource

| No. | Resource | Organization | URL |
|---:|---|---|---|
| 10 | HORDI Tomato Crop Resource | Sri Lanka Department of Agriculture | `https://doa.gov.lk/hordi-crop-tomato/` |

This resource supports tomato disease and cultivation records including:

```text
T-D-001 through T-D-013
T-C-001
```

Topics include:

- damping-off,
- early blight,
- late blight,
- target spot,
- powdery mildew,
- anthracnose,
- Septoria leaf spot,
- collar and root rot,
- bacterial wilt,
- Yellow Leaf Curl Virus,
- Curly Top Virus,
- Spotted Wilt Virus,
- Cucumber Mosaic Virus, and
- tomato cultivation and management.

---

## 7.4 Field Crop Disease, Pest and Nutrient Identification Guide

| No. | Resource | Organization | URL |
|---:|---|---|---|
| 11 | Field Crop Disease, Pest and Nutrient Identification Guide | Sri Lanka Department of Agriculture | `https://doa.gov.lk/wp-content/uploads/2021/01/Field-Crop-Disease-Pest-and-Nutrient-Identification-Guide.pdf` |

This guide is one of the major multi-crop references used by the knowledge base.

It supports disease, pest and management records for crops including:

```text
Chilli
Big Onion
Maize
Finger Millet
Legumes
Peanut
Sesame
```

Examples of topics sourced from the guide include:

- chilli leaf curl complex,
- chilli anthracnose,
- chilli bacterial wilt,
- big onion pests and diseases,
- maize pests and diseases,
- finger millet pests and disease,
- legume pests and diseases,
- peanut pests and diseases, and
- sesame pests and diseases.

---

## 7.5 Big Onion Cultivation Publication

| No. | Resource | Organization | URL |
|---:|---|---|---|
| 12 | Big Onion cultivation reference | Sri Lanka Department of Agriculture | `https://drive.google.com/file/d/1-hCIhB4W4b8dR5K2Its4rg9fpC59oKZk/view?usp=sharing` |

This source supports Big Onion crop-management topics including:

```text
O-C-001  Climate and soil requirements
O-C-002  Recommended varieties
O-C-003  Season and seed requirement
O-C-004  Nursery management
O-C-005  Seed treatment and sowing
O-C-006  Field preparation and planting
O-F-001  Fertilizer management
O-C-007  Water and weed management
O-C-008  Harvest and storage
```

---

## 7.6 Maize Cultivation Publication

| No. | Resource | Organization | URL |
|---:|---|---|---|
| 13 | Maize cultivation reference | Sri Lanka Department of Agriculture | `https://drive.google.com/file/d/1ftv-3IiDLtZyVhrfcRqN14D6B6RDiT9y/view?usp=sharing` |

This source supports Maize crop-management topics including:

```text
MZ-C-001  Introduction and general information
MZ-C-002  Climate and soil requirements
MZ-C-003  Land preparation and planting
MZ-C-004  Recommended varieties
MZ-C-005  Seed requirement and spacing
MZ-F-001  Fertilizer management
MZ-C-006  Water and weed management
MZ-C-007  Harvesting
MZ-C-008  Institutional and publication information
```

---

## 7.7 Finger Millet Cultivation Publication

| No. | Resource | Organization | URL |
|---:|---|---|---|
| 14 | Finger Millet cultivation reference | Sri Lanka Department of Agriculture | `https://drive.google.com/file/d/1WbiZaLpIaX4ZGtNboYCgttpBiKLAVpgv/view?usp=sharing` |

This source supports Finger Millet topics including:

```text
FM-C-001  Publication and background
FM-C-002  Climate and soil requirements
FM-C-003  Land preparation
FM-C-004  Recommended varieties
FM-C-005  Cultivation method and timetable
FM-C-006  Nursery management and transplanting
FM-F-001  Fertilizer management
FM-C-007  Irrigation
FM-C-008  Weed management
FM-C-009  Disease and pest management
FM-C-010  Harvest and processing
FM-C-011  Institutional information
```

---

## 7.8 Cowpea Cultivation Publication

| No. | Resource | Organization | URL |
|---:|---|---|---|
| 15 | Cowpea cultivation reference | Sri Lanka Department of Agriculture | `https://drive.google.com/file/d/1Pxq7yyStaQKbYRm-ajwC-dCVujCeINYQ/view?usp=sharing` |

This source supports Cowpea topics including:

```text
CP-C-001  Cultivation method
CP-C-002  Seed treatment, planting and spacing
CP-F-001  Fertilizer, weed and irrigation management
CP-C-003  Recommended varieties
CP-C-004  Harvest and storage
CP-C-005  Mid-season cultivation
CP-C-006  Institutional and publication information
```

---

## 7.9 Soybean Cultivation Publication

| No. | Resource | Organization | URL |
|---:|---|---|---|
| 16 | Soybean cultivation reference | Sri Lanka Department of Agriculture | `https://drive.google.com/file/d/1sWeqHWADwovlon5V4nShZAvvdskiYzkv/view?usp=sharing` |

This source supports Soybean topics including:

```text
SB-C-001  Climate and soil requirements
SB-C-002  Cultivation season
SB-C-003  Land preparation
SB-C-004  Recommended varieties
SB-C-005  Seed requirement and spacing
SB-C-006  Seed treatment and inoculation
SB-F-001  Thinning, weed control and fertilizer
SB-C-007  Irrigation
SB-C-008  Harvesting and processing
SB-C-009  Storage
SB-C-010  Institutional and publication information
```

---

## 7.10 Chilli Cultivation Publication

| No. | Resource | Organization | URL |
|---:|---|---|---|
| 17 | Chilli cultivation reference | Sri Lanka Department of Agriculture | `https://drive.google.com/file/d/1e0EU4b3Hr49K0UZV1xJh_mYv90gyoaAw/view` |

The tracked Chilli cultivation material covers topics including:

```text
General introduction
Climate and soil requirements
Planting seasons
Recommended varieties
Seed requirement and nursery preparation
Field planting and spacing
Irrigation
Fertilizer application
Weed management
Fungal diseases
Collar rot and Choanephora blight
Powdery mildew and bacterial wilt
Viral diseases
Leaf curl complex and management
Narrow leaf disorder
Harvesting and dried chilli production
```

---

## 7.11 Source Attribution Strategy

Source provenance is maintained at several levels.

### Tracking Registry

`source_tracking.md` records the human-readable source and source URL for curated knowledge records.

### RAG Corpus

Each `documents.json` entry contains:

```text
source_id
source
```

These values are copied into ChromaDB metadata during indexing.

### Structured Knowledge Bases

Structured files such as:

```text
disease_kb.json
treatment_db.json
crop_db.json
best_practices.json
seasonal_calendar.json
```

also contain source references.

This enables the system to preserve provenance from:

```text
original publication
        ↓
structured JSON
        ↓
RAG document
        ↓
ChromaDB metadata
        ↓
retrieved source
        ↓
agent response
```

---

## 7.12 Source Verification

Source verification was performed during T-31 Knowledge Base QA.

The source-tracking records mark the referenced resources as verified and completed.

The verified source families include:

```text
Sri Lanka Department of Agriculture
├── RRDI
├── HORDI
├── field-crop publications
└── crop-specific cultivation publications

International Rice Research Institute
└── Rice Diseases Online Resource
```

For pesticide-related information, current Sri Lankan pesticide registration and product-label guidance must take precedence over historical recommendations stored in the knowledge base because approved products and application instructions may change over time.

---

# 8. Knowledge Base Update Procedure

This section describes the recommended procedure for safely adding or modifying knowledge-base content.

A developer should not edit the ChromaDB files directly.

The source of truth is the JSON data stored under:

```text
knowledge_base/
```

After changing the JSON files, the ChromaDB index must be regenerated using the indexing script.

The general workflow is:

```text
Verify authoritative source
        ↓
Update structured JSON data
        ↓
Update documents.json
        ↓
Update source_tracking.md
        ↓
Run structured-data validators
        ↓
Run T-31 knowledge-base audit
        ↓
Re-index ChromaDB
        ↓
Run retrieval tests
        ↓
Run regression tests
```

---

## 8.1 Verify the Source First

New agricultural information should be based on a reliable source.

Preferred sources currently used by the project include:

```text
Sri Lanka Department of Agriculture
RRDI
HORDI
FCRDI
Registrar of Pesticides
IRRI
```

Before creating a new record:

1. identify the source publication or official page,
2. record its URL,
3. verify the agricultural information,
4. assign a source ID,
5. preserve the source name in the relevant JSON files.

For pesticide information, current Sri Lankan registration and product-label information should override historical recommendations.

---

## 8.2 Decide Which Data Files Must Change

The required files depend on the type of knowledge being added.

For a new disease, the normal update is:

```text
disease_kb.json
treatment_db.json
documents.json
source_tracking.md
```

Crop advisory information may instead require updates to:

```text
crop_db.json
best_practices.json
seasonal_calendar.json
documents.json
source_tracking.md
```

`documents.json` must be updated whenever the new information needs to be retrievable through RAG.

---

## 8.3 Preserve Stable IDs

Every RAG document requires a unique:

```text
id
```

The ID becomes the ChromaDB record ID during indexing.

Example naming convention:

```text
R-D-001
T-D-003
CH-D-001
MZ-C-004
```

Do not reuse an existing ID for a different document.

Before re-indexing, the T-31 audit checks for duplicate document IDs.

---

## 8.4 Update `disease_kb.json`

A new disease should use the same structure as existing disease records.

Template:

```json
{
  "<disease_key>": {
    "id": "<unique-source-id>",
    "name": "<disease name>",
    "scientific_name": "<causal organism>",
    "disease_type": "<fungal|bacterial|viral|other>",
    "crop": "<crop>",
    "symptoms": [
      "<symptom 1>",
      "<symptom 2>"
    ],
    "severity": {
      "level": "<severity level>",
      "basis": "<source-supported basis>"
    },
    "region": [
      "<applicable region>"
    ],
    "source": {
      "source_id": "<source-id>",
      "name": "<source name>"
    }
  }
}
```

The top-level `<disease_key>` is also used to connect the disease to its corresponding treatment record.

Example key style:

```text
rice_blast
tomato_late_blight
chilli_anthracnose
```

---

## 8.5 Update `treatment_db.json`

Every disease in `disease_kb.json` must have a matching top-level key in `treatment_db.json`.

Template:

```json
{
  "<disease_key>": {
    "disease": "<disease name>",
    "chemical": [],
    "organic": [],
    "cultural": [],
    "prevention": [],
    "source": {
      "source_id": "<source-id>",
      "name": "<source name>"
    }
  }
}
```

Treatment categories must remain arrays even when no verified recommendation is available.

For example:

```json
"chemical": []
```

is valid.

Do not invent treatments simply to avoid an empty list.

---

## 8.6 Chemical Treatment Safety

If verified chemical recommendations are added, the record may require:

```text
safety_caveat
```

Example structure:

```json
{
  "chemical": [
    "<verified chemical recommendation>"
  ],
  "safety_caveat": "<current registration and label safety guidance>"
}
```

Where pesticide dosages are stored, the safety guidance should remind users to verify current:

```text
Sri Lankan pesticide registration
product label
application rate
personal protective equipment
re-entry interval
pre-harvest interval
Registrar of Pesticides / Department of Agriculture guidance
```

The T-31 audit specifically checks numeric pesticide dosage records for missing safety guidance.

---

## 8.7 Add the RAG Document to `documents.json`

To make the new information available through semantic retrieval, add a corresponding document to:

```text
knowledge_base/documents.json
```

Current document schema:

```json
{
  "id": "<unique-id>",
  "title": "<document title>",
  "text": "<verified knowledge text>",
  "crop": "<crop>",
  "category": "<category>",
  "language": "<language code>",
  "source_id": "<source-id>",
  "source": "<source name>",
  "region": "<region>",
  "season": "<season>"
}
```

All current records use the ten fields above.

Typical English language value:

```text
en
```

A general season may be represented as:

```text
general
```

The document ID must be unique because it is used directly as the ChromaDB ID.

---

## 8.8 Add Bilingual Documents Where Appropriate

Where both English and Sinhala source-backed content is maintained, separate RAG records may be created.

For example:

```text
SS-C-001-EN
SS-C-001-SI
```

Each language-specific record must have its own unique document ID.

The `language` metadata must correctly identify the document language.

---

## 8.9 Update Source Tracking

Add the new source-backed record to:

```text
knowledge_base/source_tracking.md
```

The tracking table contains:

```text
ID
Crop
Category
Topic
Source
Source URL
Verified
Status
Notes
```

Example structure:

```markdown
| ID | Crop | Category | Topic | Source | Source URL | Verified | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| <ID> | <Crop> | <Category> | <Topic> | <Source> | <URL> | ✅ | Completed | <verification notes> |
```

This file is the human-readable provenance registry for the curated knowledge base.

---

## 8.10 Validate Disease Coverage

Run:

```bash
python scripts/validate_disease_kb.py
```

The script checks:

```text
disease record count >= 50
crop count >= 5
```

A successful run ends with:

```text
T-15.1 disease coverage passed.
```

This script checks coverage rather than every individual disease field, so developers must still follow the documented disease schema.

---

## 8.11 Validate Disease/Treatment Consistency

Run:

```bash
python scripts/validate_treatment_db.py
```

This validator checks:

```text
disease and treatment record counts
matching disease/treatment keys
required treatment fields
treatment arrays
missing treatment records
orphan treatment records
```

The following treatment fields must be lists:

```text
chemical
organic
cultural
prevention
```

Successful validation ends with:

```text
T-15.2 and T-15.3 treatment database validation passed.
```

---

## 8.12 Run the Full Knowledge-Base Audit

Run:

```bash
python scripts/audit_t31_kb.py
```

The audit reports:

```text
database counts
document schema problems
duplicate document IDs
crop coverage
category coverage
region coverage
agroclimatic-zone references
source attribution
disease/treatment key consistency
chemical-treatment safety
corpus pesticide dosage safety
under-represented crops
```

Important results to review include:

```text
Schema issues
Duplicate IDs
Missing source records
Diseases without treatment record
Treatments without disease record
Numeric dosage without safety caveat
Dosage documents without safety caveat
```

For a clean update, these issue counts should normally remain:

```text
0
```

### Important Audit Limitation

`audit_t31_kb.py` is primarily a reporting tool.

A successful process exit alone does not mean that every reported issue count is zero.

The developer must review its printed results.

The current audit checks these required `documents.json` fields:

```text
id
title
text
crop
category
source
source_id
region
season
```

The current corpus schema also requires:

```text
language
```

even though the T-31 audit does not currently include `language` in its required-field check.

Therefore, every new document should still contain all ten fields documented in Section 3.1.

---

# 9. Re-indexing Procedure

After updating `documents.json`, the ChromaDB index must be synchronized.

Do not manually modify files inside:

```text
chroma_store/
```

Use the project indexer instead.

---

## 9.1 Run the Indexer

From the repository root:

```bash
python scripts/index_knowledge_base.py
```

The indexer:

```text
1. loads documents.json,
2. builds metadata-enriched embedding text,
3. creates all-MiniLM-L6-v2 embeddings,
4. detects stale ChromaDB IDs,
5. deletes stale records,
6. upserts current records,
7. checks the final document count.
```

---

## 9.2 Expected Re-index Behaviour

If a new document is added:

```text
documents.json count increases
        ↓
new ChromaDB record inserted
```

If an existing document is edited while retaining the same ID:

```text
existing ChromaDB ID
        ↓
upsert
        ↓
record updated
```

If a document is deleted:

```text
ID exists in ChromaDB
but not documents.json
        ↓
stale-record detection
        ↓
ChromaDB record deleted
```

---

## 9.3 Verify Index Counts

The indexer prints:

```text
Source document count
ChromaDB document count
```

These values must match.

The final T-31 baseline was:

```text
Source document count   : 303
ChromaDB document count : 303
```

After adding new documents, the expected count depends on the number of documents added.

For example:

```text
303 existing documents
+ 1 new RAG document
------------------------
304 expected documents
```

or:

```text
303 existing documents
+ 2 bilingual records
------------------------
305 expected documents
```

The indexer automatically raises an error when:

```text
ChromaDB count != documents.json count
```

---

## 9.4 Test Basic Retrieval

After indexing, run:

```bash
python scripts/test_retrieval.py
```

This verifies that semantic retrieval can return relevant ChromaDB documents.

For a newly added disease, developers should also manually query terminology associated with that disease and confirm that the expected document appears among the returned results.

---

## 9.5 Test Retrieval Quality

Run:

```bash
python scripts/test_rag_quality.py
```

This exercises the broader RAG query set.

The script currently requires manual relevance review.

Its output should therefore be inspected rather than interpreted as an automatic pass/fail relevance score.

---

## 9.6 Test Keyword Fallback

Run:

```bash
python scripts/test_t23_fallback.py
```

This verifies:

```text
normal semantic retrieval
low-confidence keyword fallback
hybrid fallback ranking
exact-title rescue
```

The existing fallback regression should continue to pass after knowledge-base changes.

---

## 9.7 Run Full Regression Tests

Finally run:

```bash
python -m pytest -v
```

At the end of T-31, the project baseline was:

```text
216 passed
0 failed
```

A knowledge-base update should not introduce regression failures.

---

# 10. Worked Example: Adding a New Disease

This example describes the complete developer workflow.

The example uses placeholders intentionally so that unsupported agricultural facts are not introduced into the knowledge base.

Assume a verified source describes a disease with:

```text
Disease key : <new_disease_key>
Document ID : <NEW-D-001>
Crop        : <crop>
Source      : <verified publication>
```

---

## 10.1 Step 1 — Add the Disease Record

Open:

```text
knowledge_base/disease_kb.json
```

Add:

```json
"<new_disease_key>": {
  "id": "<NEW-D-001>",
  "name": "<Disease Name>",
  "scientific_name": "<Scientific Name>",
  "disease_type": "<Disease Type>",
  "crop": "<crop>",
  "symptoms": [
    "<verified symptom 1>",
    "<verified symptom 2>"
  ],
  "severity": {
    "level": "<level>",
    "basis": "<source-supported basis>"
  },
  "region": [
    "Sri Lanka"
  ],
  "source": {
    "source_id": "<NEW-D-001>",
    "name": "<Verified Source Name>"
  }
}
```

Ensure the surrounding JSON syntax remains valid.

---

## 10.2 Step 2 — Add the Matching Treatment Record

Open:

```text
knowledge_base/treatment_db.json
```

Use exactly the same top-level disease key:

```json
"<new_disease_key>": {
  "disease": "<Disease Name>",
  "chemical": [],
  "organic": [],
  "cultural": [
    "<verified cultural recommendation>"
  ],
  "prevention": [
    "<verified prevention recommendation>"
  ],
  "source": {
    "source_id": "<NEW-D-001>",
    "name": "<Verified Source Name>"
  }
}
```

If no source-backed recommendation exists for a treatment category, keep the list empty.

Do not invent missing treatment information.

---

## 10.3 Step 3 — Add the RAG Document

Open:

```text
knowledge_base/documents.json
```

Append:

```json
{
  "id": "<NEW-D-001>",
  "title": "<Disease Name>",
  "text": "<Verified source-backed description, symptoms and management information>",
  "crop": "<crop>",
  "category": "disease",
  "language": "en",
  "source_id": "<NEW-D-001>",
  "source": "<Verified Source Name>",
  "region": "Sri Lanka",
  "season": "general"
}
```

If both English and Sinhala versions are maintained, create separate unique IDs.

---

## 10.4 Step 4 — Record the Source

Update:

```text
knowledge_base/source_tracking.md
```

Add the source and URL with verification notes.

Example:

```markdown
| <NEW-D-001> | <Crop> | Disease | <Disease Name> | <Source> | <URL> | ✅ | Completed | Symptoms and management verified |
```

---

## 10.5 Step 5 — Validate the Structured Data

Run:

```bash
python scripts/validate_disease_kb.py
python scripts/validate_treatment_db.py
```

Confirm that:

```text
disease validation passes
treatment validation passes
no missing treatment key exists
no orphan treatment key exists
```

---

## 10.6 Step 6 — Run Knowledge-Base QA

Run:

```bash
python scripts/audit_t31_kb.py
```

Review the output.

The following should normally remain zero:

```text
Schema issues
Duplicate IDs
Missing source records
Diseases without treatment record
Treatments without disease record
Numeric dosage without safety caveat
Dosage documents without safety caveat
```

Also verify that the new crop/document appears in the relevant coverage output.

---

## 10.7 Step 7 — Re-index ChromaDB

Run:

```bash
python scripts/index_knowledge_base.py
```

Confirm:

```text
Source document count == ChromaDB document count
```

If one new document was added to the current 303-document baseline:

```text
304 == 304
```

should be expected.

---

## 10.8 Step 8 — Verify Retrieval

Run:

```bash
python scripts/test_retrieval.py
```

Then test terminology specific to the newly added disease and verify that the expected document is returned.

Also run:

```bash
python scripts/test_rag_quality.py
python scripts/test_t23_fallback.py
```

Review the RAG-quality output manually and ensure fallback tests still pass.

---

## 10.9 Step 9 — Run the Regression Suite

Run:

```bash
python -m pytest -v
```

The update is ready when:

```text
structured validators pass
KB audit has no unexpected issues
ChromaDB count matches documents.json
new disease can be retrieved
fallback behaviour remains correct
full regression suite passes
```

---

## 10.10 Developer Checklist

Before committing a knowledge-base update, confirm:

```text
[ ] Source is authoritative and recorded
[ ] New ID is unique
[ ] disease_kb.json updated
[ ] matching treatment_db.json key added
[ ] treatment arrays use correct list structure
[ ] pesticide safety caveat added where required
[ ] documents.json updated with all 10 fields
[ ] language metadata included
[ ] source_tracking.md updated
[ ] validate_disease_kb.py passes
[ ] validate_treatment_db.py passes
[ ] audit_t31_kb.py reviewed
[ ] duplicate IDs = 0
[ ] missing sources = 0
[ ] disease/treatment mismatch = 0
[ ] pesticide safety issues = 0
[ ] ChromaDB re-indexed
[ ] ChromaDB count matches source count
[ ] retrieval tested
[ ] fallback regression tested
[ ] full pytest suite passes
```

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