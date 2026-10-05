#!/usr/bin/env python3
"""
Master Test Runner for all 15 Security Test Cases (Student 1 Specialization).
Executes each test case sequentially and outputs a formatted terminal matrix.
"""

import sys
import importlib
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from test_cases.common import GREEN, RED, CYAN, BOLD, RESET, DIM

TEST_MODULES = [
    ("T01", "Direct Prompt Injection", "test_cases.test_case_01_direct_prompt_injection"),
    ("T02", "Instruction Override", "test_cases.test_case_02_instruction_override"),
    ("T03", "Role Manipulation", "test_cases.test_case_03_role_manipulation"),
    ("T04", "Safety Bypass Jailbreak", "test_cases.test_case_04_safety_bypass_jailbreak"),
    ("T05", "Prompt Leakage", "test_cases.test_case_05_prompt_leakage"),
    ("T06", "Instruction Extraction", "test_cases.test_case_06_instruction_extraction"),
    ("T07", "Context Delimiter Spoofing", "test_cases.test_case_07_context_delimiter_spoofing"),
    ("T08", "Multi-Turn Manipulation", "test_cases.test_case_08_multi_turn_manipulation"),
    ("T09", "Indirect Prompt Injection", "test_cases.test_case_09_indirect_prompt_injection"),
    ("T10", "Prompt Obfuscation Base64", "test_cases.test_case_10_prompt_obfuscation_base64"),
    ("T11", "Conflicting Instructions", "test_cases.test_case_11_conflicting_instructions"),
    ("T12", "Social Engineering Authority", "test_cases.test_case_12_social_engineering_authority"),
    ("T13", "Hypothetical Fictional Jailbreak", "test_cases.test_case_13_hypothetical_fictional_jailbreak"),
    ("T14", "Repetition Persistence Attack", "test_cases.test_case_14_repetition_persistence_attack"),
    ("T15", "Prompt Robustness Perturbation", "test_cases.test_case_15_prompt_robustness_perturbation"),
]


def main():
    print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}{CYAN}AGRI-ADVISOR SECURITY TEST SUITE RUNNER (15 TEST CASES){RESET}")
    print(f"{DIM}Student 1 Component: Prompt Injection & Jailbreak Analysis{RESET}")
    print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")

    summary_results = []
    start_time = time.time()

    for test_id, name, module_path in TEST_MODULES:
        print(f"\n>>> Running {BOLD}{test_id}: {name}{RESET}...")
        try:
            mod = importlib.import_module(module_path)
            passed = mod.run_test()
            summary_results.append((test_id, name, passed, "Executed"))
        except Exception as e:
            print(f"{RED}[ERROR] Failed executing {test_id}: {e}{RESET}")
            summary_results.append((test_id, name, False, f"Error: {e}"))
        time.sleep(0.5)

    total_time = round(time.time() - start_time, 2)
    passed_count = sum(1 for _, _, passed, _ in summary_results if passed)
    failed_count = len(summary_results) - passed_count

    print(f"\n\n{BOLD}{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}SECURITY TEST SUITE EXECUTION SUMMARY{RESET}")
    print(f"{'='*80}")
    print(f"{BOLD}{'ID':<6} {'Test Case Name':<38} {'Status':<15} {'Evaluation'}{RESET}")
    print(f"{'-'*80}")

    for test_id, name, passed, notes in summary_results:
        status_str = f"{GREEN}PASS [DEFENDED]{RESET}" if passed else f"{RED}FAIL [VULNERABLE]{RESET}"
        eval_str = "Attack neutralized / blocked" if passed else notes
        print(f"{test_id:<6} {name:<38} {status_str:<24} {eval_str}")

    print(f"{'-'*80}")
    print(f"Total Tests: {len(summary_results)} | {GREEN}Passed/Defended: {passed_count}{RESET} | {RED}Failed/Vulnerable: {failed_count}{RESET} | Duration: {total_time}s")
    print(f"Defense Success Rate: {BOLD}{round((passed_count/len(summary_results))*100, 1)}%{RESET}")
    print(f"{'='*80}\n")

    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
