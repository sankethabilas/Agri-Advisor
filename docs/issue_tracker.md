# Agri-Advisor: Shared Defect Log & Issue Tracker (Task T-22.8)

| **Document Version** | `1.0.0` |
| :--- | :--- |
| **Status** | **ACTIVE & MAINTAINED** |
| **Last Updated** | 2026-09-30 |
| **Lead Quality Engineer** | **Sanketh** (Team Lead & Orchestrator Engineer) |
| **Team Contributors** | **Sanketh**, **Danindu**, **Ishira**, **Pathum** |

---

## 1. Overview & Tracking Workflow

This issue tracker logs all defects, architectural drifts, and integration discrepancies identified during Sprint Day 6 End-to-End Orchestration Integration (Task T-22). Each defect is assigned a unique tracking ID, severity, component owner, root cause analysis, resolution commit, and verification status.

---

## 2. Integration Defect Log

| Issue ID | Severity | Component / Area | Description & Symptom | Owner | Root Cause | Resolution & Fix | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-01** | `High` | `RAG Agent`<br>(`/agents/rag`) | Semantic search returned 0 sources for valid agricultural queries with default similarity cutoff (`0.60`). | **Danindu** / **Sanketh** | ChromaDB collection used squared Euclidean distance (`l2`) instead of cosine distance; naive `1 - dist` produced near-zero values. | Updated `build_sources` to calculate cosine similarity via `1.0 - (dist / 2.0)` on normalized unit embeddings with calibrated thresholding. | **RESOLVED & VERIFIED** |
| **DEF-02** | `Medium` | `RAG Agent`<br>(`/agents/rag`) | RAG search with `crop_filter="Paddy"` returned 0 documents due to case and alias mismatch. | **Danindu** / **Sanketh** | `documents.json` contains mixed casing (`"rice"`, `"tomato"` vs `"Chilli"`, `"Maize"`) and query entities use `"Paddy"`. | Created `normalize_crop_filter()` mapping aliases to multi-cased candidate lists (`["rice", "Rice", "paddy", "Paddy"]`) using `$in` query filters. | **RESOLVED & VERIFIED** |
| **DEF-03** | `Low` | `Synthesis Engine`<br>(`/orchestrator`) | Fallback advisory for non-chemical diseases lacked explicit Pre-Harvest Interval (PHI) text. | **Sanketh** | Diseases managed culturally (e.g. Bacterial Leaf Blight) had empty `chemical` lists, omitting PHI text. | Added standard safety advisory and PHI guidance note in fallback chemical block for non-chemical prescriptions. | **RESOLVED & VERIFIED** |
| **DEF-04** | `Critical` | `Crop Agent`<br>(`/agents/crop`) | Crop Advisor lacked a live implementation, falling back exclusively to offline mock stubs. | **Danindu** / **Sanketh** | `/agents/crop` directory only contained `.gitkeep` placeholder prior to final integration. | Implemented live `CropAgent` (`/agents/crop/agent.py`) and FastAPI service (`/agents/crop/main.py`) delivering all 8 advisory sections. | **RESOLVED & VERIFIED** |
| **DEF-05** | `Medium` | `Orchestrator Hub`<br>(`/orchestrator`) | `GET /api/health` returned hardcoded mock fixture instead of inspecting live microservices. | **Sanketh** | Health check endpoint was wired to `stub_service.get_health_check()`. | Replaced with dynamic health monitor inspecting orchestrator, disease KB, weather client, ChromaDB collection, and crop guidelines with live latencies. | **RESOLVED & VERIFIED** |
| **DEF-06** | `Low` | `Testing / Scripts`<br>(`/scripts`) | UnicodeEncodeError when printing Sinhala agricultural text / emojis to Windows CP1252 console. | **Sanketh** | Windows command prompt default codepage (cp1252) failed to encode Unicode crop emojis (`🌾`, `🌱`). | Sanitized benchmark/validation scripts with explicit UTF-8 handling and safe terminal printing fallbacks. | **RESOLVED & VERIFIED** |

---

## 3. Defect Classification Guidelines

- **Critical**: Blocks core end-to-end data flow, breaks contract compatibility, or causes service crash.
- **High**: Functional failure in a specialist agent (e.g. 0 retrieved documents, incorrect intent dispatch).
- **Medium**: Non-critical functional issue or degraded behavior with fallback available.
- **Low**: Formatting, logging, or minor environmental / documentation discrepancies.

---

## 4. Verification Record

All 6 logged defects have been resolved in the development branch and verified via the automated test suite (`85 passed across 9 test modules`) and live execution of the two documented worked scenarios.
