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