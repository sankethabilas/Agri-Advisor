# Security Audit Report (T-33)

**Audit date:** 2026-09-30  
**Scope:** T-33.1 through T-33.8; dependencies T-21, T-25, and T-29.  
**Verification:** Security suite (9 passed), API contract suite (26 passed), and resilience suite (11 passed). Full-suite collection was blocked because `chromadb` is not installed in the active environment (`tests/test_e2e_integration_t22.py` import error).

## Results

| Subtask | Result | Evidence |
| --- | --- | --- |
| T-33.1 Prompt injection | Pass | Ten crafted override attempts were sent to `/api/orchestrator/process`; each returned `400` before orchestration. The detector now also recognizes safety-guardrail variants, explicit system/developer policy headers, DAN/persona requests, forgotten-rule requests, and requests to disregard earlier instructions. |
| T-33.2 Output filtering | Partial; accepted residual | Unit tests confirm prompt-instruction lines are removed and secret-like output is redacted. A direct probe showed an unrelated cryptocurrency answer is returned unchanged. The current deterministic filter cannot reliably establish semantic relevance without a trusted classifier; the risk is documented and accepted for this audit, not reported as a passing off-topic filter. Grounded synthesis and specialist-source controls remain the primary relevance safeguards. |
| T-33.3 Authentication bypass | Pass | Missing, malformed, wrong-signature forged, and expired tokens returned `401`. Tokens used against another registered user's `user_id` returned `403`. |
| T-33.4 Password handling | Pass | SQLite stores per-user salted PBKDF2-HMAC-SHA256 hashes (310,000 iterations). Registration and login response bodies were checked to ensure they do not contain the submitted password or a password-hash field. |
| T-33.5 Secrets in source, logs, and errors | Pass for tracked files and exercised paths; local config noted | Tracked text files were scanned for credential assignments, common provider-key shapes, and private-key markers; no secret values were found. A synthetic secret sentinel passed through the orchestration failure path and was absent from both the response and captured logs. Error logging now records exception types without exception messages or tracebacks. The ignored, untracked local `.env` contains configured `OPENWEATHER_API_KEY`, `GROQ_API_KEY`, and `JWT_SECRET_KEY` values; values were not displayed or copied, and the file was not modified. `.env` is excluded by `.gitignore`. |
| T-33.6 Input validation | Pass | Tests cover a 1,001-character query, 101-character crop context, 255-character user ID, empty query and district, control-only input, and special characters/Unicode. Invalid boundaries are rejected; supported special characters are accepted and sanitized as applicable. |
| T-33.7 Rate limiting | Pass | Eight rapid requests with a three-request window produced three successful responses followed by `429` responses with `Retry-After`. |
| T-33.8 Findings | Pass with accepted residual above | Confirmed injection and exception-log findings were fixed and regression-tested. The off-topic semantic-filter gap is explicitly recorded as an accepted residual limitation. |

## Changes Made

- Expanded prompt-injection detection for common instruction overrides and persona/policy-header variants.
- Removed exception text and tracebacks from application logs; retained exception type and structured failure context.
- Added maximum lengths for orchestrator identity, session, crop-context, and location fields, and require a non-empty district and identity.
- Added the T-33 authentication, password, prompt-injection, boundary, rate-limit, and log-redaction regression cases to `tests/test_security_t21.py`.

## Residual Risk

The output filter is lexical, not semantic. It removes known unsafe instruction lines and redacts matching secret formats, but cannot reliably determine whether arbitrary generated text is off-topic or agriculturally unsafe. This limitation is accepted and documented for this audit; use of generated pesticide recommendations in production still requires trusted grounding and review controls. The local `.env` remains a private, ignored runtime configuration file; keep it out of commits and rotate its credentials if it is ever exposed.