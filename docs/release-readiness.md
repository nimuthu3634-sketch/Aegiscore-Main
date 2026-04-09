# Release Readiness

## Final product declaration

**AegisCore is the final scoped v1 product for single-tenant SME/lab deployment.** It is **not** positioned as an enterprise commercial SOC platform. Threat scope, connectors, notifications, and automated response are **lab-bounded** and **honestly limited** as described in this document and [project-status-summary.md](project-status-summary.md).

## Final Freeze Note

This repository state is the **final scoped v1 release candidate** for academic handoff and SME/lab deployment unless a new blocker is found. Any post–release-candidate change should be treated as **blocker-only** remediation, followed by a full re-run of the verification sequence and an update to this document and related checklists.

See also [release-candidate-note.md](release-candidate-note.md).

## Intended Readiness Level

AegisCore is the **final scoped v1 product** for this project: **single-tenant**, **SME/lab**. It is **not an enterprise commercial SOC platform**. Threat coverage is limited to **`brute_force`**, **`file_integrity_violation`**, **`port_scan`**, and **`unauthorized_user_creation`** (see `README.md` for explicit out-of-scope items).

## Product Positioning

- **Release readiness**: real backend-owned SOC workflows for those four detections only—dashboard, ingestion/normalization, **ML-capable risk scoring** (baseline + optional model), incidents, responses, reporting/export.
- **Live connectors (lab-bounded)**: Wazuh polling and Suricata `file_tail` as documented; not universal vendor coverage or enterprise SOAR.
- **Validation**: deterministic release checks are fixture- and browser/API-test-backed; **VM/lab simulated-attack validation** is documented and repeatable (`scripts/validate_attack_scenarios.py`, operator guides).

## Local Release Checklist

### Platform Startup

- `docker compose up --build -d` succeeds
- database migrations apply cleanly
- local seed command succeeds
- [operator runbook](setup/operator-runbook.md) first-start sequence is executable as written
- `/health` returns healthy API and database status
- `/health/live` returns API liveness
- `/health/ready` reports `ready` with database `up`
- `docker compose ps` shows healthy status for `postgres`, `api`, `web`, and `nginx`

### Security And Access

- `JWT_SECRET_KEY` is set to a non-placeholder value outside throwaway local work
- `VITE_ENABLE_DEV_AUTH_BOOTSTRAP=false` unless temporary local testing explicitly needs it
- destructive automated response remains disabled unless adapters and controls are understood

### Data Flow

- live Wazuh and Suricata connector status endpoints are healthy for configured lab sources
- live connectors are enabled for normal VM/lab ingestion (`WAZUH_CONNECTOR_ENABLED=true`, `SURICATA_CONNECTOR_ENABLED=true`)
- normalized alerts appear in the list and detail UI
- scoring metadata is visible in alert and incident detail
- policy-driven responses appear in response history
- reports include the validated activity
- connector status endpoints remain reachable after API restart
- fixture ingestion remains available only for deterministic test/demo fallback workflows

### Recovery And Continuity

- restarting `api` does not require manual data recovery when `postgres_data` volume is intact
- readiness transitions back to `ready` after restart
- connector status endpoints return healthy or explicit dependency-state details after restart
- migration command remains idempotent (`alembic upgrade head`)
- local backup command for PostgreSQL has been run at least once and restore steps are documented
- docker service logs are bounded locally via `json-file` rotation settings

### Validation Commands

Backend (the API image entrypoint starts the server; override it so `pytest` runs):

```powershell
docker compose run --rm --entrypoint pytest api
```

Frontend:

```powershell
npm run lint:web
npm run build:web
```

Browser (requires a reachable backend for the Vite dev proxy; see **Environment expectations** below):

```powershell
npm run test:web:e2e
```

Scenario validation (requires a running API, default `http://127.0.0.1:8000`):

```powershell
docker compose up -d postgres api
docker compose exec api python -m app.db.seed
py -3 scripts/validate_attack_scenarios.py
```

### Environment expectations (code vs runtime)

- **Backend tests**: run inside Docker against Compose PostgreSQL; no manual API process needed.
- **Frontend lint/build**: run on the host; no database required.
- **Playwright**: starts the Vite dev server and proxies `/api` to **`http://127.0.0.1:8000`**. Start the API (e.g. `docker compose up -d api`) and seed users (`docker compose exec api python -m app.db.seed`) so login and ingestion tests succeed.
- **Attack scenario script**: HTTP client against a live API base URL (`--base-url` or `AEGISCORE_API_BASE_URL`); not the same process as pytest.

## Known Limitations

- deterministic validation still relies heavily on fixtures despite live connector support
- Playwright covers core routes, major write workflows, notification panel surfaces, simulated API failure on alert acknowledge, and selected negative paths; **some tests can still skip** in sparse databases (e.g. no incident or no alert–incident link). The repository currently ships **17** Playwright tests; the last **full-stack** recorded run reported **16 passed, 0 skipped** (before `operator-workflows.spec.ts` was added). Re-run `npm run test:web:e2e` after pulling latest to refresh counts. See [testing/playwright-coverage.md](testing/playwright-coverage.md) for intentional gaps.
- the frontend is operational but still benefits from additional route-level code splitting over time
- no scheduled reporting or digest-email workflow exists; **operator notification delivery** (high-risk / state / response / `notify_admin`) is implemented via persisted `notification_events`, backend `log` mode, and optional SMTP configuration (`docs/setup/notifications.md`)

## Future Work

- add Suricata authenticated forwarding mode beyond `file_tail`
- extend browser coverage to role-restriction and remaining edge-case mutation paths
- add background replay handling for failed ingestions
- broaden lab verification coverage for explicitly gated destructive adapter paths
- continue splitting the frontend bundle if the console grows substantially

## Requirement Traceability

- Proposal/requirement alignment evidence is maintained in [requirement-compliance-matrix.md](requirement-compliance-matrix.md).
- Use that matrix during review to separate implemented behavior from intentional local/lab constraints.

## Latest verification snapshot

### 2026-04-09 (documentation alignment + host frontend gate)

Executed in the maintainer environment **without** Docker Desktop / API: frontend toolchain only.

| Check | Command | Result | Notes |
| --- | --- | --- | --- |
| Frontend lint | `npm run lint:web` | **Passed** | ESLint clean. |
| Frontend build | `npm run build:web` | **Passed** | `tsc -b && vite build` succeeded. |
| Backend tests | `docker compose run --rm --entrypoint pytest api` | *Not run (this pass)* | Requires Docker; use command before submission. |
| Playwright | `npm run test:web:e2e` | *Not run (this pass)* | Requires API on `127.0.0.1:8000` + seed. |
| Attack scenario validation | `py -3 scripts/validate_attack_scenarios.py` | *Not run (this pass)* | Requires running API (default port 8000). |

### 2026-04-08 (full-stack release-candidate run, seeded Compose API)

| Check | Command | Result | Notes |
| --- | --- | --- | --- |
| Backend tests | `docker compose run --rm --entrypoint pytest api` | Passed | `103 passed`, `1 warning` (Passlib `crypt` deprecation). |
| Frontend lint | `npm run lint:web` | Passed | No ESLint errors. |
| Frontend build | `npm run build:web` | Passed | Vite production build succeeded. |
| Playwright | `npm run test:web:e2e` | Passed | **16 passed**, 0 skipped (API on `127.0.0.1:8000`, DB seeded). |
| Attack scenario validation | `py -3 scripts/validate_attack_scenarios.py` | Passed | All four supported scenarios validated end-to-end against the same API. |

**After 2026-04-08:** the suite gained one Playwright spec (`tests/operator-workflows.spec.ts`, simulated acknowledge failure). **Expected Playwright count is now 17** — re-run e2e to record an updated green snapshot before viva if you need a single dated row for all five checks.

Freeze route-surface smoke checks (authenticated API) returned `200` for:

- `/api/dashboard/summary`
- `/api/alerts`
- `/api/incidents`
- `/api/alerts/{id}`
- `/api/incidents/{id}`
- `/api/assets`
- `/api/responses`
- `/api/policies`
- `/api/reports/daily-summary`
- `/api/reports/alerts/export?format=json`
- `/api/reports/responses/export?format=json`

Auth behavior was confirmed during freeze:

- `/api/auth/login` returned a valid JWT for seeded admin credentials.
- connector status routes require auth and returned `401` when called without token (expected).

Prior blocker remediation (closed before this RC pass):

- **Playwright `/auth/login` socket-hang-up**: resolved by stabilizing backend incident/report serialization for orphan incident records and hardening Playwright session/test assumptions (`session_role` storage and resilient write-workflow branching).
- **`brute_force` daily report mismatch in scenario validator**: resolved by making validator query daily reports using the ingested alert's actual date window and auto-enabling scoped policies before validation.

Documentation alignment (2026-04-08):

- **Backend pytest invocation**: the API container `ENTRYPOINT` runs migrations and starts uvicorn; one-shot tests require `--entrypoint pytest`. README, checklists, and operator docs now use `docker compose run --rm --entrypoint pytest api` consistently.
