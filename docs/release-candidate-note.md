# Release Candidate Note

**AegisCore is the final scoped v1 product for single-tenant SME/lab deployment.**

**As of documentation alignment (2026-04-09) and the last full-stack recorded run (2026-04-08), this repository is the final scoped v1 submission and release candidate** unless a new blocker is discovered. Post–release-candidate changes should be treated as blocker-only remediation, with the full verification sequence re-run and these docs updated. Re-run Docker-backed pytest, Playwright (now **17** tests in tree), and `validate_attack_scenarios.py` on your machine before the viva if you need a single fresh snapshot for all five gates.

## Product stance

- **Final scoped v1 product** for this project: **single-tenant**, **SME/lab**; **not an enterprise commercial SOC platform**.
- Threat scope is **only** the four supported detections: `brute_force`, `file_integrity_violation`, `port_scan`, `unauthorized_user_creation`. Not in scope: ransomware/phishing/APT/zero-day products, large-scale enterprise claims, or full commercial SOC parity.
- Live Wazuh and Suricata connectors are implemented for lab use with documented limits; deterministic acceptance still relies primarily on fixture-backed APIs and browser tests; VM/lab simulated-attack validation is documented separately.

## Verification record pointer

Authoritative command results and environment expectations are recorded in:

- [release-readiness.md](release-readiness.md)
- [final-submission-checklist.md](final-submission-checklist.md)
- [testing/playwright-coverage.md](testing/playwright-coverage.md)
