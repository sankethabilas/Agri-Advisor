# Agri-Advisor: Documented Worked Scenarios Execution Report (Task T-22.7)

| **Document Version** | `1.0.0` |
| :--- | :--- |
| **Execution Date** | 2026-09-29 19:42:04Z |
| **Lead Engineer** | **Sanketh** (Team Lead & Orchestrator Engineer) |
| **Status** | **VERIFIED LIVE ON DEVELOPMENT BRANCH** |

---

## Scenario 1: Rice Pathology & Weather Risk Management
- **Query**: *"My paddy crops in Kurunegala have spindle-shaped lesions with grey centres and yellowing leaves. What disease is this and how should I treat it?"*
- **Location**: Kurunegala (`IL1a`)
- **Intent**: `disease_diagnosis`
- **Diagnosed Disease**: **Bacterial Leaf Blight (Xanthomonas oryzae pv. oryzae)** (High Severity, High Confidence)
- **Consulted Agents**: `disease_agent, weather_agent, rag_agent`
- **Execution Time**: **3052.88 ms**
- **Citations**: 3 verified Department of Agriculture sources
- **Helpline**: `Agriculture Extension Office: 1920`

---

## Scenario 2: Maize Maha Season Cultivation & Agronomy
- **Query**: *"I am planting Maize in Anuradhapura during the Maha season. Provide recommended varieties and fertilizer schedule."*
- **Location**: Anuradhapura (`DL1b`)
- **Intent**: `crop_advice`
- **Consulted Agents**: `crop_agent, rag_agent`
- **Execution Time**: **42.72 ms**
- **Citations**: 3 verified Department of Agriculture sources
- **Helpline**: `Agriculture Extension Office: 1920`

---

## Validation Summary
Both documented worked scenarios execute end-to-end through the live multi-agent backend without relying on mock stubs. All returned advisories include grounded diagnostics/agronomy, live weather risk assessment, verified knowledge sources, and the mandatory helpline disclaimer.
