# Release Candidate Note

**As of the latest recorded verification (2026-04-08), this repository state is the final scoped v1 submission and release candidate** for AegisCore unless a new blocker is discovered. Post–release-candidate changes should be treated as blocker-only remediation, with the full verification sequence re-run and these docs updated.

## Product stance

- Single-tenant SME/lab SOC console, not an enterprise commercial platform.
- Scope is fixed to the four supported detections (`brute_force`, `file_integrity_violation`, `port_scan`, `unauthorized_user_creation`).
- Live Wazuh and Suricata connectors are implemented for lab use with documented limits; deterministic acceptance still relies primarily on fixture-backed APIs and browser tests.

## Verification record pointer

Authoritative command results and environment expectations are recorded in:

- [release-readiness.md](release-readiness.md)
- [final-submission-checklist.md](final-submission-checklist.md)
- [testing/playwright-coverage.md](testing/playwright-coverage.md)
