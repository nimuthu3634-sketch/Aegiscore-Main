# AegisCore

AegisCore is a single-tenant, SME-focused SOC platform prototype. It ingests Wazuh and Suricata events, normalizes them into a shared alert model, scores risk, groups incidents, records analyst workflow, evaluates safe automated-response policies, and exposes the resulting data through a backend-owned web console.

This repository is intentionally scoped to four supported detections only:

- `brute_force`
- `file_integrity_violation`
- `port_scan`
- `unauthorized_user_creation`

## Monorepo Layout

- `apps/web`: React + TypeScript + Tailwind SOC console
- `apps/api`: FastAPI + SQLAlchemy + Alembic backend
- `apps/worker`: worker shell for future background execution
- `ai`: training, inference, datasets, and model artifacts
- `infra/nginx`: local reverse proxy config
- `infra/docker`: Dockerfiles for the local stack
- `scripts`: validation and local helper scripts
- `docs`: architecture, setup, testing, scoring, and release-readiness guides

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

4. Open the platform:

- `http://localhost` through NGINX
- `http://localhost/api/health` through NGINX
- `http://localhost:8000/health` direct API
- `http://localhost:5173` direct frontend dev server

Default local credentials:

- `admin / AegisCore123!`
- `analyst / AegisCore123!`

## Local Validation Commands

Backend:

```powershell
docker compose run --rm --no-deps api pytest
```

Frontend:

```powershell
npm run lint:web
npm run build:web
```

Browser coverage:

```powershell
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

Current live workflow endpoints:

- `POST /alerts/{id}/acknowledge`
- `POST /alerts/{id}/close`
- `POST /alerts/{id}/link-incident`
- `POST /alerts/{id}/notes`
- `POST /incidents/{id}/transition`
- `POST /incidents/{id}/notes`

Current policy and response endpoints:

- `GET /policies`
- `PATCH /policies/{id}`
- `GET /responses`

Current reporting endpoints:

- `GET /reports/daily-summary`
- `GET /reports/weekly-summary`
- `GET /reports/alerts/export`
- `GET /reports/incidents/export`
- `GET /reports/responses/export`

Current ingestion endpoints:

- `POST /integrations/wazuh/events`
- `POST /integrations/suricata/events`

## Safety Notes

- The frontend talks only to backend APIs.
- Raw source payloads are preserved for auditability and debugging.
- Automated response is policy-driven and limited to the supported detection scope.
- Destructive live actions remain blocked unless `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=true`.
- This prototype is intentionally single-tenant and SME-oriented. It does not include multi-tenant SaaS or enterprise SOAR complexity.

## Documentation Map

- [Architecture](/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/docs/architecture.md)
- [Environment Reference](/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/docs/environment.md)
- [Scoring](/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/docs/scoring.md)
- [Operator Guide](/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/docs/setup/operator-guide.md)
- [Analyst Guide](/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/docs/setup/analyst-guide.md)
- [End-to-End Validation](/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/docs/testing/end-to-end-validation.md)
- [Playwright Coverage](/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/docs/testing/playwright-coverage.md)
- [Release Readiness](/Users/nimus/OneDrive/Documents/GitHub/Aegiscore-Main/docs/release-readiness.md)

## Known Limitations

- Live Wazuh and Suricata polling or webhook auth is not implemented yet; current validation uses the real ingestion endpoints with fixture-backed payloads.
- Playwright covers core read workflows and scenario visibility, but not every mutation path.
- The frontend is operational and validated, but still large enough to benefit from additional route-level code splitting over time.

## Future Work

- add live connector polling or webhook integration for Wazuh and Suricata
- expand browser coverage for notes, transitions, and policy mutation flows
- move selected heavy frontend routes to dynamic imports if bundle size becomes a sustained local problem
- add background replay handling for ingestion failures and deeper adapter integrations for live response actions
