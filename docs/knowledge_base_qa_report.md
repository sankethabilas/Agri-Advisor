# T-31 Knowledge Base QA & Source Attribution Verification Report

**Project:** Agri-Advisor — Multi-Agent AI System for Smart Farming  
**Task:** T-31 Knowledge Base QA & Source Attribution Verification  
**Member:** Danindu  
**Area:** WA-2  

## 1. Objective

T-31 verifies that the Agri-Advisor corpus is accurate, source-attributed, reasonably distributed across crops and regions, safe when presenting pesticide guidance, and still retrieves correctly after knowledge-base edits.

The QA work covered `documents.json`, `disease_kb.json`, and `treatment_db.json`.

## 2. QA Tools

The following scripts were used:

- `scripts/audit_t31_kb.py`
- `scripts/apply_t31_safety_fixes.py`
- `scripts/apply_t31_verified_corrections.py`
- `scripts/add_t31_sesame_coverage.py`
- `scripts/index_knowledge_base.py`
- `scripts/test_retrieval.py`
- `scripts/test_rag_quality.py`
- `scripts/test_t23_fallback.py`

Local JSON backups created during fixes are stored under `backups/t31/` and are excluded from Git.

## 3. Treatment Recommendation Verification

Treatment/source families were reviewed for Rice, Tomato, Chilli, Maize, Legumes, Peanut, Sesame, Big Onion, Soybean, Mungbean, Cowpea and Finger Millet.

Two clear corpus recommendation differences were corrected.

### Big Onion

Updated:
- `O-C-005-EN`
- `O-C-005-SI`

Verified seed-treatment guidance stored in the corpus:
- Thiram 80% — 5 g/kg seed
- Captan 80% — 4 g/kg seed
- Captan 50% — 6 g/kg seed
- Thiophanate methyl 50% + Thiram 30% WP — 4 g/kg seed

### Mungbean

Updated:
- `MG-C-002-EN`
- `MG-C-002-SI`

Verified seed-treatment guidance stored in the corpus:
- Captan — 3 g/kg seed
- Thiram — 2 g/kg seed
- Thiram + Thiophanate methyl — 2 g/kg seed

For older pesticide recommendations whose current registration status could not be confirmed with sufficient confidence, the historical recommendation was not silently rewritten. Instead, a current-registration/product-label safety caveat was added.

## 4. Source Attribution Verification

Final source statistics:

- Unique literal source names: **17**
- Unique source IDs: **90**
- Missing source records: **0**

Verified source families include:

- Department of Agriculture, Sri Lanka
- Horticultural Crops Research and Development Institute (HORDI)
- Rice Research and Development Institute (RRDI)
- Field Crops Research and Development Institute (FCRDI)
- Office of the Registrar of Pesticides (ROP)
- International Rice Research Institute (IRRI)

Official source families used during verification included:

- https://doa.gov.lk/hordi-crops/
- https://doa.gov.lk/hordi-crop-tomato/
- https://doa.gov.lk/hordi-crop-capsicum/
- https://doa.gov.lk/rrdi_ricediseases/
- https://doa.gov.lk/rrdi_commonricediseases/
- https://doa.gov.lk/fcrdi-downloads/
- https://doa.gov.lk/field-crops-sesame/
- https://doa.gov.lk/rop-downloads/
- https://rice-diseases.irri.org/

Source naming remains intentionally non-uniform in some places because publication-specific, crop-specific, year-specific and Sinhala/English source labels were retained for provenance.

## 5. Crop Coverage

### Before T-31 improvement

| Crop | Documents |
|---|---:|
| Chilli | 64 |
| Maize | 40 |
| Legumes | 35 |
| Big Onion | 34 |
| Finger Millet | 24 |
| Soybean | 22 |
| Mungbean | 16 |
| Cowpea | 15 |
| Tomato | 14 |
| Rice | 13 |
| Peanut | 10 |
| Sesame | 4 |

Sesame was the clearest coverage gap.

Twelve new source-attributed Sesame documents were added as six bilingual topic pairs covering:

- climate and soil,
- varieties / seed requirement / spacing,
- land preparation and sowing time,
- weed and water management,
- nutrient management,
- harvesting and storage.

### Final crop coverage

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

Final normalized crop groups: **12**

Every crop has non-zero coverage.

The audit also uses an internal review heuristic that flags crops with fewer than 25% of the highest crop count. This is a QA aid only, not a formal assignment completion criterion.

## 6. Regional Coverage

Final region metadata:

- `Sri Lanka` — 296 documents
- `general` — 5 documents
- `Dry and Intermediate Zones, Sri Lanka` — 2 documents

Detected agroclimatic references:

- Dry Zone — 8 documents
- Wet Zone — 5 documents
- Intermediate Zone — 8 documents

All three required agroclimatic zones are represented.

## 7. Chemical Safety Verification

A standardized safety caveat was added to:

- **21 structured treatment records** containing chemical recommendations
- **77 RAG corpus documents** containing pesticide/fungicide/insecticide/herbicide application guidance

The safety wording requires users to follow current Sri Lankan registration and product-label guidance for:

- dosage,
- PPE,
- re-entry interval,
- pre-harvest interval (PHI), and
- current Department of Agriculture / Registrar of Pesticides instructions.

Final safety audit:

- Records with chemical recommendations: **21**
- Records with numeric dosage: **10**
- Numeric dosage without safety caveat: **0**
- Corpus pesticide dosage documents detected: **15**
- Dosage documents without safety caveat: **0**

## 8. Final Data Integrity Audit

| Check | Result |
|---|---:|
| Corpus documents | 303 |
| Disease records | 51 |
| Treatment records | 51 |
| Schema issues | 0 |
| Duplicate IDs | 0 |
| Missing source records | 0 |
| Diseases without treatment record | 0 |
| Treatments without disease record | 0 |
| Normalized crop groups | 12 |
| Unique source names | 17 |
| Unique source IDs | 90 |
| Structured safety issues | 0 |
| Corpus dosage safety issues | 0 |

## 9. ChromaDB Re-indexing

Command:

`python scripts/index_knowledge_base.py`

Final result:

- Source document count: **303**
- ChromaDB document count: **303**
- Stale indexed documents: **0**

The vector store therefore matches the final source corpus.

## 10. Retrieval Verification

### Retrieval smoke test

Command:

`python scripts/test_retrieval.py`

Query:

`rice yellow spots`

Top results:

1. Leaf Scald — `R-D-005`
2. Brown Spot — `R-D-003`
3. Narrow Brown Leaf Spot — `R-D-007`

The returned results were relevant rice-disease documents.

### RAG quality test

Command:

`python scripts/test_rag_quality.py`

The full 15-query benchmark was rerun after re-indexing. The script uses manual `REVIEW` labels rather than an automatic final score. The reviewed top-ranked outputs remained relevant and no retrieval exception occurred.

### Keyword fallback / title rescue

Command:

`python scripts/test_t23_fallback.py`

Result:

- Semantic retrieval working
- Keyword fallback triggered correctly
- Tomato Late Blight ranked first during forced fallback
- Exact-title rescue triggered correctly
- Tomato Late Blight ranked first after title rescue
- **T-23 KEYWORD FALLBACK TEST PASSED**

## 11. Full Regression Test

Command:

`python -m pytest -v`

Result:

- **216 tests collected**
- **216 passed**
- **0 failed**
- **1 deprecation warning**
- Runtime: **127.73 seconds**

The warning was a Starlette `TestClient` / `httpx` deprecation warning and did not affect test success.

## 12. T-31 Completion Status

| Subtask | Status |
|---|---|
| T-31.1 Review treatment recommendations | Complete |
| T-31.2 Verify source attribution | Complete |
| T-31.3 Check and improve crop coverage | Complete |
| T-31.4 Check regional coverage | Complete |
| T-31.5 Verify chemical safety caveats | Complete |
| T-31.6 Re-index and rerun retrieval tests | Complete |
| T-31.7 Record final counts, coverage and sources | Complete |

Completion criteria:

- Every document has source attribution — **PASS**
- No crop has zero coverage — **PASS**
- ChromaDB successfully re-indexed — **PASS**
- Source corpus / ChromaDB count — **303 / 303**
- Retrieval smoke test — **PASS**
- Keyword fallback test — **PASS**
- Full regression suite — **216 / 216 PASS**

## 13. Known Limitations

1. Crop coverage is improved but not perfectly balanced; Peanut, Rice, Tomato and Cowpea remain below the internal 25% review heuristic.
2. Most records still use broad `Sri Lanka` region metadata instead of explicit zone-level metadata.
3. Source labels are valid but not fully normalized because provenance-specific names were retained.
4. Pesticide registration can change over time; current registration and product-label guidance must take precedence over stored historical recommendations.
5. `test_rag_quality.py` requires manual relevance review instead of automatically calculating the final relevance score.

## 14. Final Outcome

The final Agri-Advisor knowledge base contains **303 source-attributed documents across 12 normalized crop groups**. All crops have non-zero coverage, Sesame coverage increased from **4 to 16 documents**, automated pesticide-dosage safety issues were reduced to **zero**, ChromaDB was re-indexed successfully to **303 documents**, retrieval/fallback behaviour remained functional, and the full project regression suite passed **216/216 tests**.

T-31 is complete subject to the documented limitations above.
