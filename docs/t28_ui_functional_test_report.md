# T-28 UI, Usability and Functional Test Report

| Field        | Value                      |
| ------------ | -------------------------- |
| Member       | Ishira                     |
| Priority     | High                       |
| Area         | WA-8                       |
| Dependencies | T-24, T-17                 |
| Test date    | 2026-09-30                 |
| Status       | **FAIL - release blocked** |

## 1. Scope and evidence

This pass maps the user-facing requirements in [ui-spec.md](ui-spec.md) to the register, login, query, advisory response, language, and logout flows. The intended user is a farmer with limited formal education using a phone.

Evidence collected:

- Focused automated suite: `44 passed, 1 failed` for `tests/test_api_contract_t29.py`, `tests/test_resilience_t25.py`, and `tests/test_responsible_ai_t26.py`, run with the repository on `PYTHONPATH`.
- Desktop browser smoke check: Streamlit loaded the error page instead of the auth screen; visible error was `ModuleNotFoundError: No module named 'utils'` at `ui/app.py` line 27.
- Mobile browser smoke check: same error at a 390 x 844 viewport. The screenshot was captured in the browser session as `ui-startup-error-mobile.png`; the desktop capture was `ui-startup-error-desktop.png`. The browser capture service did not persist PNG files into the workspace.
- Static implementation evidence: `ui/app.py` imports `utils.i18n` before inserting the repository root into `sys.path`; the query district is a required `selectbox` with no blank option; auth copy visibly uses `Username`, `Account Credentials`, and `Client-side validation`.

Result labels: **PASS** means exercised with evidence; **FAIL** means the behavior was exercised and did not meet the requirement; **BLOCKED** means a prerequisite defect prevented execution.

## 2. Functional checklist mapped to requirements

| ID       | Requirement / scenario                     | Expected result                                                                                | Result  | Evidence                                                                                                       |
| -------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------- | ------- | -------------------------------------------------------------------------------------------------------------- |
| FR-UI-01 | Register with valid details                | Account is created and user enters the query flow                                              | BLOCKED | UI startup error; DEF-T28-01                                                                                   |
| FR-UI-02 | Register with missing/invalid fields       | Plain-language inline validation identifies the field                                          | BLOCKED | UI startup error; DEF-T28-01                                                                                   |
| FR-UI-03 | Login with valid credentials               | User is authenticated and query screen is shown                                                | BLOCKED | UI startup error; DEF-T28-01                                                                                   |
| FR-UI-04 | Login with invalid credentials             | Friendly error is shown and user remains on login                                              | BLOCKED | UI startup error; DEF-T28-01                                                                                   |
| FR-UI-05 | Authenticated query with district and crop | Request is submitted with user, district, language, crop, and session                          | PASS    | Contract suite response validation passed; implementation traced in `ui/app.py`                                |
| FR-UI-06 | Empty query                                | Query is rejected locally with a plain-language message                                        | PASS    | `ui/app.py` checks `not query_text.strip()` before API call; `err_empty_query` exists in all three locales     |
| FR-UI-07 | Very long query                            | Input is limited to 1,000 characters and does not submit excess text                           | PASS    | `st.text_area(..., max_chars=1000)` in `ui/app.py`; contract validation tests passed                           |
| FR-UI-08 | Missing location                           | User can leave location empty and receives a field-level validation message                    | FAIL    | District has a default and no blank option; scenario cannot be exercised from the UI; DEF-T28-04               |
| FR-UI-09 | Advisory success response                  | Response renders the documented blocks and session ID                                          | BLOCKED | UI startup error; renderer has structured and legacy paths                                                     |
| FR-UI-10 | Complete advisory response                 | Diagnosis, treatment, prevention, weather, sources, disclaimer, follow-up, and feedback render | BLOCKED | UI startup error; structured renderer present                                                                  |
| FR-UI-11 | Partial advisory response                  | Missing optional blocks are omitted without a crash and service update remains understandable  | PASS    | `tests/test_resilience_t25.py` passed; renderer uses optional block guards                                     |
| FR-UI-12 | Error response                             | Technical error details are not the primary farmer-facing message                              | BLOCKED | UI startup error; error renderer could not be reached                                                          |
| FR-UI-13 | Logout                                     | Token and conversation state are cleared and login is shown                                    | BLOCKED | UI startup error; logout implementation exists in `ui/app.py` and `ui/auth.py`                                 |
| FR-UI-14 | Session continuity                         | Follow-up retains `metadata.session_id`                                                        | PASS    | Contract response includes session metadata; `ui/app.py` persists it before rendering                          |
| FR-UI-15 | Tampered token                             | API rejects the request with HTTP 401                                                          | FAIL    | Contract suite failed: tampered JWT returned HTTP 200; DEF-T28-02                                              |
| FR-UI-16 | Missing RAG dependency                     | System reports a safe degraded response or installation is complete                            | FAIL    | Test logs show `ModuleNotFoundError: sentence_transformers`; response degraded with service update; DEF-T28-03 |

## 3. Advisory rendering matrix

| Response fixture/state                  | Expected                                                           | Result  | Evidence                                                 |
| --------------------------------------- | ------------------------------------------------------------------ | ------- | -------------------------------------------------------- |
| Complete structured response            | All required blocks render in order                                | BLOCKED | Cannot load app because of DEF-T28-01                    |
| Partial response, no weather or sources | Missing blocks omitted cleanly                                     | PASS    | Resilience suite passed; renderer checks optional values |
| Error response 400/401/500              | Friendly message, no raw request ID or stack trace as primary text | BLOCKED | UI startup error prevents interaction                    |

## 4. Language and script matrix

| Locale         | Static UI strings              | Script rendering         | English fallback                   | Result  |
| -------------- | ------------------------------ | ------------------------ | ---------------------------------- | ------- |
| English (`en`) | Implemented in `utils/i18n.py` | Not reachable in live UI | Baseline                           | BLOCKED |
| Sinhala (`si`) | Implemented in `utils/i18n.py` | Not reachable in live UI | Translator fallback is implemented | BLOCKED |
| Tamil (`ta`)   | Implemented in `utils/i18n.py` | Not reachable in live UI | Translator fallback is implemented | BLOCKED |

The code-level fallback contract is present: translation failures return the original English string and a warning. Live script rendering remains unverified until DEF-T28-01 is fixed.

## 5. Viewport and usability pass

| Viewport / criterion           | Result  | Evidence                                                                                                 |
| ------------------------------ | ------- | -------------------------------------------------------------------------------------------------------- |
| Desktop viewport               | FAIL    | Startup error captured in browser session                                                                |
| 390 x 844 mobile viewport      | FAIL    | Same startup error captured in browser session                                                           |
| No jargon                      | FAIL    | Auth screen source uses `Username`, `Account Credentials`, and `Client-side validation`; DEF-T28-05      |
| Readable text                  | BLOCKED | Cannot inspect rendered screen while app fails at startup                                                |
| Minimal steps                  | BLOCKED | Cannot complete the login to query flow                                                                  |
| High contrast / large controls | BLOCKED | CSS declares 1rem base labels and full-width submit buttons, but live visual verification is unavailable |

## 6. Defect summary

| Defect                                                                                            | Severity | Owner             | Status |
| ------------------------------------------------------------------------------------------------- | -------- | ----------------- | ------ |
| DEF-T28-01: Streamlit UI cannot import `utils` when launched from the documented command          | Critical | Ishira            | Open   |
| DEF-T28-02: Tampered JWT accepted by orchestrator                                                 | High     | Pathum / Sanketh  | Open   |
| DEF-T28-03: Missing `sentence_transformers` causes degraded RAG responses in the test environment | Medium   | Danindu / Sanketh | Open   |
| DEF-T28-04: Query location is never empty, so missing-location validation is absent               | Medium   | Ishira            | Open   |
| DEF-T28-05: Auth copy contains technical/jargon-heavy labels                                      | Low      | Ishira            | Open   |

Full assignments and reproduction details are in [issue_tracker.md](issue_tracker.md).

## 7. Completion decision

T-28 does **not** meet completion criteria. Every screen could not be exercised because the UI startup failure blocks the complete user journey, and the tampered-token contract test is failing. Re-test all blocked scenarios, capture persisted desktop/mobile screenshots, and close the five defects before marking this task complete.

🔴 Testing commands - 
From the project root in PowerShell:

```powershell
cd C:\xampp\htdocs\Git_hub\Agri-Advisor
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -q
```

To run only the T-28-related focused tests:

```powershell
python -m pytest -q tests/test_api_contract_t29.py tests/test_resilience_t25.py tests/test_responsible_ai_t26.py
```

To start Streamlit:

```powershell
$env:PYTHONPATH = (Get-Location).Path
streamlit run ui/app.py
```

The error occurs because `utils` is a project-level package, but `app.py` imports it before adding the project root to Python’s import path:

```python
from utils.i18n import ...
```

The later `sys.path.insert(...)` runs too late. Setting `PYTHONPATH` to the repository root makes `utils` discoverable before the app starts.
