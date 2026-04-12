# AegisCore Project Status Summary

## Final product

**AegisCore** is the **final submitted product**: a **centralized SOC platform MVP** (web console + backend + database) covering **monitoring**, **alert handling**, **incident workflows**, **explainable AI-assisted alert prioritization** (baseline + optional **TensorFlow**), **reporting**, and **controlled automated response**. The **academic release** implements **only** **`brute_force`**, **`port_scan`**, **`file_integrity_violation`**, and **`unauthorized_user_creation`**. Full definition: **[final-product.md](final-product.md)**.

## 1. System overview

**AegisCore** is the **submission MVP** named above: **single-tenant**, **enterprise-inspired** in operator workflow, with **centralized visibility**, **alert triage**, **risk-based prioritization**, **incident handling**, **explainable AI-assisted scoring** (deterministic baseline default; optional **TensorFlow** trainable model), **controlled automated response**, and **operational reporting**—aligned with commercial SOC practice while **clearly bounding** the **academic release** to the four listed threats.

**Approved scope** matches the four validated threat categories only: `brute_force`, `port_scan`, `file_integrity_violation`, `unauthorized_user_creation`. The current academic MVP validates four core threat categories: brute-force attacks, port scans, file integrity violations, and unauthorized user account creation; broader categories are **roadmap-only** beyond this implementation. **Beyond this release (documented, not implied):** ransomware/phishing/APT/zero-day product lines; claims of unlimited enterprise rollout; and parity with full commercial SOC suites.

### Product Positioning

- **MVP**: complete backend-owned workflow for the four validated threat categories—ingestion, normalization, scoring, incidents, responses, reporting, authenticated access—delivered as a **substantive commercial-style build**, not a UI-only mock-up.
- **Live connectors (evaluation-ready)**:
  - Wazuh: authenticated live polling with retries, pagination/checkpointing, dedupe, and status (common lab envelopes).
  - Suricata: `file_tail` on `eve.json` with checkpointing and retries; authenticated forwarding not implemented.
- **Validation**: deterministic regression is primarily fixture- and test-backed; **simulated-attack validation** is supported via documented replay and `scripts/validate_attack_scenarios.py`, with optional live connectors in **evaluation** environments.

The implemented platform covers the full backend-owned workflow for a narrow and deliberate scope:

- ingest supported Wazuh and Suricata events
- normalize them into a shared alert schema
- assign explainable risk scores
- group alerts into incidents
- apply policy-driven automated responses
- expose the results through a React SOC console
- support operational reporting and export

## 2. Implemented Feature Summary

### Frontend

- login screen and authenticated analyst workflow
- overview dashboard with live summary cards, charts, and activity panels
- alerts list and alert detail investigation flow
- incidents queue and incident detail investigation flow
- assets or endpoints page
- response history page
- rules or policies page
- reports page with export actions

### Backend

- JWT authentication with `admin` and `analyst` roles
- explicit route-level role protection for sensitive actions:
  - `admin` required for response policy mutation
  - `admin` required for manual ingestion submission
- modular FastAPI service layer with SQLAlchemy, Alembic, and PostgreSQL
- persisted models for users, assets, raw alerts, normalized alerts, incidents, risk scores, response policies, response actions, analyst notes, and audit logs
- live read and write endpoints for alert and incident workflows
- audit-backed notes and state changes

### Scoring

- deterministic baseline scoring for production-safe prioritization
- optional trainable TensorFlow (Keras) scoring path
- persisted score metadata including method, version, explanation, and driver information

### Automated Response

- policy-driven response evaluation after scoring
- dry-run and live execution modes
- support for `block_ip`, `disable_user`, `quarantine_host_flag`, `create_manual_review`, and `notify_admin`
- first-party built-in lab adapters with explicit safety gates
- auditable response history and policy state

### Reporting

- daily summary
- weekly summary
- alert export
- incident export
- response export
- CSV and JSON export support

## 3. Architecture Summary

AegisCore is organized as a monorepo:

- `apps/web`: React + TypeScript + Tailwind frontend
- `apps/api`: FastAPI backend and domain services
- `apps/worker`: reserved for future background execution
- `ai`: training and inference assets for scoring
- `infra/nginx`: local reverse proxy
- `scripts`: validation helpers
- `docs`: operator, analyst, testing, and release documentation

The frontend communicates only with backend APIs. All integration complexity for Wazuh and Suricata stays in the backend. Raw source payloads are preserved for debugging and auditability, while the frontend consumes only normalized backend responses.

## 4. Supported Detections

The current implemented and validated threat scope is intentionally limited to:

1. `brute_force`
2. `port_scan`
3. `file_integrity_violation`
4. `unauthorized_user_creation`

No additional detection categories should be claimed as implemented in the current project state.

## 5. Validation Summary

The project has been validated across the implemented end-to-end flow for the four validated threat categories:

- source event ingestion
- normalization into the alert schema
- risk scoring
- incident creation or grouping
- automated response behavior
- report visibility
- frontend route and detail visibility

Validation uses real backend ingestion/workflow APIs. The default repeatable proof path is fixture-backed, with optional live-connector VM/lab checks.

## 6. Test Summary

**2026-04-09:** Host-only verification confirmed **frontend lint** and **production build** pass (`npm run lint:web`, `npm run build:web`). Backend pytest, Playwright, and `validate_attack_scenarios.py` require Docker and a running seeded API on the examiner machine.

**2026-04-08 (last full five-step recorded run):**

- backend test suite: **103 passed**, 1 warning (`docker compose run --rm --entrypoint pytest api`)
- frontend lint and production build: passing
- Playwright: **16 passed**, 0 skipped (API on `127.0.0.1:8000`, seeded DB)
- four-scenario validation script: successful for all supported detections

**Current Playwright tree:** **17** tests (added `operator-workflows.spec.ts` for deterministic API failure feedback). Re-run `npm run test:web:e2e` to record an updated all-green row after pulling latest.

The validated commands are:

```powershell
docker compose run --rm --entrypoint pytest api
npm run lint:web
npm run build:web
docker compose up -d postgres api
docker compose exec api python -m app.db.seed
npm run test:web:e2e
py -3 scripts/validate_attack_scenarios.py
```

**Environment note:** pytest runs in Docker; Playwright and `validate_attack_scenarios.py` require a running, seeded API (published port **8000** for the default dev proxy and script base URL).

## 7. Reports And Export Summary

The reporting layer is **operational-first** for the MVP (exportable summaries and CSV/JSON) rather than a full analytics platform. The backend exposes:

- `GET /reports/daily-summary`
- `GET /reports/weekly-summary`
- `GET /reports/alerts/export`
- `GET /reports/incidents/export`
- `GET /reports/responses/export`

The frontend Reports page uses those real endpoints for summary cards, distributions, top assets, and export actions. Export formats are limited to CSV and JSON.

## 8. Known Limitations

- role model is intentionally simple (`admin` + `analyst`) and does not provide enterprise RBAC custom role authoring
- deterministic validation still relies heavily on fixture-backed scenarios even though live connectors and adapters are implemented
- Playwright covers core read workflows, major write workflows, one simulated mutation failure path, and selected negative paths, but not every negative-path role/edge branch; incident-dependent browser branches can be conditionally skipped when seeded runs do not produce incident candidates
- destructive live response behavior remains safety-gated and disabled by default
- the worker service is still a future-facing shell rather than a mature asynchronous execution subsystem
- scheduled reporting and PDF export are not implemented; **SMTP/log operator notifications** for critical incidents and policy-driven outcomes are implemented (`docs/setup/notifications.md`) and are separate from scheduled reporting

## 9. Future Improvements

- extend Wazuh compatibility profiles for additional upstream envelope/query variants
- add Suricata authenticated forwarding mode in addition to `file_tail`
- expand browser coverage for analyst-role restriction and terminal/edge workflow assertions
- add replay handling for ingestion failures
- broaden repeatable lab validation coverage for intentionally gated destructive adapter paths
- continue incremental frontend code splitting if the dashboard grows
- extend reporting only where it remains practical for **operator workflows** within the MVP scope

## 10. Local Deployment Summary

The current deployment orientation is local or lab use through Docker Compose:

```powershell
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
```

Default local entrypoints:

- `http://localhost`
- `http://localhost/api/health`
- `http://localhost:8000/health`

Default local credentials:

- `admin / AegisCore123!`
- `analyst / AegisCore123!`

This deployment posture is suitable for project review, demo delivery, and academic evaluation. It should not be described as a finished enterprise deployment model.

## 11. Demo Flow Summary

The recommended demo flow is:

1. sign in through the live login page
2. show the overview dashboard
3. open alerts and highlight live filtering
4. open an alert detail page and show normalized evidence, raw payload, scoring explanation, and related responses
5. open an incident detail page and show linked alerts, notes, timeline, and response history
6. show the responses page and real execution outcomes
7. show the rules or policies page and current safe policy controls
8. show the reports page and export actions
9. demonstrate one short path for each supported detection

The detailed presentation sequence is documented in [demo-script.md](demo-script.md).

## 12. Team Handoff Notes

Requirement traceability for proposal review is documented in [requirement-compliance-matrix.md](requirement-compliance-matrix.md).

### Where to Start

- system overview and commands: [README.md](../README.md)
- architecture: [architecture.md](architecture.md)
- viva prep and likely questions: [viva-qa.md](viva-qa.md)
- operator workflow: [operator-guide.md](setup/operator-guide.md)
- analyst workflow: [analyst-guide.md](setup/analyst-guide.md)
- validation: [end-to-end-validation.md](testing/end-to-end-validation.md)
- browser coverage: [playwright-coverage.md](testing/playwright-coverage.md)
- release candidate stance: [release-candidate-note.md](release-candidate-note.md)

### Practical Handoff Points

- the frontend currently assumes backend ownership of all integrations and scoring contracts
- the four validated threat categories are the project boundary and should remain explicit in any review discussion
- normal **evaluation / demonstration** runs should use connector-driven ingestion when sources are configured; manual ingestion endpoints are kept for regression and panel tooling
- dev auth bootstrap is opt-in and should usually remain disabled for realistic testing
- local validation commands are stable and should be rerun before demos or submission packaging

### MVP position statement (academic release)

AegisCore is a **commercial-style SOC platform MVP** for this project—**single-tenant**, **enterprise-inspired**—with **only** the four **validated** detections in scope. It delivers a complete ingest-to-report pipeline for those threats, with **documented** limits on connector variants, browser edge coverage, and production hardening—appropriate for a **defensible university submission** and **panel-style demos**.

## 13. Viva Quick Defense

### What The System Does

- ingests supported Wazuh and Suricata events
- normalizes data into one alert schema
- scores alerts with baseline rules plus optional TensorFlow model path
- groups and tracks incidents with audit history
- evaluates policy-driven automated responses with safety gates
- provides analyst/admin workflows and reporting/export in one SOC console

### What Is Complete

- full scoped flow for the four validated threat categories is implemented
- backend role enforcement is in place for sensitive mutations
- reporting and export are live and usable
- deterministic validation path is documented and repeatable

### What Is Still Limited

- Suricata live integration is currently `file_tail` mode only
- Wazuh compatibility is broad for common lab envelopes, not all variants
- destructive live response paths are intentionally guarded by explicit flags
- deterministic acceptance validation remains fixture-backed by default

### Why This Is Still A Valid MVP

Within the **declared academic release boundary**, AegisCore provides a complete, testable, and auditable SOC workflow from ingestion to response and reporting for the four validated threat categories. The remaining gaps are **explicitly documented** scope limits—not missing core pipeline functionality for that boundary.
