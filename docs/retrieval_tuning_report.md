# T-23 Retrieval Tuning and Keyword Fallback Report

## 1. T-11 Baseline

The original RAG retrieval implementation used:

- Vector database: ChromaDB
- Embedding model: `all-MiniLM-L6-v2`
- Embedding dimension: 384
- Collection: `agri_knowledge_base`
- Indexed documents: 291
- Default `top_k`: 3
- Retrieval method: semantic similarity search
- Metadata support:
  - crop
  - category
  - language
  - region
  - season
  - source
  - source_id
  - title

### Baseline Evaluation

The T-11 retrieval quality test used 15 representative farmer queries.

| Metric | T-11 Result |
|---|---:|
| Total queries | 15 |
| Correct top-ranked results | 14 |
| Incorrect top-ranked results | 1 |
| Top-1 retrieval accuracy | 93.33% |

## 2. Identified Failure Case

The main known failure occurred for a tomato late-blight query.

Expected document:

- Tomato Late Blight
- Source ID: `T-D-003`

Incorrect top-ranked result:

- Tomato Early Blight
- Source ID: `T-D-002`

Both documents are semantically similar because they discuss tomato fungal diseases, symptoms and fungicide management.

This indicates that semantic similarity alone may fail when documents have highly similar content but different disease names.

## 3. T-23 Improvement Plan

The retrieval system will be improved using:

1. Better embedding text containing document title and metadata.
2. Review of document chunking.
3. Metadata-aware filtering.
4. Keyword fallback when semantic similarity is below a threshold.
5. Exact disease-name/title boosting in keyword search.
6. Re-evaluation of `top_k=3`.
7. Re-running the original 15-query test set.

## 4. Target

The goal for T-23 is:

- Improve retrieval accuracy above the T-11 baseline of 93.33%.
- Target 15/15 correct top-ranked documents.
- Demonstrate that a low-similarity query triggers keyword fallback.

## 5. Top-K Evaluation

The original T-11 retrieval system used a default `top_k` value of 3.

This value was reviewed during T-23.

### Decision

The default value will remain:

`top_k = 3`

### Reasoning

The T-11 baseline already achieved 14 correct top-ranked results out of 15 test queries, equivalent to 93.33% top-1 retrieval accuracy.

The identified retrieval failure was not caused by an insufficient number of returned documents. Instead, it occurred because Tomato Early Blight and Tomato Late Blight contain highly similar semantic content.

Increasing `top_k` would return additional documents but would not necessarily correct the ranking of highly similar documents. It would also increase the amount of context passed to downstream components and may introduce less relevant information.

The T-23 keyword fallback directly addresses this failure by applying stronger weighting to matching titles and disease-name phrases.

Therefore:

- Default semantic retrieval remains `top_k = 3`.
- The caller may still override `top_k` where required.
- Keyword fallback also returns up to the requested `top_k`.
- Retrieval quality will be improved through ranking and fallback rather than globally increasing the number of retrieved documents.

This keeps retrieval concise while preserving the existing API behaviour.

## 6. Chunking and Metadata Tuning

### Existing Chunking Structure

The knowledge base currently contains curated topic-level records. Each record normally represents one focused agricultural subject, such as a disease, crop management practice, variety recommendation, pest, or cultivation guideline.

During T-23, additional automatic splitting of every record was considered.

### Decision

The existing topic-level record boundaries will be retained.

The corpus will not be blindly divided into smaller fixed-size chunks because many records already represent a coherent agricultural topic. Further splitting could separate related symptoms, management recommendations, treatment information, or cultivation instructions.

Instead, retrieval quality is improved by enriching the text used to generate each document embedding.

### Metadata-Enriched Embeddings

Previously, embeddings were generated only from the document `text`.

The T-23 indexing pipeline now embeds:

- title
- crop
- category
- region
- season
- document text

The original document text is still stored as the ChromaDB document and returned to the RAG agent.

This allows metadata such as `Tomato Late Blight`, `tomato`, and `disease` to influence semantic ranking without adding artificial metadata text to the final RAG context.

### Expected Benefit

This tuning is particularly useful for documents whose body text is highly semantically similar, such as Tomato Early Blight and Tomato Late Blight.

The document title and crop/category metadata provide additional discriminative information during vector retrieval.

## Final T-23 Retrieval Evaluation

### T-11 Baseline

- Test queries: 15
- Correct top-ranked results: 14
- Incorrect top-ranked results: 1
- Top-1 retrieval accuracy: 93.33%

The main failure was:

`How do I manage tomato late blight?`

Semantic retrieval incorrectly ranked `Tomato Early Blight (T-D-002)`
above `Tomato Late Blight (T-D-003)`.

### T-23 Improvements

T-23 introduced:

- metadata-enriched embeddings using title, crop, category, region and season
- preservation of topic-level knowledge-base records as retrieval units
- low-similarity keyword fallback
- title and phrase-weighted keyword ranking
- exact-title rescue for high-confidence semantic misranking
- stale-record cleanup during re-indexing
- retention of default `top_k = 3`

No missing knowledge-base document was identified for the known failure.
`Tomato Late Blight (T-D-003)` was already present, so the issue was
classified as a retrieval-ranking problem rather than a knowledge-coverage
problem.

### T-23 Final Result

- Test queries: 15
- Correct top-ranked results: 15
- Incorrect top-ranked results: 0
- Top-1 retrieval accuracy: 100.00%

### Improvement

Retrieval accuracy improved from 93.33% to 100.00%.

- Additional correct queries: 1
- Accuracy improvement: 6.67 percentage points

The previously failed tomato late-blight query now returns:

- `Tomato Late Blight`
- Source ID: `T-D-003`
- Retrieval method: `keyword_title_rescue`

A separate forced-threshold test also demonstrated that low-similarity
semantic retrieval correctly triggers the keyword fallback.

Therefore, both T-23 completion criteria were satisfied:
retrieval quality improved over the T-11 baseline, and keyword fallback
was demonstrably triggered for a forced low-similarity case.