# T-29 API Contract Test Report

**Run date:** 2026-09-30  
**Contract:** Day 1 / T-02 API Contract v1.0.0  
**Command:** `python -m pytest tests/test_api_contract_t29.py -q`  
**Result:** 26 passed, 0 failed

## Endpoint Results

Valid request responses were checked against their Pydantic response models, required contract fields, nested field sets, and documented crop sections. Timings are single-run local `TestClient` measurements in milliseconds; weather was fixture-backed and RAG used its fixture fallback because ChromaDB is not installed in this test environment.

| Endpoint | Valid response | Time (ms) | Notes |
|---|---:|---:|---|
| `POST /api/orchestrator/process` | PASS | 62.39 | Authenticated valid token |
| `POST /api/disease/diagnose` | PASS | 14.88 | Response and nested treatments validated |
| `POST /api/weather/advice` | PASS | 4.05 | Contract weather response fixture |
| `POST /api/rag/retrieve` | PASS | 16.78 | Stub fallback response; live Chroma path not exercised |
| `POST /api/crop/advice` | PASS | 10.27 | All eight advisory sections present |
| `GET /api/health` | PASS | 9.76 | All five documented services present |
| `POST /api/auth/register` | PASS | 742.78 | Exact response keys and values checked |
| `POST /api/auth/login` | PASS | 396.97 | Token, type, expiry, and user checked |

## Failure Coverage

| Scenario | Result |
|---|---|
| Missing required request fields on all seven POST endpoints | PASS, `400 VALIDATION_ERROR` |
| Malformed JSON on all seven POST endpoints | PASS, `400 VALIDATION_ERROR` |
| Wrong primitive/object types on all seven POST endpoints | PASS, `400 VALIDATION_ERROR` |
| Semantic coordinate constraint violation | PASS, `422 UNPROCESSABLE_ENTITY` |
| Health request body | N/A by contract; GET has no request model and remains valid |
| Orchestrator authentication: valid, missing, expired, tampered | PASS; valid succeeds and the other three return `401 UNAUTHORIZED` |
| Rate limit above configured threshold | PASS, `429 RATE_LIMIT_EXCEEDED` with `Retry-After` |

## Deviation Notice

**Danindu, RAG / T-02.4:** The response fixture satisfies the required RAG source fields, but the live RAG implementation does not currently carry `publication_year` through Chroma metadata. `scripts/index_knowledge_base.py` does not index that property, `agents/rag/agent.py` does not populate it, and `RagSourceItem.publication_year` is optional although T-02.4 requires an integer. With ChromaDB unavailable here, the endpoint test exercised the stub fallback and cannot verify this live path. Add verified publication-year metadata to the corpus/indexer and make the response field required, or raise the discrepancy with the contract owner rather than inventing citation years.

**Sanketh, shared validation handling:** The initial check found malformed JSON, missing fields, and wrong input types returning `422`; the contract assigns these request-shape errors to `400`. The validation handler is now aligned and the full contract collection passes. Semantic constraints continue to return `422`.