# AegisCore Project Status Summary

## 1. System Overview

AegisCore is a final scoped v1 single-tenant SOC product for SME/lab deployment. It centralizes security event review, alert prioritization, incident investigation, basic automated response, and operational reporting. It is intentionally not positioned as an enterprise cloud/SaaS deployment model.

### Product Positioning

- **Fully implemented for scoped v1**: centralized SOC dashboard, four-detection ingestion/normalization, risk scoring, incident and response recording, basic automated response, authenticated access, and reporting/export.
- **Partially implemented / limited mode (live connectors)**:
  - Wazuh: live polling connector is implemented with auth, retries, pagination, checkpointing, dedupe, and status visibility; compatibility is limited to common upstream envelope variants.
  - Suricata: live connector is implemented for `file_tail` mode on `eve.json` with checkpointing and retry/error handling; authenticated forwarding mode is not yet implemented.
- **Fixture-backed validation baseline**: deterministic regression validation is still primarily fixture-backed, with optional live VM/lab verification.

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
- optional trainable scikit-learn scoring path
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
2. `file_integrity_violation`
3. `port_scan`
4. `unauthorized_user_creation`

No additional detection categories should be claimed as implemented in the current project state.

## 5. Validation Summary

The project has been validated across the implemented end-to-end flow for the four supported detections:

- source event ingestion
- normalization into the alert schema
- risk scoring
- incident creation or grouping
- automated response behavior
- report visibility
- frontend route and detail visibility

Validation uses real backend ingestion/workflow APIs. The default repeatable proof path is fixture-backed, with optional live-connector VM/lab checks.

## 6. Test Summary

At the current validated state:

- backend test suite: passing in local Docker validation runs
- frontend lint: passing
- frontend production build: passing
- Playwright suite: `9` passing browser tests
- four-scenario validation script: successful across all supported detections

The validated commands are:

```powershell
docker compose run --rm --no-deps api pytest
npm run lint:web
npm run build:web
npm run test:web:e2e
py -3 scripts/validate_attack_scenarios.py
```

## 7. Reports And Export Summary

The reporting layer is practical and SME-oriented rather than enterprise-heavy. The backend exposes:

- `GET /reports/daily-summary`
- `GET /reports/weekly-summary`
- `GET /reports/alerts/export`
- `GET /reports/incidents/export`
- `GET /reports/responses/export`

The frontend Reports page uses those real endpoints for summary cards, distributions, top assets, and export actions. Export formats are limited to CSV and JSON.

## 8. Known Limitations

- role model is intentionally simple (`admin` + `analyst`) and does not provide enterprise RBAC custom role authoring
- deterministic validation still relies heavily on fixture-backed scenarios even though live connectors and adapters are implemented
- Playwright covers core read workflows and major write workflows, but not every negative-path role/edge branch
- destructive live response behavior remains safety-gated and disabled by default
- the worker service is still a future-facing shell rather than a mature asynchronous execution subsystem
- scheduled reporting and PDF export are not implemented

## 9. Future Improvements

- extend Wazuh compatibility profiles for additional upstream envelope/query variants
- add Suricata authenticated forwarding mode in addition to `file_tail`
- expand browser coverage for analyst-role restriction and terminal/edge workflow assertions
- add replay handling for ingestion failures
- broaden repeatable lab validation coverage for intentionally gated destructive adapter paths
- continue incremental frontend code splitting if the dashboard grows
- extend reporting only where it remains practical for SME operations

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
- operator workflow: [operator-guide.md](setup/operator-guide.md)
- analyst workflow: [analyst-guide.md](setup/analyst-guide.md)
- validation: [end-to-end-validation.md](testing/end-to-end-validation.md)
- browser coverage: [playwright-coverage.md](testing/playwright-coverage.md)

### Practical Handoff Points

- the frontend currently assumes backend ownership of all integrations and scoring contracts
- the four supported detections are the project boundary and should remain explicit in any review discussion
- normal VM/lab operations should run connector-driven ingestion; manual ingestion endpoints are kept for test/demo tooling
- dev auth bootstrap is opt-in and should usually remain disabled for realistic testing
- local validation commands are stable and should be rerun before demos or submission packaging

### Honest Project Position

AegisCore is a final scoped v1 product for SME/lab review and operation. It demonstrates an end-to-end SOC workflow with real backend logic and real frontend integration, with clearly documented limits around connector compatibility breadth, deeper edge-path browser coverage, and production-style hardening.
