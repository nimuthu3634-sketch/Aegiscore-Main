# Release Candidate Note

**Final product:** **AegisCore** is the **release candidate artifact**—the **centralized SOC platform MVP** (single-tenant app) that is the **intended end deliverable** for the project. Capability and detection scope: see **[final-product.md](final-product.md)**.

**As of documentation alignment (2026-04-09) and the last full-stack recorded run (2026-04-08), this repository is the submission release candidate** unless a new blocker is discovered. Post–release-candidate changes should be treated as blocker-only remediation, with the full verification sequence re-run and these docs updated. Re-run Docker-backed pytest, Playwright (now **17** tests in tree), and `validate_attack_scenarios.py` on your machine before the viva if you need a single fresh snapshot for all five gates.

## Product stance

- **Commercial-style, enterprise-inspired SOC MVP** for this project: **single-tenant**; **transparent** scope limited to **four validated detections** in the **academic release** (not an unlimited production catalogue).
- Threat scope is **only** the four supported detections: `brute_force`, `file_integrity_violation`, `port_scan`, `unauthorized_user_creation`. **Beyond this release:** ransomware/phishing/APT/zero-day product lines; large-scale rollout maturity claims; or parity with full commercial SOC suites.
- Live Wazuh and Suricata connectors are implemented for **evaluation** use with documented limits; deterministic acceptance still relies primarily on fixture-backed APIs and browser tests; simulated-attack validation is documented separately (including optional **university lab** setups).

## Verification record pointer

Authoritative command results and environment expectations are recorded in:

- [release-readiness.md](release-readiness.md)
- [final-submission-checklist.md](final-submission-checklist.md)
- [testing/playwright-coverage.md](testing/playwright-coverage.md)
