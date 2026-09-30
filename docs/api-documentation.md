# Agri-Advisor API Documentation (As Built)

**Updated:** 2026-09-30  
**API version:** `1.0.0`  
**Base URL (local):** `http://127.0.0.1:8000`

This is the as-built reference for the FastAPI application in `orchestrator.main`. It supersedes the Day 1 endpoint descriptions where they differ. Start the service with `python -m uvicorn orchestrator.main:app --host 127.0.0.1 --port 8000`. Interactive OpenAPI documentation is available at `/docs`.

The eight T-29 contract endpoints are registration, login, orchestrator processing, disease diagnosis, weather advice, RAG retrieval, crop advice, and health. The application also implements feedback, session lookup/clear, and the root overview routes; they are documented below as additional routes. Samples show response shapes and representative values. Timestamps, IDs, latency, service status, and agent output vary at runtime. The T-29 contract test suite verified successful response models; its RAG test used the stub fallback because ChromaDB was unavailable in that test environment.

## Authentication

### Register

`POST /api/auth/register` creates a case-insensitive unique SQLite account. Username length is 3-254 characters and must match `[A-Za-z0-9][A-Za-z0-9_.@+-]{2,253}`. Password length is 12-128 characters. Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes (310,000 iterations); the password is never returned.

Request:

```http
POST /api/auth/register
Content-Type: application/json

{"username":"farmer_anu_0842","password":"Example-Password-2026!"}
```

Response `201 Created`:

```json
{"user_id":"farmer_anu_0842","message":"Account created successfully."}
```

Other statuses: `400 VALIDATION_ERROR` for malformed or structurally invalid input; `422 UNPROCESSABLE_ENTITY` for field constraints; `409 ERROR` if the username already exists.

### Login and JWT

`POST /api/auth/login` checks the account and issues a signed JSON Web Token.

Request:

```http
POST /api/auth/login
Content-Type: application/json

{"username":"farmer_anu_0842","password":"Example-Password-2026!"}
```

Response `200 OK`:

```json
{
  "access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.<claims>.<signature>",
  "token_type":"bearer",
  "expires_in":1800,
  "user_id":"farmer_anu_0842"
}
```

The token is an HS256-signed compact JWT with `sub`, `iat`, and `exp` claims. `JWT_EXPIRY_MINUTES` controls token lifetime (default 30 minutes; `expires_in` is seconds). Configure `JWT_SECRET_KEY`; production refuses to start without it. Development generates an ephemeral signing key when unset, so tokens do not survive an application restart. Invalid credentials return `401 UNAUTHORIZED`; malformed or invalid fields return `400` or `422` as described under [Errors](#errors).

### Protected routes

Send `Authorization: Bearer <access_token>` to:

- `POST /api/orchestrator/process`. The JWT subject must exactly equal request `user_id`; a mismatch returns `403 FORBIDDEN`.
- `POST /api/feedback`.

The registration and login routes are public. Disease, weather, RAG, crop, health, root overview, and both session routes are also public in the current implementation. In particular, `GET` and `DELETE /api/sessions/{user_id}` do not currently verify JWT ownership; do not expose them to untrusted clients with sensitive session data. Production enables HTTP-to-HTTPS redirection when `APP_ENV=production`.

## Contract Endpoints

### 1. `POST /api/orchestrator/process`

Authenticated end-to-end advisory. The service classifies the query, dispatches relevant local specialist agents, retrieves RAG context for every query, synthesizes an answer, applies responsible-AI checks, and stores the conversation turn in in-memory session context.

Required request fields: `query` (1-1000 characters), `user_id` (1-254 characters), and `location.district` (1-100 characters). Optional fields: `location.province`, `latitude` (5-10), `longitude` (79-82), `agro_ecological_zone` (max 32), `session_id` (max 128), `language` (`en`, `si`, or `ta`, default `en`), and `crop_context` (max 100).

Request:

```http
POST /api/orchestrator/process
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "query":"How should I manage paddy brown spot in Anuradhapura?",
  "user_id":"farmer_anu_0842",
  "location":{"district":"Anuradhapura","province":"North Central","latitude":8.3114,"longitude":80.4037,"agro_ecological_zone":"DL1b"},
  "language":"en",
  "crop_context":"Paddy"
}
```

Response `200 OK` (optional response fields are omitted here):

```json
{
  "answer":"Brown spot risk is elevated. Inspect the crop and follow the cited DOA treatment guidance. Avoid spraying when heavy rain is forecast.",
  "sources":[{"title":"Paddy Brown Spot Management","author_organization":"Department of Agriculture (DOA), Sri Lanka","document_id":"DOA-PADDY-PATH-2023-V2","section":"Brown Spot","confidence_score":0.94,"reference_url":"https://doa.gov.lk/rrdi/pathology/brown-spot-guidelines"}],
  "weather_alert":{"severity":"none","title":"Normal Conditions","message":"No severe weather warnings active.","impact_warning":"Proceed with standard field operations.","valid_until":"2026-09-30T12:00:00+00:00"},
  "metadata":{"session_id":"sess-a1b2c3d4e5f6","user_id":"farmer_anu_0842","intent":"disease_diagnosis","confidence":0.95,"agents_consulted":["disease_agent","weather_agent","rag_agent"],"language":"en","latency_ms":342,"timestamp":"2026-09-30T12:00:00+00:00"}
}
```

Success: `200`. Errors: `400`, `401`, `403`, `422`, `429`, or `500`. `429` includes `Retry-After`. By default the per-user sliding-window limit is 30 requests per 60 seconds; configure `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`.

### 2. `POST /api/disease/diagnose`

Public specialist endpoint. Required: `crop`, a non-empty `symptoms` array, and `location.district`. `growth_stage` and `season` (`Maha` or `Yala`) are optional.

Request:

```http
POST /api/disease/diagnose
Content-Type: application/json

{"crop":"Paddy","symptoms":["oval brown spots with grey centers","yellowing leaves"],"location":{"district":"Anuradhapura","province":"North Central","agro_ecological_zone":"DL1b"},"growth_stage":"Tillering","season":"Maha"}
```

Response `200 OK`:

```json
{
  "disease":"Paddy Brown Spot (Bipolaris oryzae)",
  "confidence":0.94,
  "severity":"Moderate",
  "treatment":{"chemical":[{"name":"Azoxystrobin 250 g/L SC","dosage":"15 mL per 16 L knapsack sprayer","instructions":"Spray during calm weather, thoroughly covering foliage.","pre_harvest_interval_days":14}],"organic":[{"name":"Neem Seed Kernel Extract (NSKE 5%)","dosage":"50 g crushed neem seed per liter of water","instructions":"Filter and spray early in the morning."}],"cultural":[{"practice":"Water drainage","description":"Drain stagnant water for 48 hours to reduce canopy humidity."}]},
  "prevention":["Use certified disease-free seed.","Maintain balanced N:P:K fertilization."],
  "source":"Sri Lanka Department of Agriculture (DOA) - Field Handbook on Paddy Pathology & Disease Management (2023 Edition)",
  "symptoms_confirmed":["Oval brown lesions with grey centers","Yellow halo surrounding leaf spots"],
  "differential_diagnoses":[{"disease":"Paddy Blast (Magnaporthe oryzae)","confidence":0.38,"distinguishing_factor":"Blast lesions are spindle-shaped rather than oval."}]
}
```

Success: `200`. Errors: `400` for malformed/structurally invalid input and `422` for constraints or invalid literal values. Agent exceptions are handled by the application's generic `500` handler.

### 3. `POST /api/weather/advice`

Public weather and risk endpoint. Required: `location.district`. Optional: `crop` and `growth_stage`. In production, weather service failures return `502` rather than being reported as normal conditions.

Request:

```http
POST /api/weather/advice
Content-Type: application/json

{"location":{"district":"Anuradhapura","province":"North Central","latitude":8.3114,"longitude":80.4037,"agro_ecological_zone":"DL1b"},"crop":"Paddy","growth_stage":"Tillering"}
```

Response `200 OK`:

```json
{
  "current":{"temperature_c":28.6,"humidity_pct":89,"rainfall_mm":6.4,"wind_speed_kmh":14.2,"wind_direction":"SW","condition":"Moderate Rain","icon":"10d","timestamp":"2026-09-30T12:00:00+00:00"},
  "forecast":[{"date":"2026-10-01","temp_min_c":24.2,"temp_max_c":31.5,"rainfall_mm":22.0,"rainfall_prob_pct":85,"humidity_pct":92,"wind_speed_kmh":16.5,"condition":"Heavy Showers"}],
  "disease_risk":{"level":"High","score":0.88,"susceptible_diseases":["Paddy Brown Spot"],"contributing_factors":["High humidity","Warm temperatures"]},
  "pest_risk":{"level":"Moderate","score":0.62,"susceptible_pests":["Brown Plant Hopper"],"contributing_factors":["Warm nocturnal temperatures"]},
  "advisory":"Postpone spraying before heavy rain and keep drainage channels clear.",
  "alerts":[{"id":"ALT-WZ-20260930-01","alert_type":"heavy_rain","severity":"warning","title":"Heavy rain alert","description":"Heavy showers are forecast.","valid_from":"2026-09-30T18:00:00+00:00","valid_to":"2026-10-02T18:00:00+00:00","recommended_action":"Halt spraying and inspect drainage."}]
}
```

Success: `200`. Errors: `400`, `422`, or `502 UPSTREAM_AGENT_ERROR` when the weather service is unavailable.

### 4. `POST /api/rag/retrieve`

Public semantic retrieval endpoint. Required: `query` (3-500 characters). Optional: `top_k` (1-10, default 3), `crop_filter`, `category_filter`, and `min_score` (0-1, default 0.60). The endpoint falls back to a stub response if live retrieval fails.

Request:

```http
POST /api/rag/retrieve
Content-Type: application/json

{"query":"Paddy brown spot symptoms and treatment","top_k":3,"crop_filter":"Paddy","category_filter":"disease","min_score":0.65}
```

Response `200 OK`:

```json
{
  "context":"Brown Spot (Bipolaris oryzae) causes oval brown spots with grey centers. Follow DOA fungicide and crop sanitation guidance.",
  "sources":[{"id":"DOA-PADDY-PATH-2023-CH04-S02","title":"Field Handbook on Paddy Pathology & Disease Management","content":"Brown Spot causes oval brown spots with grey centers.","score":0.94,"document_id":"DOA-PADDY-PATH-2023-V2","section":"Section 4.2: Brown Spot","author_organization":"Department of Agriculture (DOA), Sri Lanka","publication_year":2023,"url":"https://doa.gov.lk/rrdi/pathology/brown-spot-guidelines"}],
  "confidence":[0.94],
  "metadata":{"total_chunks_retrieved":1,"query_embedding_model":"sentence-transformers/all-MiniLM-L6-v2","vector_distance_metric":"cosine","execution_time_ms":28}
}
```

Success: `200` (including stub fallback). Errors: `400` or `422` for request validation. `publication_year` is optional in the live response model even though Day 1 marked it required; live Chroma metadata does not currently guarantee that value.

### 5. `POST /api/crop/advice`

Public crop advisory endpoint. Required: `crop`, `location.district`, and `season` (`Maha` or `Yala`). Optional: `soil_type`, `land_extent_acres` (default 1.0), and `irrigation_type` (`Major Irrigation`, `Minor Irrigation`, or `Rainfed`). The route falls back to a stub response if live crop execution fails. The response contains the eight named advisory sections.

Request:

```http
POST /api/crop/advice
Content-Type: application/json

{"crop":"Paddy","location":{"district":"Kurunegala","province":"North Western","agro_ecological_zone":"IL1a"},"season":"Maha","soil_type":"Low Humic Gley (LHG)","land_extent_acres":2.0,"irrigation_type":"Major Irrigation"}
```

Response `200 OK` (all eight required section keys shown; section objects are intentionally abbreviated):

```json
{
  "crop":"Paddy (Rice)","season":"Maha","agro_ecological_zone":"IL1a (Low Country Intermediate Zone)","soil_type":"Low Humic Gley (LHG)","land_extent_acres":2.0,
  "advisory_sections":{
    "1_varieties":{"section_title":"Recommended Rice Varieties","recommended_varieties":[{"variety_name":"Bg 352"}]},
    "2_land_preparation":{"section_title":"Field Preparation"},
    "3_planting_schedule":{"section_title":"Crop Establishment"},
    "4_fertilizer_management":{"section_title":"Fertilizer Schedule"},
    "5_water_management":{"section_title":"Water Management"},
    "6_weed_control":{"section_title":"Integrated Weed Management"},
    "7_harvesting_and_post_harvest":{"section_title":"Harvesting and Storage"},
    "8_crop_rotation_and_intercropping":{"section_title":"Crop Rotation"}
  },
  "source":"Sri Lanka Department of Agriculture (DOA) - Paddy Crop Management Compendium (Circular RRDI-2023-01)",
  "generated_at":"2026-09-30T12:00:00+00:00"
}
```

Success: `200`. Errors: `400` or `422`. Runtime crop-agent failures are logged and served through fallback rather than surfaced as an HTTP error.

### 6. `GET /api/health`

Public health check. It probes the local knowledge base and agent dependencies, returning overall `healthy` or `degraded` status plus per-service status, latency, and message. Health data is runtime-dependent.

Request:

```http
GET /api/health
```

Response `200 OK`:

```json
{"status":"healthy","version":"1.0.0","environment":"development","timestamp":"2026-09-30T12:00:00+00:00","services":{"orchestrator":{"status":"healthy","latency_ms":1,"message":"Orchestrator core online"},"disease_agent":{"status":"healthy","latency_ms":1,"message":"Disease diagnostic engine connected (1 diseases loaded)"},"weather_agent":{"status":"healthy","latency_ms":1,"message":"Weather API connection and risk models verified"},"rag_agent":{"status":"degraded","latency_ms":1,"message":"ChromaDB store warning"},"crop_agent":{"status":"healthy","latency_ms":1,"message":"Crop advisory guidelines loaded (1 crops)"}}}
```

## Additional Implemented Routes

### `POST /api/feedback` (authenticated)

Request:

```http
POST /api/feedback
Content-Type: application/json
Authorization: Bearer <access_token>

{"session_id":"sess-a1b2c3d4e5f6","helpful":true}
```

Response `200 OK`: `{"accepted":true,"message":"Feedback received."}`. Errors: `400`, `401`, or `422`. Feedback is currently retained in process memory.

### `GET /api/sessions/{user_id}` (currently unauthenticated)

Example request: `GET /api/sessions/farmer_anu_0842`  
Success `200 OK` returns the session object with `session_id`, `user_id`, `created_at`, `updated_at`, `language`, `active_crop`, `location`, `growth_stage`, `confirmed_diseases`, `turn_count`, and `history`. A history turn contains `turn_id`, `query`, `answer`, `intent`, `timestamp`, `language`, and `agents_consulted`. A missing session returns `404 RESOURCE_NOT_FOUND`.

### `DELETE /api/sessions/{user_id}` (currently unauthenticated)

Example request: `DELETE /api/sessions/farmer_anu_0842`  
Success `200 OK`: `{"message":"Session for user 'farmer_anu_0842' successfully cleared.","user_id":"farmer_anu_0842"}`. A missing session returns `404 RESOURCE_NOT_FOUND`.

### `GET /`

Example request: `GET /`  
Success `200 OK` returns system name, version, online status, endpoint paths, and active in-memory session count. No authentication is required.

## Errors

All application-handled errors use this JSON envelope. `details` is `null` for HTTP errors and an array for validation errors. The timestamp and request ID are generated per response.

```json
{
  "error": {
    "code":"VALIDATION_ERROR",
    "message":"Request failed validation against API contract.",
    "status_code":400,
    "details":[{"field":"body -> query","issue":"Field required"}],
    "timestamp":"2026-09-30T12:00:00+00:00",
    "request_id":"req-a1b2c3d4"
  }
}
```

| HTTP status | Error code | Actual meaning / trigger |
|---|---|---|
| `400` | `VALIDATION_ERROR` | Malformed JSON, missing required fields, wrong primitive/object types, or orchestrator input rejected by sanitization/injection checks. |
| `401` | `UNAUTHORIZED` | Missing, invalid, tampered, or expired bearer token; invalid login credentials. |
| `403` | `FORBIDDEN` | Orchestrator token subject differs from request `user_id`. |
| `404` | `RESOURCE_NOT_FOUND` | Session lookup or clear requested a user with no active session. |
| `409` | `ERROR` | Duplicate registration username. The current HTTP exception mapper has no dedicated conflict code. |
| `422` | `UNPROCESSABLE_ENTITY` | Pydantic constraints or semantic values fail validation (for example, coordinates outside the allowed range). |
| `429` | `RATE_LIMIT_EXCEEDED` | Per-user orchestrator request limit exceeded; includes `Retry-After` in seconds. |
| `500` | `INTERNAL_SERVER_ERROR` | Unhandled exception or orchestration pipeline failure. Generic responses do not reveal exception text. |
| `502` | `UPSTREAM_AGENT_ERROR` | Weather service unavailable for the direct weather endpoint. |
| `503` | `SERVICE_UNAVAILABLE` | Reserved by the HTTP exception mapper; no current documented route emits it in the inspected implementation. |
| `504` | `AGENT_TIMEOUT` | Reserved by the HTTP exception mapper; orchestrator agent timeouts are isolated and omitted from results rather than currently returned as 504. |
| Other mapped HTTP status | `ERROR` | Fallback code for an HTTPException status without a dedicated mapping. |

The wrapper resembles a problem-details envelope but is not the RFC 7807 media type or canonical shape. Unmatched paths may use FastAPI's framework-default 404 response rather than this application envelope.

Request-shape errors (missing fields, malformed JSON, and wrong types) are `400`; field/semantic validation such as numeric bounds and invalid enum values are `422`. This distinction is intentional and covered by T-29 tests.

## Security Controls

- **Credential storage:** account passwords use per-account random salts and PBKDF2-HMAC-SHA256 with 310,000 iterations; login comparison uses a constant-time digest comparison.
- **JWT:** HS256 with `sub`, issue time, and expiry claims. Set a strong persistent `JWT_SECRET_KEY`; production requires it and enables HTTPS redirection. The development fallback key is ephemeral.
- **Protected-route coverage:** only orchestrator processing and feedback require a token. Specialist routes, health, and session read/delete routes are not authenticated. Session routes expose conversational history and should be restricted before deployment beyond a trusted environment.
- **Sanitization:** orchestrator query (max 1,000), crop context (100), district (100), and agro-ecological zone (32) have ANSI escape sequences and Unicode control/format characters removed; whitespace is normalized and text is truncated. Other specialist request bodies are Pydantic-validated but do not pass through this sanitizer.
- **Prompt-injection detection:** case-insensitive patterns detect common instruction overrides, prompt disclosure requests, safety bypasses, policy headers, and DAN/persona requests in the sanitized query, crop context, district, and agro-ecological zone. Matches are rejected with `400`; logs record the event without including submitted text. This is pattern detection, not a general semantic classifier.
- **Generated output filtering:** answer text is sanitized, limited to 20,000 characters, known unsafe instruction lines are removed, and secret-like token/private-key strings are redacted. This lexical filter does not reliably detect off-topic or unsafe agronomic content; T-33 records that limitation as an accepted residual risk. Responsible-AI response processing also performs PII redaction.
- **Rate limiting:** only `/api/orchestrator/process` is limited, using a thread-safe, process-local per-subject sliding window. Defaults: 30 requests per 60 seconds. Rejected requests return `429` and `Retry-After`. Multi-worker deployments need shared limiter state for a global limit.
- **CORS and transport:** allowed origins come from `CORS_ALLOWED_ORIGINS`; defaults are localhost Streamlit origins. Production redirects HTTP to HTTPS. Deploy behind a trusted TLS-terminating proxy and do not expose the app port directly.

## Risk Scoring (T-16)

The weather agent returns a score from 0.00 to 1.00, clamped and rounded to two decimal places. The response labels use `Low`, `Moderate`, `High`, and `Critical` (the T-16 examples' `Medium` name is represented as `Moderate` in the API).

| Score | Level |
|---|---|
| `< 0.60` | `Low` |
| `0.60` to `< 0.85` | `Moderate` |
| `0.85` to `< 0.95` | `High` |
| `0.95` to `1.00` | `Critical` |

Disease risk contributions: temperature 20-32 C adds 0.25; relative humidity at least 80% adds 0.35; current rainfall at least 5 mm adds 0.25; warm temperature together with high humidity adds another 0.25. Pest risk contributions: temperature 25-35 C adds 0.35; relative humidity 60-85% adds 0.25; rainfall below 5 mm adds 0.25. Scores are rule-based scouting indicators, not calibrated epidemiological predictions or diagnoses. The heavy-rain/spray safety rules and forecast alert thresholds are detailed in [risk-model.md](risk-model.md).

## Day 1 Contract Deviations

These decisions describe the shipped behavior, not proposed contract changes. The Day 1 contract remains available as the baseline in [api-contract.md](api-contract.md); the final architecture flow is updated there.

| Day 1 design or silence | As built | Reason / evidence |
|---|---|---|
| Separate UI, orchestrator, disease, weather, RAG, and crop service ports and microservice calls. | One FastAPI app on port 8000 exposes all API routes and calls agent implementations in-process. Only external weather/LLM/vector-store dependencies cross process boundaries in the normal local setup. | Backend setup and `orchestrator.main` show agents are imported/called locally; separate service ports are not required to run the app. |
| Diagram showed every query could call disease, crop, weather, and RAG as independent service calls. | NLP intent routes to a specialist branch; RAG retrieval is attempted unconditionally. Disease routes also request weather; mixed intent selects agents at a 0.35 component-score threshold; specialist calls have independent timeouts. | Matches `orchestrator.router` dispatch rules. |
| Auth and feedback/session API coverage were not all part of the original core route set. | Public registration/login plus authenticated process and feedback routes exist; GET/DELETE session routes exist and are currently unauthenticated. | T-21/T-33 security work and current FastAPI route definitions. Session route authorization remains a security gap, documented above. |
| Contract listed only the final answer, sources, weather alert, and metadata as orchestrator response fields. | Response model also permits `diagnosis`, `immediate_treatment`, `prevention`, `disclaimer`, and `why_explanation`. Metadata intent accepts additional labels such as `weather_query`, `crop_advice`, `general_query`, and `mixed_query`. | The live Pydantic models support these optional/additional values; omitted optional fields are not guaranteed in every response. |
| RAG `publication_year` was required in Day 1 source objects. | It is optional in the live `RagSourceItem`; the live index/agent does not guarantee publication-year metadata. | T-29 report identifies this live data gap; year values must not be invented. |
| Day 1 grouped malformed input, types, and semantic validation under `400`; older route errors were initially `422`. | Malformed JSON, missing fields, and wrong types are `400 VALIDATION_ERROR`; semantic/bounds validation stays `422 UNPROCESSABLE_ENTITY`. | T-29 adjusted validation handling and verifies this split. |
| Day 1 described errors as uniform RFC 7807 and listed dedicated conflict/availability/timeout codes. | Actual body is `{error:{code,message,status_code,details,timestamp,request_id}}`; duplicate username returns `409` with generic `ERROR`. `503` and `504` are mapped but not currently emitted by inspected routes. | Actual exception handlers in `orchestrator.main`; this is RFC-7807-like, not canonical RFC 7807. |
| Contract implied shared status behavior such as `404` for unknown crop/disease/document, `502` for any upstream, and `503/504` agent responses. | Verified route-specific behavior differs: session-not-found emits `404`; direct weather unavailability emits `502`; RAG/crop routes fall back to stubs; orchestrated specialist failures are isolated and omitted from partial synthesis. | Current route handlers, router, and T-29 coverage. |
| Error-handling text stated exception details were logged, and security policy did not specify field-level controls. | Generic failures return safe messages; structured logs include request ID and exception type without exception message/traceback. Injection checks, selective sanitization, lexical output filtering, and per-user process limiting are implemented. | T-33 audit and current security/exception middleware. |
| Risk level examples used “Medium” for the 0.60 band. | API enum calls that band `Moderate`; thresholds are `<0.60`, `0.60-<0.85`, `0.85-<0.95`, and `0.95-1.00`. | T-16 decision recorded in `risk-model.md` and `agents/weather/risk_utils.py`. |
| Day 1 health example implied OpenWeather and all agents were independently probed and healthy. | Health checks local knowledge-base loading and RAG collection access; weather service status is currently marked healthy by a local code path and is not a live upstream probe. Overall status can be `degraded`. | Current `/api/health` implementation; response values depend on installed data/services. |
| Day 1 described multi-turn session and feedback persistence generally. | Session context and feedback are in process memory; accounts are in SQLite. In-memory sessions/feedback do not survive restart and are not shared across workers. | Current `SessionManager` and feedback store. |

## Verification

The T-29 report records `26 passed` for `python -m pytest tests/test_api_contract_t29.py -q`, including successful response-model checks for all eight contract endpoints, authentication behavior, malformed/type-invalid requests, coordinate bounds, and `429` with `Retry-After`. The live Chroma retrieval path was not covered in that environment; the tested response used the documented RAG stub fallback. See [api_test_report_t29.md](api_test_report_t29.md) and [security_audit_t33.md](security_audit_t33.md).
