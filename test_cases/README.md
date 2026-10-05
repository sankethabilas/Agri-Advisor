# Agri-Advisor Security Test Suite (Student 1 Component)

This directory contains standalone Python test scripts corresponding to the 15 security test cases documented in [`docs/Security_Testing_Test_Suite_Student1.pdf`](../docs/Security_Testing_Test_Suite_Student1.pdf).

## Prerequisites

Ensure the backend server is running locally:
```bash
python -m uvicorn orchestrator.main:app --reload --host 127.0.0.1 --port 8000
```

---

## Running Test Cases

### 1. Run All 15 Test Cases
To execute the complete security evaluation matrix and generate a terminal summary report:
```bash
python test_cases/run_all.py
```

### 2. Run Individual Test Cases via Terminal
You can run any single test case independently from the command line:

| Test ID | Script Path | Category |
| :--- | :--- | :--- |
| **T01** | `python test_cases/test_case_01_direct_prompt_injection.py` | Direct Prompt Injection |
| **T02** | `python test_cases/test_case_02_instruction_override.py` | Instruction Override |
| **T03** | `python test_cases/test_case_03_role_manipulation.py` | Role Manipulation / Persona Hijack |
| **T04** | `python test_cases/test_case_04_safety_bypass_jailbreak.py` | Safety Bypass / Ethical Audit Jailbreak |
| **T05** | `python test_cases/test_case_05_prompt_leakage.py` | Direct Prompt Leakage |
| **T06** | `python test_cases/test_case_06_instruction_extraction.py` | Indirect Instruction Extraction |
| **T07** | `python test_cases/test_case_07_context_delimiter_spoofing.py` | Context Delimiter Spoofing |
| **T08** | `python test_cases/test_case_08_multi_turn_manipulation.py` | Multi-Turn Context Manipulation |
| **T09** | `python test_cases/test_case_09_indirect_prompt_injection.py` | Indirect Prompt Injection |
| **T10** | `python test_cases/test_case_10_prompt_obfuscation_base64.py` | Prompt Obfuscation (Base64) |
| **T11** | `python test_cases/test_case_11_conflicting_instructions.py` | Conflicting Instructions |
| **T12** | `python test_cases/test_case_12_social_engineering_authority.py` | Social Engineering & Authority Spoofing |
| **T13** | `python test_cases/test_case_13_hypothetical_fictional_jailbreak.py` | Hypothetical / Fictional Jailbreak |
| **T14** | `python test_cases/test_case_14_repetition_persistence_attack.py` | Repetition & Persistence Attack |
| **T15** | `python test_cases/test_case_15_prompt_robustness_perturbation.py` | Prompt Robustness Perturbation |

---

## Output Format
Each individual script prints:
- Test ID, Title, Category, and Severity
- Exact adversarial payload sent to the orchestrator
- Server response status code and latency
- Technical analysis of defense mechanism triggered
- Clear `[PASS - DEFENSE INTACT]` or `[FAIL - VULNERABILITY DETECTED]` status
