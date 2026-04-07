# Release Readiness

## Intended Readiness Level

AegisCore is positioned as a final scoped v1 single-tenant SOC product for SME/lab deployment. It is not presented as an enterprise production cloud service.

## Product Positioning

- **Fully implemented for scoped v1**: dashboard, four-detection ingestion/normalization, risk scoring, incident/response workflows, basic automated response, and reporting/export.
- **Partially implemented / limited mode (live connectors)**:
  - Wazuh live polling is implemented with auth, retries, checkpointing, dedupe, and status visibility; upstream compatibility is currently limited to common envelope variants.
  - Suricata live ingestion is implemented in `file_tail` mode for `eve.json`; authenticated forwarding mode is not implemented yet.
- **Fixture-backed validation baseline**: release validation is deterministic and primarily fixture-backed, with optional live connector checks in VM/lab environments.

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

- deterministic validation still relies heavily on fixtures despite live connector support
- Playwright covers core route visibility plus major write workflows, but not every negative-path or role-restriction branch
- the frontend is operational but still benefits from additional route-level code splitting over time
- no scheduled reporting or email-delivery workflow exists

## Future Work

- add Suricata authenticated forwarding mode beyond `file_tail`
- extend browser coverage to role-restriction and remaining edge-case mutation paths
- add background replay handling for failed ingestions
- deepen adapter integrations for safe live response actions
- continue splitting the frontend bundle if the console grows substantially

## Requirement Traceability

- Proposal/requirement alignment evidence is maintained in [requirement-compliance-matrix.md](requirement-compliance-matrix.md).
- Use that matrix during review to separate implemented behavior from intentional local/lab constraints.
