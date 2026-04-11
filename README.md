# AegisCore

## Final product (proposal deliverable)

**AegisCore** is the **final application product** for this project: a **centralized SOC platform MVP**—a **single-tenant web system** (React + TypeScript analyst console, FastAPI backend, PostgreSQL, optional **TensorFlow/Keras** model artifacts for trainable risk scoring). It delivers **monitoring** (Wazuh and Suricata), **alert handling**, **incident investigation workflows**, **explainable AI-assisted risk scoring** (deterministic baseline by default; optional TensorFlow path when enabled), **reporting and export**, and **policy-driven, controlled automated response** with audit trails. The **academic release** implements **only** four **validated** threat detections, listed below.

Canonical wording for reports and panels: **[docs/final-product.md](docs/final-product.md)**.

**Supported detections only** (no others are in scope for this release):

- `brute_force`
- `port_scan`
- `file_integrity_violation`
- `unauthorized_user_creation`

The current academic MVP validates four core threat categories: brute-force attacks, port scans, file integrity violations, and unauthorized user account creation. Additional detection categories are **future roadmap** items, not part of the current implementation.

**Explicitly out of scope** for this project: ransomware-specific pipelines, phishing campaigns, APT hunting, zero-day detection claims, multi-tenant SaaS, and other full commercial-grade SOC features beyond the bounded workflow above.

## Start Here (Examiner Flow)

If you are reviewing AegisCore for final academic submission, use this quick flow:

1. Understand the **final product** (see [docs/final-product.md](docs/final-product.md)):
   - **AegisCore** is the submitted **centralized SOC platform MVP** (web app + backend + data plane)
   - **Academic release** limited to the four **validated** detections listed below
2. Run the platform:
   - `docker compose up --build -d`
   - `docker compose exec api alembic upgrade head`
   - `docker compose exec api python -m app.db.seed`
3. Validate core behavior:
   - `docker compose run --rm --entrypoint pytest api`
   - `npm run lint:web`
   - `npm run build:web`
   - start the API and seed users, then `npm run test:web:e2e` (dev server proxies `/api` to `http://127.0.0.1:8000`)
   - `py -3 scripts/validate_attack_scenarios.py` (expects the same API on port 8000 by default)
4. Review handoff docs:
   - architecture: [docs/architecture.md](docs/architecture.md)
   - project status: [docs/project-status-summary.md](docs/project-status-summary.md)
   - requirement evidence: [docs/requirement-compliance-matrix.md](docs/requirement-compliance-matrix.md)
   - release checklist: [docs/release-readiness.md](docs/release-readiness.md)
   - release candidate note: [docs/release-candidate-note.md](docs/release-candidate-note.md)
   - demo walkthrough: [docs/demo-script.md](docs/demo-script.md)
   - operator and analyst guides:
     - [docs/setup/operator-guide.md](docs/setup/operator-guide.md)
     - [docs/setup/analyst-guide.md](docs/setup/analyst-guide.md)

## Product positioning

**Unified stance:** The **final product** is the **AegisCore** SOC platform MVP above—**enterprise-inspired**, **single-tenant**—with a **transparent academic scope**: this **release** implements **only** the four validated detections below. Validation emphasizes **repeatable fixtures**, **automated tests**, and documented **simulated-attack** scenarios; optional **live Wazuh/Suricata connectors** support evaluation and demonstration environments.

- **Implemented for this MVP**: centralized visibility; log and network ingestion for the four detections only; explainable risk scoring (deterministic baseline + optional TensorFlow trainable path); incident lifecycle and response history; controlled automated response; JWT roles (`admin` / `analyst`); operational reporting and export.
- **Live connectors (evaluation-ready)**: Wazuh authenticated polling includes retries, pagination/checkpointing, dedupe, and status visibility (reference API envelope variants). Suricata live ingestion is **`file_tail` on `eve.json`** with checkpointing, retries, dedupe, and status visibility; authenticated forwarding mode is not implemented in this release.
- **Operational default (evaluation / demonstration)**: with `WAZUH_CONNECTOR_ENABLED=true` and `SURICATA_CONNECTOR_ENABLED=true`, live connectors are the normal path; manual ingestion remains for deterministic regression and panel demos.
- **Validation**: repeatable evidence is fixture- and test-driven; live connector checks are optional where sources are configured.

## Repository Tour

- `apps/web`: React + TypeScript + Tailwind SOC console
- `apps/api`: FastAPI + SQLAlchemy + Alembic backend
- `apps/worker`: worker shell for future background execution
- `ai`: training, inference, datasets, and model artifacts
- `infra/nginx`: local reverse proxy config
- `infra/docker`: Dockerfiles for the local stack
- `scripts`: validation and local helper scripts
- `docs`: architecture, setup, testing, scoring, and release-readiness guides

## Submission Docs

- [Final product definition](docs/final-product.md)
- [Project Status Summary](docs/project-status-summary.md)
- [Demo Script](docs/demo-script.md)
- [Requirement Compliance Matrix](docs/requirement-compliance-matrix.md)
- [Release Readiness](docs/release-readiness.md)
- [Release Candidate Note](docs/release-candidate-note.md)
- [Operator Guide](docs/setup/operator-guide.md)
- [Analyst Guide](docs/setup/analyst-guide.md)
- [Operator Runbook](docs/setup/operator-runbook.md)

## Local Quick Start

1. Copy the example env files if you want local overrides.
2. Start the stack:

```powershell
docker compose up --build -d
```

3. Run migrations and seed local users:

```powershell
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
```

1. Open the platform:

- `http://localhost` through NGINX
- `http://localhost/api/health` through NGINX
- `http://localhost/api/health/live` through NGINX
- `http://localhost/api/health/ready` through NGINX
- `http://localhost:8000/health` direct API
- `http://localhost:8000/health/ready` direct API
- `http://localhost:5173` direct frontend dev server

Default local credentials:

- `admin / AegisCore123!`
- `analyst / AegisCore123!`

For local demos only, override seeded passwords in `.env` before sharing environments:

- `DEV_SEED_ADMIN_PASSWORD`
- `DEV_SEED_ANALYST_PASSWORD`

## Local Validation Commands

Backend:

```powershell
docker compose run --rm --entrypoint pytest api
```

Frontend:

```powershell
npm run lint:web
npm run build:web
```

Browser coverage (API must be listening on `127.0.0.1:8000`; seed users if needed):

```powershell
docker compose exec api python -m app.db.seed
npm run test:web:e2e
```

Four-scenario validation:

```powershell
py -3 scripts/validate_attack_scenarios.py
```

## Dev Authentication Boundary

The browser login boundary is explicit by default, even in development.

- `VITE_ENABLE_DEV_AUTH_BOOTSTRAP=false` is the default local posture.
- Set `VITE_ENABLE_DEV_AUTH_BOOTSTRAP=true` only when you intentionally want the frontend API client to obtain a dev token automatically for local lab work.
- Seeded credentials are still available through the normal `/login` flow whether dev bootstrap is enabled or not.

## Backend Workflow Surface

Role model is intentionally minimal and single-tenant:

- `admin`: full API access, including policy mutation and manual ingestion endpoints
- `analyst`: investigation and reporting access across alerts, incidents, responses, assets, dashboard, and reports
- frontend behavior mirrors this boundary: policy toggle controls are admin-only and analyst sessions see read-only policy state

This MVP ships a **focused admin/analyst model** for single-tenant operations; richer RBAC matrices are a natural extension beyond the academic release.

Current live workflow endpoints:

- `POST /alerts/{id}/acknowledge`
- `POST /alerts/{id}/close`
- `POST /alerts/{id}/link-incident`
- `POST /alerts/{id}/notes`
- `POST /incidents/{id}/transition`
- `POST /incidents/{id}/notes`

Current policy and response endpoints:

- `GET /policies`
- `PATCH /policies/{id}` (`admin` only)
- `GET /responses`

Current reporting endpoints:

- `GET /reports/daily-summary`
- `GET /reports/weekly-summary`
- `GET /reports/alerts/export`
- `GET /reports/incidents/export`
- `GET /reports/responses/export`

Operator notifications (optional): when `NOTIFICATIONS_ENABLED=true`, the backend can deliver administrator alerts via **`log` mode** (audited, no SMTP) or **`smtp` mode** (real email to lab sinks such as MailHog). Triggers cover high-risk scoring, configured incident states, selected response outcomes, and `notify_admin` policy actions. History is persisted in `notification_events` and shown on incident and linked-alert detail plus response history. Scheduled reporting digests are not part of this subsystem.

Current ingestion endpoints:

- `POST /integrations/wazuh/events` (`admin` only)
- `POST /integrations/suricata/events` (`admin` only)
- `GET /integrations/wazuh/connector/status`
- `GET /integrations/suricata/connector/status`

Server-side role enforcement is authoritative; UI restrictions are an operator UX layer and do not replace backend permission checks.

Operational note: in **evaluation and pilot-style deployments**, enable both live connectors when sources are available; treat manual ingestion routes as regression and demonstration tooling.

Operational health endpoints:

- `GET /health` (API + DB health summary)
- `GET /health/live` (process liveness)
- `GET /health/ready` (readiness with DB + connector dependency statuses)

## Safety Notes

- The frontend talks only to backend APIs.
- Raw source payloads are preserved for auditability and debugging.
- Automated response is policy-driven and limited to the supported detection scope.
- Destructive live actions remain blocked unless `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=true`.
- This MVP is **intentionally single-tenant** and optimized for **transparent evaluation**; **multi-tenant SaaS** and **full SOAR-class orchestration** are **out of scope** for the **current academic release** and documented as future-scale directions.

## Documentation Map

- [Final product definition](docs/final-product.md)
- [Architecture](docs/architecture.md)
- [Environment Reference](docs/environment.md)
- [Scoring](docs/scoring.md)
- [Operator Guide](docs/setup/operator-guide.md)
- [Operator Runbook](docs/setup/operator-runbook.md)
- [Analyst Guide](docs/setup/analyst-guide.md)
- [Ubuntu VM lab — live SOC (Wazuh + Suricata)](docs/setup/ubuntu-vm-lab-live-soc.md)
- [Wazuh Live Integration](docs/setup/wazuh-live-integration.md)
- [Suricata Live Integration](docs/setup/suricata-live-integration.md)
- [Notifications Setup](docs/setup/notifications.md)
- [End-to-End Validation](docs/testing/end-to-end-validation.md)
- [Playwright Coverage](docs/testing/playwright-coverage.md)
- [Requirement Compliance Matrix](docs/requirement-compliance-matrix.md)
- [Release Readiness](docs/release-readiness.md)

## Known Limitations

- Live Suricata integration is currently limited to `file_tail` mode for `eve.json`; authenticated forwarding mode is not yet implemented.
- Live Wazuh integration is implemented for common lab endpoint/auth shapes and currently expects a list response or a `data.affected_items`/`data.items` envelope.
- Playwright covers core read workflows, key write flows, one simulated API failure on alert acknowledge, and selected negative paths, but does not cover every possible negative-path mutation branch; some incident-dependent branches are conditionally skipped when no incident candidate is available in seeded runs. The suite currently defines **17** browser tests—see [docs/testing/playwright-coverage.md](docs/testing/playwright-coverage.md).
- The frontend is operational and validated, but still large enough to benefit from additional route-level code splitting over time.

## Future Work

- add authenticated forwarding mode support for Suricata live connector
- improve Wazuh connector compatibility profiles for additional Wazuh endpoint query/filter patterns
- add analyst-role negative-path browser checks for restricted actions
- expand browser coverage for remaining terminal/edge workflow branches
- move selected heavy frontend routes to dynamic imports if bundle size becomes a sustained local problem
- add background replay handling for ingestion failures and broaden lab validation coverage for destructive adapter paths

## Academic Supervision
This project was guided and supervised by Ann Roshanie Appuhamy as part of undergraduate coursework.
