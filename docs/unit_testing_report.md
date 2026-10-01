# T-27 Unit Testing Report — Agents and Data Layer

## 1. Overview

This report documents the unit testing completed for **T-27 — Unit Testing: Agents and Data Layer** of the Agri-Advisor project.

The objective of T-27 was to verify that the major AI agents and structured data layer behave correctly in isolation, including important safety and edge-case paths.

The required testing areas were:

- RAG Agent retrieval and ranking
- Crop Advisory Agent eight-section output
- Disease Agent ranking and tie handling
- Disease Agent no-diagnosis and low-confidence safety paths
- Knowledge-base loaders and JSON schema validity
- Weather disease and pest risk thresholds
- Weather alert and pesticide-safety behavior

The project requirement was a minimum of **25 pytest unit tests** with a recorded pass rate.

---

## 2. Test Environment

| Item | Value |
|---|---|
| Operating System | Windows |
| Python Version | 3.12.0rc3 |
| pytest Version | 9.1.1 |
| pluggy Version | 1.6.0 |
| Test Directory | `tests/` |
| pytest Configuration | `pytest.ini` |
| Full-Suite Command | `python -m pytest -v` |

The pytest configuration allows the complete test suite to be executed using a single command from the project root.

---

## 3. T-27 Test Summary

| Test Area | Test File | Tests | Result |
|---|---|---:|---|
| RAG Agent | `tests/test_rag_agent_D27.py` | 16 | PASS |
| Crop Advisory Agent | `tests/test_crop_agent_D27.py` | 10 | PASS |
| Disease Agent | `tests/test_disease_agent_D27.py` | 10 | PASS |
| Knowledge Base / Data Loaders | `tests/test_data_loaders_D27.py` | 20 | PASS |
| Weather Agent | `tests/test_weather_agent_D27.py` | 23 | PASS |
| **Total T-27 Tests** |  | **79** | **79/79 PASS** |

### T-27 Pass Rate

**79 passed / 79 executed = 100%**

The T-27 suite therefore exceeds the required minimum of 25 unit tests.

---

## 4. T-27.1 — pytest Setup

pytest was configured at the project level using `pytest.ini`.

The test structure supports execution from the repository root and automatically discovers test modules inside the `tests/` directory.

The complete test suite can be executed using:

```powershell
python -m pytest -v
```

**Status: PASS**

---

## 5. T-27.2 — RAG Agent Testing

Test file:

```text
tests/test_rag_agent_D27.py
```

A total of **16 tests** were implemented for the RAG Agent.

The following areas were tested:

| Area | Verification |
|---|---|
| Distance conversion | ChromaDB distance is correctly converted to similarity |
| Rice crop aliases | Rice and paddy aliases are normalized correctly |
| Chilli crop aliases | Chilli and chili aliases are normalized correctly |
| Empty crop filter | `None` crop filter is handled safely |
| Retrieval top-K | Requested `top_k` value is passed correctly |
| Metadata filtering | Crop and category filters are created correctly |
| Ranking order | Retrieved documents remain ordered by similarity |
| Source metadata | Document ID, title, crop, category, source and region are returned correctly |
| Empty retrieval | Empty ChromaDB results are handled safely |
| Minimum score filtering | Low-similarity results are rejected |
| Top similarity | Highest similarity is calculated correctly |
| Empty similarity | Empty result returns a safe similarity value |
| Context construction | Retrieved sources are converted into RAG context |
| Empty context | Empty source list returns empty context |
| Keyword fallback | Keyword retrieval activates correctly |
| Exact-title rescue | Explicit disease titles can rescue an incorrect semantic top result |

### Result

```text
16 passed
0 failed
```

**Status: PASS**

---

## 6. T-27.3 — Crop Advisory Agent Testing

Test file:

```text
tests/test_crop_agent_D27.py
```

A total of **10 tests** were implemented for the Crop Advisory Agent.

All eight required advisory sections were tested:

| Section | Result |
|---|---|
| 1. Recommended Varieties | PASS |
| 2. Land Preparation | PASS |
| 3. Planting Schedule | PASS |
| 4. Fertilizer Management | PASS |
| 5. Water Management | PASS |
| 6. Weed Management | PASS |
| 7. Harvesting and Post-Harvest | PASS |
| 8. Crop Rotation and Intercropping | PASS |

Additional tests verified:

- Crop-name normalization
- Correct variety data handling
- Planting-window handling
- Four-stage rice fertilizer schedule
- Alternate Wetting and Drying water-management information
- Complete advisory composition
- Presence of all eight advisory sections in the final response

### Result

```text
10 passed
0 failed
```

**Status: PASS**

---

## 7. T-27.4 — Disease Agent Ranking and Tie Handling

Test file:

```text
tests/test_disease_agent_D27.py
```

The Disease Agent ranking tests verified:

| Behavior | Result |
|---|---|
| Farmer symptoms correctly match disease symptoms | PASS |
| Higher-confidence disease is ranked first | PASS |
| Confidence score is calculated correctly | PASS |
| Exact ranking tie is handled consistently | PASS |
| Rice yellow-spots Bacterial Leaf Blight tie-breaking behavior works | PASS |
| Empty symptom input returns no ranked diseases | PASS |

### Symptom Ranking

The ranking function calculates confidence using the number of matched farmer symptoms relative to the total number of supplied symptoms.

The ranking also considers an evidence score based on overlapping symptom tokens.

### Tie Handling

An explicit tie test was included.

When two diseases have identical confidence and evidence scores, Python's stable sorting behavior preserves their original candidate order unless a defined disease-specific tie-breaking condition applies.

A special test also verified the implemented Bacterial Leaf Blight prioritization behavior for rice yellow-spot symptoms.

**Status: PASS**

---

## 8. T-27.5 — Disease Safety Paths

The Disease Agent safety behavior was tested for both the **no-diagnosis** and **low-confidence** paths.

### 8.1 No-Diagnosis Path

When no candidate disease matches the submitted symptoms, the system returns:

```text
Disease: No diagnosis
Confidence: 0.0
Severity: Low
```

The response contains:

- No chemical treatment
- No organic treatment
- No cultural treatment
- No confirmed symptoms
- No differential diagnoses

This prevents the system from guessing a disease when there is insufficient evidence.

### 8.2 Low-Confidence Path

The Disease Agent uses the following threshold:

```python
LOW_CONFIDENCE_THRESHOLD = 0.5
```

When the highest-ranked disease has a confidence score below `0.5`, the system returns:

```text
Uncertain diagnosis
```

The low-confidence path was verified to:

- Return the calculated confidence score
- Use Low severity
- Avoid chemical treatment recommendations
- Avoid organic treatment recommendations
- Avoid cultural treatment recommendations
- Provide alternative candidate diseases
- Recommend confirmation from a local agricultural extension officer

This protects the farmer from receiving potentially unsafe treatment advice when the system is not sufficiently confident.

### Result

All Disease Agent T-27 tests:

```text
10 passed
0 failed
```

**Status: PASS**

---

## 9. T-27.6 — Knowledge Base and Data Loader Testing

Test file:

```text
tests/test_data_loaders_D27.py
```

A total of **20 executed test cases** were completed.

The following structured JSON files were validated:

| File | Result |
|---|---|
| `disease_kb.json` | PASS |
| `treatment_db.json` | PASS |
| `crop_db.json` | PASS |
| `best_practices.json` | PASS |
| `seasonal_calendar.json` | PASS |

### 9.1 JSON Validity

Each structured data file was opened using Python's JSON parser.

The tests confirmed that:

- Each file exists
- Each file contains valid JSON
- Each root object is a dictionary
- Each database contains records

### 9.2 Disease Knowledge Base Schema

Disease records were checked for the following required fields:

```text
name
scientific_name
crop
symptoms
severity
region
source
```

The tests also confirmed that:

- `symptoms` is a non-empty list
- `region` is stored as a list
- Disease records have valid keys
- Disease coverage meets the project minimum

### 9.3 Disease and Crop Coverage

The data layer was verified to contain:

- At least 12 disease records
- At least 5 represented crops

This satisfies the minimum structured-data coverage requirement.

### 9.4 Treatment Database Schema

Treatment records were checked for:

```text
chemical
organic
cultural
prevention
```

Each category was verified to use a list structure.

### 9.5 Crop Database Schema

The crop database was verified to contain at least five crops.

Each crop was checked for a `varieties` list.

Each variety was verified to contain a valid variety name.

### 9.6 Best-Practices Schema

Best-practice records were checked for the following categories:

```text
planting
fertilizer
irrigation
pest_disease_management
harvesting
rotation
sustainability
```

Each category was verified to contain a list.

### 9.7 Seasonal Calendar

The seasonal calendar was verified to contain both:

```text
maha
yala
```

Each season was also checked for a valid:

```text
crop_windows
```

structure.

### 9.8 Loader Helper Functions

Tests verified the correct behavior of helper functions including:

- `get_disease()`
- `get_diseases_by_crop()`
- `get_treatment()`
- `get_crop_varieties()`
- `get_planting_window()`
- `get_database_summary()`

Known rice disease, treatment, maize variety, and Maha planting-window records were successfully retrieved.

### 9.9 Error Handling

The data loader was tested against two important error conditions.

Missing file:

```text
FileNotFoundError
```

Invalid JSON:

```text
ValueError
```

Both error paths behaved correctly.

### Result

```text
20 passed
0 failed
```

**Status: PASS**

---

## 10. T-27.7 — Weather Risk Threshold Testing

Test file:

```text
tests/test_weather_agent_D27.py
```

A total of **23 tests** were executed.

### 10.1 Risk-Level Thresholds

The shared risk-scoring utility uses the following thresholds:

| Score | Risk Level |
|---:|---|
| `< 0.60` | Low |
| `0.60 – 0.84` | Moderate |
| `0.85 – 0.94` | High |
| `>= 0.95` | Critical |

The following exact boundary values were explicitly tested:

```text
0.00
0.59
0.60
0.84
0.85
0.94
0.95
1.00
```

All boundary tests passed.

### 10.2 Score Bounding

Risk scores are bounded between `0.0` and `1.0`.

Tests confirmed:

```text
1.25 -> 1.00
-0.25 -> 0.00
```

### 10.3 Disease Risk Prediction

Disease-risk calculation considers:

```text
Temperature between 20 C and 32 C
Humidity >= 80%
Rainfall >= 5 mm
Combined warm and humid conditions
```

Tests were created for:

- Low disease risk
- Moderate disease risk
- High disease risk
- Critical disease risk

The Critical test also verified that a raw score above `1.0` is correctly limited to `1.0`.

### 10.4 Pest Risk Prediction

Pest-risk calculation considers:

```text
Temperature between 25 C and 35 C
Humidity between 60% and 85%
Rainfall below 5 mm
```

Tests were created for:

- Low pest risk
- Moderate pest risk
- High pest risk

### 10.5 Weather Alert Thresholds

The following weather alert boundaries were explicitly tested:

| Condition | Threshold | Result |
|---|---:|---|
| Heavy rain watch | 25 mm over 3 days | PASS |
| Heavy rain warning | 50 mm over 3 days | PASS |
| Flood emergency | 50 mm in one day | PASS |
| High wind | 40 km/h | PASS |
| Extreme heat | 38 C | PASS |

A test also verified that rainfall below the 25 mm threshold does not produce a heavy-rain alert.

### 10.6 Heavy-Rain Pesticide Safety Rule

The advisory logic was tested to confirm that pesticide application is postponed when a heavy-rain alert is active.

The test verified that the generated advisory includes guidance to:

```text
postpone pesticide applications
```

and that the disease-risk recommendation is modified to:

```text
defer pesticide applications
```

until the rainfall has passed and foliage is dry.

### Result

```text
23 passed
0 failed
```

**Status: PASS**

---

## 11. Dedicated T-27 Test Results

The dedicated T-27 tests produced the following results:

| Component | Tests Passed |
|---|---:|
| RAG Agent | 16 |
| Crop Advisory Agent | 10 |
| Disease Agent | 10 |
| Data Layer | 20 |
| Weather Agent | 23 |
| **Total** | **79** |

Final dedicated T-27 result:

```text
79 passed
0 failed
0 errors
```

### Dedicated T-27 Pass Rate

```text
79 / 79 = 100%
```

The project requirement of at least 25 unit tests was therefore exceeded by 54 tests.

---

## 12. Full Repository Test Execution

After completing the dedicated T-27 tests, the complete Agri-Advisor repository test suite was executed using:

```powershell
python -m pytest -v
```

pytest successfully discovered:

```text
216 items
```

Final result:

```text
216 passed, 1 warning in 90.11s
```

### Full-Suite Summary

| Metric | Result |
|---|---:|
| Tests Collected | 216 |
| Tests Passed | 216 |
| Tests Failed | 0 |
| Errors | 0 |
| Warnings | 1 |
| Execution Time | 90.11 seconds |
| Pass Rate | **100%** |

The full repository therefore executes successfully using a single pytest command.

---

## 13. Initial Environment Issue and Resolution

During the first complete repository test run, pytest collection stopped because the local Python environment did not contain the `python-jose` dependency.

The error was:

```text
ModuleNotFoundError: No module named 'jose'
```

The issue affected tests importing authentication and security functionality because those modules use:

```python
from jose import JWTError, jwt
```

The dependency was installed using:

```powershell
python -m pip install "python-jose[cryptography]"
```

The installation was verified before rerunning the suite.

After installing the missing dependency, the complete repository test suite executed successfully.

### Issue Classification

| Item | Value |
|---|---|
| Type | Environment dependency |
| Application defect | No |
| Test defect | No |
| Resolution | Install `python-jose[cryptography]` |
| Current Status | Resolved |

---

## 14. Warnings and Open Issues

### 14.1 Test Failures

There are currently no failed tests.

```text
Failures: 0
```

### 14.2 Test Errors

There are currently no unresolved test errors.

```text
Errors: 0
```

Therefore, there are no failure-related defects requiring assignment from T-27.

### 14.3 Non-Blocking Warning

The final full test run produced one warning:

```text
StarletteDeprecationWarning:
Using httpx with starlette.testclient is deprecated;
install httpx2 instead.
```

This warning did not cause any test failure and does not currently affect application functionality.

| Item | Value |
|---|---|
| Type | Dependency deprecation warning |
| Severity | Low |
| Current Impact | None |
| Test Impact | None |
| Status | Open / Non-blocking |
| Recommended Action | Update the compatible HTTP testing dependency stack during future maintenance |

---

## 15. T-27 Completion Checklist

| Subtask | Description | Status |
|---|---|---|
| T-27.1 | Set up pytest and test folder structure | PASS |
| T-27.2 | Test RAG retrieval, ranking order, source return and empty results | PASS |
| T-27.3 | Test Crop Advisory Agent across all eight output sections | PASS |
| T-27.4 | Test Disease Agent ranking function including tie case | PASS |
| T-27.5 | Test no-diagnosis and low-confidence safety paths | PASS |
| T-27.6 | Test knowledge-base loaders and JSON schema validity | PASS |
| T-27.7 | Test weather risk-scoring thresholds | PASS |
| T-27.8 | Record pass/fail results and open issues | PASS |

---

## 16. Final Result

### T-27 Dedicated Test Suite

```text
Tests:     79
Passed:    79
Failed:    0
Errors:    0
Pass Rate: 100%
```

### Complete Repository Test Suite

```text
Tests:     216
Passed:    216
Failed:    0
Errors:    0
Warnings:  1
Pass Rate: 100%
Time:      90.11 seconds
```

---

## 17. Conclusion

T-27 — **Unit Testing: Agents and Data Layer** has been completed successfully.

The implementation produced **79 dedicated T-27 unit tests**, significantly exceeding the required minimum of 25 tests.

The tests successfully verified:

- RAG retrieval behavior
- Similarity ranking
- Source metadata handling
- Empty-result handling
- Keyword fallback
- Exact-title rescue
- All eight Crop Advisory sections
- Disease symptom matching
- Disease confidence calculation
- Disease ranking
- Disease tie handling
- No-diagnosis safety behavior
- Low-confidence safety behavior
- Treatment suppression during uncertain diagnosis
- Structured JSON validity
- Disease database schema
- Treatment database schema
- Crop database schema
- Best-practice schema
- Seasonal calendar schema
- Data-loader helper functions
- Data-loader error handling
- Weather risk boundaries
- Disease-risk prediction
- Pest-risk prediction
- Heavy-rain thresholds
- Flood thresholds
- High-wind thresholds
- Extreme-heat thresholds
- Heavy-rain pesticide safety behavior

All **79 dedicated T-27 tests passed**.

The complete repository was then tested using a single pytest command, resulting in:

```text
216 / 216 tests passed
```

with a full-suite pass rate of:

```text
100%
```

There are currently no critical test failures or unresolved test errors.

The only remaining item is a non-blocking dependency deprecation warning related to the Starlette/FastAPI testing stack.

**Overall T-27 Status: COMPLETE**