# Outbreak Sentinel Agent Guide

The **Outbreak Sentinel Agent** is an autonomous agricultural disease surveillance service engineered for Sri Lankan farming ecosystems. It continuously monitors anonymized disease diagnostics across districts, detects statistically anomalous disease clusters, correlates them with real-time agro-meteorological risks, dispatches early warning alerts to agricultural extension officers and farmers, and continuously learns from intervention outcomes.

---

## 1. Architecture & Sense-Reason-Act-Learn Loop

```text
[SENSE]
  │   - Query anonymized diagnosis_log (48h window, confidence >= 0.7)
  ▼
[REASON]
  │   - Compute 28-day baseline mean & standard deviation (with std floor 0.5)
  │   - Apply learned disease threshold multiplier: (baseline + 2*std) * multiplier
  │   - Check anomaly condition: count >= MIN_CASES (5) AND count > threshold
  ▼
[DECIDE]
  │   - Call Weather Agent (/api/weather/advice) with 3x retry & backoff
  │   - Anomaly + High Weather Disease Risk  --> "outbreak"
  │   - Anomaly + Medium/Low/Offline Weather --> "watch"
  │   - Non-anomalous                       --> "none"
  ▼
[ACT]
  │   - "watch"    -> Notify District Agricultural Extension Officer only
  │   - "outbreak" -> Enforce 24h cooldown
  │                   Retrieve verified DOA treatment guidance via RAG
  │                   Dispatch localized alerts (en, si, ta) to Officers & Farmers
  │                   in affected and neighbouring districts
  ▼
[LEARN]
      - Evaluate outbreak decisions after 5 days
      - Case reduction >= 30% -> "resolved"  (decrease multiplier by 0.25, min 1.0)
      - Case surge >= 30%     -> "worsening" (increase multiplier by 0.25, max 3.0)
      - Otherwise             -> "persisting"
```

---

## 2. Guardrails & Responsible AI Design

1. **Deterministic Statistical Decisions**: The LLM **never** decides whether an outbreak exists. All thresholding, variance calculation, and risk classification are 100% deterministic Python.
2. **Constrained LLM Role**: The LLM is used strictly for formatting non-technical, farmer-friendly SMS copy (max 320 chars) and extension officer briefings.
3. **Template Fallback**: If the LLM provider (Groq/OpenAI) fails or times out, rule-based fallback templates guarantee that emergency alerts still dispatch.
4. **Mandatory Advisory Disclaimer**: Every farmer-facing message includes the compact advisory disclaimer:
   > *"Advisory only. For severe cases, visit your nearest Agrarian Services Office."*
5. **Data Minimisation & Privacy**: The Sentinel database stores only district-level agricultural data (district, crop, disease, confidence, timestamp). No farmer identities, names, or private records are ever stored in surveillance tables.
6. **Alert Fatigue Prevention**: Strict 24-hour cooldown prevents redundant farmer alert spam for the same `(district, crop, disease)`.

---

## 3. Environment Variables

Configure these settings in `.env`:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `SENTINEL_DATABASE_PATH` | `data/sentinel.sqlite3` | SQLite path for surveillance and decisions |
| `WEATHER_AGENT_URL` | `http://127.0.0.1:8000/api/weather/advice` | Weather Agent endpoint |
| `RAG_AGENT_URL` | `http://127.0.0.1:8000/api/rag/retrieve` | RAG treatment retrieval endpoint |
| `SENTINEL_MIN_CASES` | `5` | Minimum case count in 48h to qualify as a cluster |
| `SENTINEL_CONFIDENCE_THRESHOLD` | `0.7` | Minimum diagnosis confidence filter |
| `SENTINEL_COOLDOWN_HOURS` | `24` | Cooldown period between farmer alerts |
| `SENTINEL_SCAN_INTERVAL_HOURS` | `3` | Automated scan frequency via APScheduler |
| `SENTINEL_EVAL_INTERVAL_HOURS` | `24` | Automated 5-day evaluation frequency |
| `SENTINEL_ENABLE_SMS` | `false` | Enable live Twilio SMS dispatch |
| `TWILIO_ACCOUNT_SID` | - | Optional Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | - | Optional Twilio Auth Token |
| `TWILIO_FROM_NUMBER` | - | Optional Twilio sender phone number |

---

## 4. API Endpoints (`/api/sentinel`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/sentinel/scan` | Trigger immediate surveillance scan cycle |
| `GET` | `/api/sentinel/decisions` | Query past decisions (`?district=...&level=...`) |
| `POST` | `/api/sentinel/evaluate` | Trigger 5-day outcome evaluation & threshold adaptation |
| `POST` | `/api/sentinel/seed-demo` | Seed synthetic cases for test/demo |
| `GET` | `/api/sentinel/health` | Service and scheduler health check |

---

## 5. How to Run the Demo

### Step 1: Start the Backend Service
```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn orchestrator.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 2: Seed Demo Data
```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/sentinel/seed-demo"
```
*Creates 6 simulated cases of Bacterial Leaf Blight in Rice for Anuradhapura within 48h and 28 days of low background activity.*

### Step 3: Trigger Scan
```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/sentinel/scan"
```

### Step 4: Verify Decisions & Dispatches
```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/sentinel/decisions"
```

---

## 6. Known Limitations & Future Work

1. **Simulated Background Baseline**: In initial deployment without years of historical data, baseline models rely on synthetic seeds and small window moving averages.
2. **Farmer Self-Report Noise**: Initial diagnoses originate from farmer symptom descriptions which may contain observational inaccuracies before verification by an extension officer.
3. **Threshold Calibration**: The $\pm 0.25$ multiplier step algorithm is transparent and explainable, but full operational rollout will require calibration against multi-season epidemiology field studies conducted by the Department of Agriculture.
