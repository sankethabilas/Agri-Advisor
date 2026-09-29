# Agri-Advisor: End-to-End Performance Benchmark & SLA Verification (Task T-22.6)

| **Document Version** | `1.0.0` |
| :--- | :--- |
| **Status** | **VERIFIED & BENCHMARKED** |
| **Test Date** | 2026-09-29 19:40:21Z |
| **Lead Engineer** | **Sanketh** (Team Lead & Orchestrator Engineer) |
| **Core Requirement** | "Seconds not Days" Interactive Agricultural Advisory Turnaround |

---

## 1. Executive Summary & Objective

In traditional agricultural extension models in Sri Lanka, farmers typically wait **3 to 7 days** for an agricultural extension officer (AI / ARP) to visit plots, inspect symptoms, and recommend interventions. 

Agri-Advisor eliminates this lag, achieving an interactive multi-agent advisory turnaround time measured in **milliseconds to seconds**.

### Benchmark Highlights
- **Overall Average E2E Response Time**: **754.34 ms (0.75 s)**
- **Fastest Response Time**: **65.43 ms**
- **Maximum Measured Latency**: **3372.69 ms**
- **Target SLA**: **< 4,000 ms** (Interactive threshold)
- **SLA Compliance**: **PASSED (100% compliant with 'seconds not days' requirement)**

---

## 2. Intent-by-Intent Benchmark Results

| Intent Classification | Target Crop | District / Zone | Consulted Specialist Agents | Sources Retrieved | Avg Response Time | SLA Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `disease_diagnosis` | Paddy | Kurunegala | `disease_agent, weather_agent, rag_agent` | 3 | **1731.0 ms** | ✅ PASSED (< 4.0s) |
| `disease_diagnosis` | Tomato | Badulla | `disease_agent, weather_agent, rag_agent` | 3 | **888.1 ms** | ✅ PASSED (< 4.0s) |
| `crop_advice` | Maize | Anuradhapura | `crop_agent, rag_agent` | 3 | **101.5 ms** | ✅ PASSED (< 4.0s) |
| `crop_advice` | Chilli | Jaffna | `crop_agent, rag_agent` | 3 | **76.4 ms** | ✅ PASSED (< 4.0s) |
| `weather_query` | Paddy | Polonnaruwa | `disease_agent, weather_agent, rag_agent` | 1 | **843.0 ms** | ✅ PASSED (< 4.0s) |
| `mixed_query` | Paddy | Ampara | `disease_agent, weather_agent, rag_agent` | 1 | **886.1 ms** | ✅ PASSED (< 4.0s) |

---

## 3. Subsystem Latency Breakdown

| Subsystem Component | Operational Details | Typical Latency Contribution |
| :--- | :--- | :--- |
| **Security & Authentication Gate** | JWT token validation, rate-limiting check, input sanitization | **1 - 3 ms** |
| **NLP Classification & NER** | Keyword & Regex intent scoring, crop/symptom/stage extraction | **2 - 8 ms** |
| **Specialist Disease Agent** | Pathology knowledge base search, symptom token matching, ranking | **10 - 25 ms** |
| **Specialist Weather Agent** | Coordinate resolution, cached live Open-Meteo fetch, risk calculation | **20 - 80 ms** |
| **Specialist RAG Agent** | Sentence Transformer embedding generation & ChromaDB vector search | **150 - 450 ms** |
| **Specialist Crop Advisor** | 8-section agronomy assembly, seasonal planting window, variety lookup | **10 - 30 ms** |
| **LLM Synthesis / Fallback** | Role-prompt formatting, 8-block advisory structuring & disclaimer | **20 - 80 ms (rule-based) / 800-1800 ms (cloud LLM)** |
| **Total End-to-End Pipeline** | Full orchestrator intake to rendered response payload | **~250 - 850 ms (typical development mode)** |

---

## 4. Conclusion & Sign-Off

The integrated Agri-Advisor system achieves instantaneous advisory generation with complete domain grounding, fulfilling the primary requirement of delivering **timely, actionable, and safe agronomic advice in seconds**.
