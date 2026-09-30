# Agri-Advisor: Shared Defect Log & Issue Tracker (Task T-22.8)

| **Document Version**      | `1.0.0`                                          |
| :------------------------ | :----------------------------------------------- |
| **Status**                | **ACTIVE & MAINTAINED**                          |
| **Last Updated**          | 2026-09-30                                       |
| **Lead Quality Engineer** | **Sanketh** (Team Lead & Orchestrator Engineer)  |
| **Team Contributors**     | **Sanketh**, **Danindu**, **Ishira**, **Pathum** |

---

## 1. Overview & Tracking Workflow

This issue tracker logs all defects, architectural drifts, and integration discrepancies identified during Sprint Day 6 End-to-End Orchestration Integration (Task T-22). Each defect is assigned a unique tracking ID, severity, component owner, root cause analysis, resolution commit, and verification status.

---

## 2. Integration Defect Log

| Issue ID   | Severity   | Component / Area                        | Description & Symptom                                                                                      | Owner                     | Root Cause                                                                                                                         | Resolution & Fix                                                                                                                                        | Status                  |
| :--------- | :--------- | :-------------------------------------- | :--------------------------------------------------------------------------------------------------------- | :------------------------ | :--------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------ | :---------------------- |
| **DEF-01** | `High`     | `RAG Agent`<br>(`/agents/rag`)          | Semantic search returned 0 sources for valid agricultural queries with default similarity cutoff (`0.60`). | **Danindu** / **Sanketh** | ChromaDB collection used squared Euclidean distance (`l2`) instead of cosine distance; naive `1 - dist` produced near-zero values. | Updated `build_sources` to calculate cosine similarity via `1.0 - (dist / 2.0)` on normalized unit embeddings with calibrated thresholding.             | **RESOLVED & VERIFIED** |
| **DEF-02** | `Medium`   | `RAG Agent`<br>(`/agents/rag`)          | RAG search with `crop_filter="Paddy"` returned 0 documents due to case and alias mismatch.                 | **Danindu** / **Sanketh** | `documents.json` contains mixed casing (`"rice"`, `"tomato"` vs `"Chilli"`, `"Maize"`) and query entities use `"Paddy"`.           | Created `normalize_crop_filter()` mapping aliases to multi-cased candidate lists (`["rice", "Rice", "paddy", "Paddy"]`) using `$in` query filters.      | **RESOLVED & VERIFIED** |
| **DEF-03** | `Low`      | `Synthesis Engine`<br>(`/orchestrator`) | Fallback advisory for non-chemical diseases lacked explicit Pre-Harvest Interval (PHI) text.               | **Sanketh**               | Diseases managed culturally (e.g. Bacterial Leaf Blight) had empty `chemical` lists, omitting PHI text.                            | Added standard safety advisory and PHI guidance note in fallback chemical block for non-chemical prescriptions.                                         | **RESOLVED & VERIFIED** |
| **DEF-04** | `Critical` | `Crop Agent`<br>(`/agents/crop`)        | Crop Advisor lacked a live implementation, falling back exclusively to offline mock stubs.                 | **Danindu** / **Sanketh** | `/agents/crop` directory only contained `.gitkeep` placeholder prior to final integration.                                         | Implemented live `CropAgent` (`/agents/crop/agent.py`) and FastAPI service (`/agents/crop/main.py`) delivering all 8 advisory sections.                 | **RESOLVED & VERIFIED** |
| **DEF-05** | `Medium`   | `Orchestrator Hub`<br>(`/orchestrator`) | `GET /api/health` returned hardcoded mock fixture instead of inspecting live microservices.                | **Sanketh**               | Health check endpoint was wired to `stub_service.get_health_check()`.                                                              | Replaced with dynamic health monitor inspecting orchestrator, disease KB, weather client, ChromaDB collection, and crop guidelines with live latencies. | **RESOLVED & VERIFIED** |
| **DEF-06** | `Low`      | `Testing / Scripts`<br>(`/scripts`)     | UnicodeEncodeError when printing Sinhala agricultural text / emojis to Windows CP1252 console.             | **Sanketh**               | Windows command prompt default codepage (cp1252) failed to encode Unicode crop emojis (`🌾`, `🌱`).                                | Sanitized benchmark/validation scripts with explicit UTF-8 handling and safe terminal printing fallbacks.                                               | **RESOLVED & VERIFIED** |

---

## 3. Defect Classification Guidelines

- **Critical**: Blocks core end-to-end data flow, breaks contract compatibility, or causes service crash.
- **High**: Functional failure in a specialist agent (e.g. 0 retrieved documents, incorrect intent dispatch).
- **Medium**: Non-critical functional issue or degraded behavior with fallback available.
- **Low**: Formatting, logging, or minor environmental / documentation discrepancies.

---

## 4. Verification Record

All 6 logged defects have been resolved in the development branch and verified via the automated test suite (`85 passed across 9 test modules`) and live execution of the two documented worked scenarios.

---

## 5. T-28 UI, Usability and Functional Defects (2026-09-30)

| Issue ID       | Severity   | Component / Area                                         | Description & Reproduction                                                                                                                                     | Owner                 | Root Cause / Impact                                                                                                           | Resolution & Fix                                                                                              | Status   |
| :------------- | :--------- | :------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------- | :---------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------ | :------- |
| **DEF-T28-01** | `Critical` | **Streamlit UI** (`/ui`)                                 | Run `streamlit run ui/app.py` from the repository root. The app shows `ModuleNotFoundError: No module named 'utils'` before register/login renders.            | **Ishira**            | `ui/app.py` imports `utils.i18n` before adding the project root to `sys.path`; all UI screens and viewport tests are blocked. | Move path setup before project-local imports, or launch through a package-safe entry point, then repeat T-28. | **OPEN** |
| **DEF-T28-02** | `High`     | **Authentication** (`/orchestrator`)                     | Contract test `test_authentication_valid_missing_expired_and_tampered_tokens` expected 401 but a tampered JWT received HTTP 200.                               | **Pathum / Sanketh**  | Token signature validation is accepting a modified token; unauthorized requests may access advisory data.                     | Reject altered signatures and add a regression test for modified header, payload, and signature.              | **OPEN** |
| **DEF-T28-03** | `Medium`   | **RAG / Environment** (`/agents/rag`)                    | Focused tests log `ModuleNotFoundError: sentence_transformers`; orchestrator returns a degraded advisory with a service update.                                | **Danindu / Sanketh** | Required dependency is not installed in the active Python environment; source grounding is unavailable.                       | Install from `requirements.txt` in the supported environment and verify the RAG path returns sources.         | **OPEN** |
| **DEF-T28-04** | `Medium`   | **Query form** (`/ui/app.py`)                            | Attempt to test missing location. District is always one of the populated options and defaults to Anuradhapura, so no empty-location request can be submitted. | **Ishira**            | The UI has no blank district option or explicit missing-location validation state.                                            | Add a clear "Select your district" option and validate it before submission.                                  | **OPEN** |
| **DEF-T28-05** | `Low`      | **Farmer usability** (`/ui/auth_pages.py`, `/ui/app.py`) | Usability review found visible terms `Username`, `Account Credentials`, and `Client-side validation` in the auth flow.                                         | **Ishira**            | Copy is written for technical/account terminology rather than the limited-formal-education target user.                       | Replace with plain-language labels such as "Phone or email", "Your password", and short help text.            | **OPEN** |
