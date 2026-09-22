# UI/UX Specification — Agri-Advisor

**Task:** T-04 — UI/UX Plan & Advisory Response Layout Specification
**Owner:** Ishira
**Day:** 1
**Depends on:** T-02 (API Contract, v1.0.0 FROZEN)
**Status:** Draft — pending confirmation that the synthesis prompt (T-18) can produce the eight-block layout inside `answer`

> This revision maps every block and field below directly to `/docs/api-contract.md` v1.0.0, as signed off by all four members. Where the frozen contract does not (yet) define something this spec needs, it is flagged explicitly in Section 8 rather than invented.

---

## 1. Purpose

This document specifies every screen in the Agri-Advisor Streamlit frontend and the exact eight-block layout of the advisory response. Because the Orchestrator's response envelope (`/api/orchestrator/process`) exposes only `answer` (a synthesized markdown string), `sources[]`, `weather_alert`, and `metadata` — not the raw per-agent objects — the UI's eight-block layout is built from **two sources**: the structured markdown inside `answer` (Blocks 1–4, 7–8) and the two dedicated structured fields `sources[]` and `weather_alert` (Blocks 5–6), rendered as their own cards rather than parsed out of the markdown. This split is called out again in Section 4.

---

## 2. Conversational Query Screen

```
┌──────────────────────────────────────────────────────────┐
│  🌾 Agri-Advisor              [ EN | සිං | தமிழ் ]  [Logout] │
├──────────────────────────────────────────────────────────┤
│                                                            │
│   District: [ Dropdown: Anuradhapura, Kandy, Matara... ▼]│
│   Crop context (optional): [ Paddy ▼ ]                    │
│                                                            │
│   ┌────────────────────────────────────────────────┐ 🎙  │
│   │ Describe your crop problem...                   │     │
│   │                                                  │     │
│   └────────────────────────────────────────────────┘     │
│                                                            │
│                         [   Ask Agri-Advisor   ]          │
│                                                            │
├──────────────────────────────────────────────────────────┤
│  ── Conversation History ──                                │
│  [ Previous Q ]                                            │
│  [ Previous Advisory summary ]                              │
├──────────────────────────────────────────────────────────┤
│                                                            │
│              [ ADVISORY RESPONSE AREA — Section 4 ]        │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

### 2.1 Components → Request Fields

| Component | Type | Maps to `OrchestratorProcessRequest` field |
|---|---|---|
| Language Selector | Segmented control, top-right | `language` (`"en" \| "si" \| "ta"`, default `"en"`) |
| District Input | Dropdown | `location.district` (required); `location.province`, `location.agro_ecological_zone` populated server-side where known, not entered by the farmer |
| Crop context | Optional dropdown | `crop_context` (optional) — lets a farmer pin the active crop across a multi-turn conversation |
| Query Input Box | Multi-line text area | `query` — client-side enforce `minLength: 1`, `maxLength: 1000` per the contract; show a soft character counter only as the limit is approached, no raw schema language shown |
| Voice Input Button | Icon button (🎙) beside the input box | Transcribes to the `query` field; Should Have (AS-3) |
| Submit Button | Primary button, full-width below input | Triggers `POST /api/orchestrator/process`; disabled while in flight |
| Conversation History | Collapsible list above the response area | Built from `metadata.session_id` continuity — the UI keeps `session_id` from the first response and resends it as `session_id` in subsequent requests |
| Advisory Response Area | See Section 4 | Rendered from the full `OrchestratorProcessResponse` |

`user_id` is not entered on this screen — it is carried from the authenticated session (Section 3) and attached automatically to every request.

### 2.2 States

- **Empty**: Hint text only, no advisory area rendered.
- **Loading**: Submit button disabled, spinner with a plain-language loading message.
- **Success (`200`)**: Full advisory rendered per Section 4.
- **Partial**: If `weather_alert.severity` is `"none"` or `sources` is an empty array, the corresponding block (5 or 6) is omitted cleanly rather than shown empty — see T-12.8.
- **Client/Server error**: Rendered per the error taxonomy in Section 6 — plain-language only, never the raw `error.code` or `request_id` shown as primary text (available in a collapsed "details" affordance for debugging builds only).
- **`504 AGENT_TIMEOUT`**: Per the contract, the Orchestrator itself returns a synthesized answer using whichever agents responded in time — this is not a failure state for the UI, it renders normally but the answer may note reduced confidence.

---

## 3. Authentication Screens

> **Open item:** `/docs/api-contract.md` v1.0.0 does not yet define `/api/auth/register` or `/api/auth/login` — these were scoped under T-20/T-21 but are not in the frozen contract above. The layout below is specified against the fields agreed in the Day 1 UI plan (T-04.2) and should be reconciled with Pathum's auth endpoint contracts before T-20 begins on Day 5. See Section 8.

### 3.1 Registration

```
┌───────────────────────────────┐
│        Create Account          │
├───────────────────────────────┤
│ Name          [____________]   │
│ Phone / Email [____________]   │
│ Password      [____________]   │
│ District      [ Dropdown ▼]    │
│ Preferred     [ EN|SIN|TAM ]   │
│ Language                       │
│                                 │
│        [ Register ]            │
│  Already have an account? Log in│
└───────────────────────────────┘
```

Fields: Name, Phone or Email, Password, District, Preferred Language (T-20.1). District here pre-fills `location.district` and Preferred Language pre-fills `language` on the query screen after login.

### 3.2 Login

```
┌───────────────────────────────┐
│           Log In               │
├───────────────────────────────┤
│ Phone / Email [____________]   │
│ Password      [____________]   │
│                                 │
│          [ Log In ]            │
│   New here? Create an account  │
└───────────────────────────────┘
```

On success, the returned JWT is stored in Streamlit session state and sent as `Authorization: Bearer <JWT_TOKEN>` on every `/api/orchestrator/process` call, per Section 4.1 of the contract (optional in local dev, required in prod). A `401 UNAUTHORIZED` response at any point redirects to this screen. The query screen is gated behind a valid session, with a visible Logout control.

---

## 4. Eight-Block Advisory Response Layout (Strict Order)

This order is fixed and is what the synthesis prompt (T-18.3) must produce inside `answer`, combined with the two structured fields rendered outside of it.

| Block | Rendered from | Notes |
|---|---|---|
| 1. Header | `answer` (markdown, first section) | Restates the query/crop in plain language |
| 2. Diagnosis | `answer` (markdown) | Disease name, confidence, severity — sourced by the LLM from the Disease Agent's internal response and written into the markdown; the orchestrator envelope does not re-expose the raw `disease`/`confidence`/`severity` fields separately, so the UI does not parse them out — it trusts the synthesis prompt's structure |
| 3. Immediate Treatment | `answer` (markdown) | Chemical / Organic / Cultural, numbered, with urgency markers |
| 4. Prevention | `answer` (markdown) | Bulleted |
| 5. Weather Advisory | `weather_alert` (structured field, **not** parsed from markdown) | See 4.5 below |
| 6. Sources | `sources[]` (structured field, **not** parsed from markdown) | See 4.6 below |
| 7. Disclaimer | `answer` (markdown, fixed trailing section) | Static team-agreed wording, see 4.7 |
| 8. Follow-up Prompt & Helpline | `answer` (markdown) + `metadata.session_id` | See 4.8 |

### 4.1 Block 1 — Header
Plain-language restatement, e.g. "Advisory for your Paddy crop."

### 4.2 Block 2 — Diagnosis
- Disease name (common, prominent) with scientific name secondary
- Confidence: the LLM writes this as a percentage with a High/Medium/Low label in the markdown, derived from the Disease Agent's `confidence` (0.0–1.0), and the UI's badge styling (Section 5.2) is applied by pattern-matching the label text the model emits (`High`/`Medium`/`Low`) — **flagged as fragile in Section 8**, since it depends on the model reliably emitting one of exactly three labels
- Severity, matching the Disease Agent's enum: `Low | Moderate | High | Critical`

If the Disease Agent returned no diagnosis, or `differential_diagnoses` was used instead of a single `disease`, this block instead shows the alternatives with a consultation recommendation — never a single guess presented as fact.

### 4.3 Block 3 — Immediate Treatment
Grouped into three labeled sub-sections in this order, mirroring `treatment.chemical[]`, `treatment.organic[]`, `treatment.cultural[]` from the Disease Agent contract:
1. **Chemical** — name, dosage, instructions; pre-harvest interval (`pre_harvest_interval_days`) shown as a caution note, e.g. "Do not harvest within 14 days of application"
2. **Organic** — name, dosage, instructions
3. **Cultural** — practice, description

### 4.4 Block 4 — Prevention
Bulleted list, informational tone, no urgency markers.

### 4.5 Block 5 — Weather Advisory
Rendered directly from the `weather_alert` object in the response envelope:

| Field | UI treatment |
|---|---|
| `severity` (`none\|low\|moderate\|high\|severe`) | Color-coded badge (Section 5.2); block is **omitted entirely** when `severity == "none"` |
| `title` | Card heading |
| `message` | Body text |
| `impact_warning` | Emphasized line, e.g. bold or highlighted background |
| `valid_until` | Rendered as a relative action window, e.g. "Valid until Thu 18 Sep, 6 PM" rather than the raw ISO timestamp |

Note: the richer `disease_risk`/`pest_risk`/`forecast` data from the Weather Agent's own response (`/api/weather/advice`) is consumed by the Orchestrator during synthesis but is **not** part of the final envelope — the UI only ever sees the single condensed `weather_alert` object, not per-risk scores. Per BR-12, if `alert_type` context implies heavy rain, the synthesized `answer` text is expected to omit spray timing advice; this is a synthesis-prompt responsibility, not something the UI can independently enforce.

### 4.6 Block 6 — Sources
Rendered as a list directly from `sources[]`:

| Field | UI treatment |
|---|---|
| `title` | Primary citation text |
| `author_organization` | Secondary/smaller text, e.g. "— Dept. of Agriculture, Sri Lanka" |
| `section` | Optional parenthetical, e.g. "(Section 4.2)" |
| `confidence_score` (0.0–1.0) | Not shown as a raw number to the farmer; used only to sort sources descending |
| `reference_url` | If non-null, the title becomes a link; if `null`, plain text, no dead link |

Block is omitted if `sources` is an empty array.

### 4.7 Block 7 — Disclaimer
Fixed, team-agreed wording, identical on every response, localized to `language`:

> "This advisory is generated by an AI system to support your decision-making. It does not replace professional agricultural extension advice. For severe or uncertain cases, please consult your local Agriculture Extension Officer."

This is written into the tail of the synthesis prompt template (T-18.5, BR-1/BR-2), not sourced from any API field.

### 4.8 Block 8 — Follow-up Prompt & Helpline
- Short prompt inviting a follow-up question — the UI resends `metadata.session_id` on the next request so the Orchestrator's session context (T-06.5) applies
- Static helpline placeholder for the local Agriculture Extension Office (content TBD, see Section 8)
- "Was this helpful?" feedback control (FR-50, T-24.8) — not part of the current contract; logged client-side / to a future feedback endpoint
- "Why?" control (T-12.7) — triggers the Responsible AI explanation (T-26); not yet represented as a field in this contract version, flagged in Section 8

---

## 5. Farmer-Friendly Design Rules

### 5.1 General Rules
- **Large text**: base font size no smaller than 16px equivalent; headings clearly larger than body text.
- **High contrast**: suitable for outdoor phone use in bright sunlight.
- **Minimal navigation**: single primary flow (login → query → advisory); no nested menus.
- **Zero technical jargon in UI labels**: no `error.code`, `request_id`, raw JSON, or field names like `confidence_score` ever shown verbatim to the farmer.
- **Minimal steps**: one input, one button for the core flow.

### 5.2 Visual Indicators

| Indicator | Source | Treatment |
|---|---|---|
| Diagnosis confidence (High/Medium/Low) | Label emitted inside `answer` markdown | Green / Amber / Red badge, percentage + label |
| Weather `severity: none` | `weather_alert.severity` | Block hidden |
| Weather `severity: low` | `weather_alert.severity` | Green badge |
| Weather `severity: moderate` | `weather_alert.severity` | Amber badge |
| Weather `severity: high` | `weather_alert.severity` | Orange badge, bold |
| Weather `severity: severe` | `weather_alert.severity` | Red badge, bold, placed at top of the card |
| Urgency marker (treatment) | `pre_harvest_interval_days` present, or model-flagged urgency in markdown | Small icon or bold tag, e.g. "⚠ Do not harvest within 14 days" |

Color is never the only signal — every badge carries a text label as well.

---

## 6. Error Handling (mapped to Section 5 of the API contract)

| HTTP / `error.code` | UI behavior |
|---|---|
| `400 VALIDATION_ERROR` | Highlight the offending field inline (e.g. empty query, missing district) using `error.details[].field` |
| `401 UNAUTHORIZED` | Redirect to Login screen |
| `403 FORBIDDEN` | Plain "You don't have access to this" message |
| `404 RESOURCE_NOT_FOUND` | Suggest supported crops/districts in plain language |
| `422 UNPROCESSABLE_ENTITY` | Highlight the specific field, plain-language explanation |
| `429 RATE_LIMIT_EXCEEDED` | "Please wait a moment and try again" with a short client-side backoff before re-enabling submit |
| `500 / 502 / 503` | Generic "Something went wrong on our end, please try again shortly" — never expose `request_id` or stack traces in the primary message |
| `504 AGENT_TIMEOUT` | Not treated as an error — the Orchestrator returns a best-effort `answer`; rendered normally |

`error.request_id` is logged to the browser console / debug panel only, never shown as the primary user-facing message, for support/debugging purposes.

---

## 7. Mapping Summary (Block → Contract Field)

| UI Block | Contract source |
|---|---|
| 1 Header | `answer` (markdown) |
| 2 Diagnosis | `answer` (markdown, synthesized from Disease Agent's `disease`, `confidence`, `severity`) |
| 3 Treatment | `answer` (markdown, synthesized from `treatment.chemical[]/organic[]/cultural[]`) |
| 4 Prevention | `answer` (markdown, synthesized from `prevention[]`) |
| 5 Weather | `weather_alert` (direct field) |
| 6 Sources | `sources[]` (direct field) |
| 7 Disclaimer | Static text (prompt-template-enforced) |
| 8 Follow-up | `answer` (markdown) + `metadata.session_id` |
| Language | `metadata.language` (confirms the request `language` was honored) |
| Session continuity | `metadata.session_id`, resent as `session_id` on the next request |

---

## 8. Open Items for Team Sign-off

- [ ] **Auth endpoints** (`/api/auth/register`, `/api/auth/login`) are not in `/docs/api-contract.md` v1.0.0 — Pathum to confirm exact request/response shape before T-20 (Day 5) so Section 3 of this spec can be finalized against real fields, not the T-04.2 draft.
- [ ] **Confidence-label parsing risk (Block 2)**: the UI currently relies on the LLM reliably emitting one of `High`/`Medium`/`Low` inside the markdown `answer` for badge styling, since the raw `confidence` float from the Disease Agent is not re-exposed in the final envelope. Recommend Sanketh either (a) constrain the synthesis prompt to emit a fixed marker token the UI can parse reliably, or (b) add a `diagnosis_confidence_label` field to the orchestrator response envelope in a future contract revision.
- [ ] **"Why?" explanation control (Block 8)**: no field exists yet in the contract for the Responsible AI explanation (T-26). Confirm whether this becomes a new field on the envelope or a separate endpoint.
- [ ] **Feedback control (FR-50)**: no endpoint exists yet for "Was this helpful?" — confirm whether this is in scope for the ten-day build or logged client-side only.
- [ ] Confirm real helpline contact info vs. a generic "Contact your local Agriculture Extension Office" placeholder.
- [ ] Confirm disclaimer wording (Section 4.7) with the full team — currently a draft, not yet contract-frozen text.
