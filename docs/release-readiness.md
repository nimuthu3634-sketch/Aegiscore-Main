# Release Readiness

## Intended Readiness Level

AegisCore is currently positioned as a serious SME-focused SOC platform prototype for local lab deployment and demonstration. It is not presented as a finished enterprise production service.

## Local Release Checklist

### Platform Startup

- `docker compose up --build -d` succeeds
- database migrations apply cleanly
- local seed command succeeds
- `/health` returns healthy API and database status
- `/health/live` returns API liveness
- `/health/ready` reports `ready` with database `up`
- `docker compose ps` shows healthy status for `postgres`, `api`, `web`, and `nginx`

### Security And Access

- `JWT_SECRET_KEY` is set to a non-placeholder value outside throwaway local work
- `VITE_ENABLE_DEV_AUTH_BOOTSTRAP=false` unless temporary local testing explicitly needs it
- destructive automated response remains disabled unless adapters and controls are understood

### Data Flow

- supported Wazuh or Suricata fixtures ingest successfully
- normalized alerts appear in the list and detail UI
- scoring metadata is visible in alert and incident detail
- policy-driven responses appear in response history
- reports include the validated activity
- connector status endpoints remain reachable after API restart

### Recovery And Continuity

- restarting `api` does not require manual data recovery when `postgres_data` volume is intact
- readiness transitions back to `ready` after restart
- migration command remains idempotent (`alembic upgrade head`)
- local backup command for PostgreSQL has been run at least once and restore steps are documented
- docker service logs are bounded locally via `json-file` rotation settings

### Validation Commands

Backend:

```powershell
docker compose run --rm --no-deps api pytest
```

Frontend:

```powershell
npm run lint:web
npm run build:web
```

Browser:

```powershell
npm run test:web:e2e
```

Scenario validation:

```powershell
py -3 scripts/validate_attack_scenarios.py
```

## Known Limitations

- validation still relies heavily on fixtures despite live connector support
- Playwright covers core route and scenario visibility, not every write workflow
- the frontend is operational but still benefits from additional route-level code splitting over time
- no scheduled reporting or email-delivery workflow exists

## Future Work

- implement live connector auth and polling or webhook ingestion for Wazuh and Suricata
- extend browser coverage to mutation-heavy analyst workflows
- add background replay handling for failed ingestions
- deepen adapter integrations for safe live response actions
- continue splitting the frontend bundle if the console grows substantially
