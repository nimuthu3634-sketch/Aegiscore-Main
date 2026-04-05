# Release Readiness

## Intended Readiness Level

AegisCore is currently positioned as a serious SME-focused SOC platform prototype for local lab deployment and demonstration. It is not presented as a finished enterprise production service.

## Local Release Checklist

### Platform Startup

- `docker compose up --build -d` succeeds
- database migrations apply cleanly
- local seed command succeeds
- `/health` returns healthy API and database status

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

- validation uses real backend ingestion endpoints with fixtures instead of live Wazuh or Suricata polling
- Playwright covers core route and scenario visibility, not every write workflow
- the frontend is operational but still benefits from additional route-level code splitting over time
- response adapters beyond safe local or internal actions still depend on operator-supplied scripts
- no scheduled reporting or email-delivery workflow exists

## Future Work

- implement live connector auth and polling or webhook ingestion for Wazuh and Suricata
- extend browser coverage to mutation-heavy analyst workflows
- add background replay handling for failed ingestions
- deepen adapter integrations for safe live response actions
- continue splitting the frontend bundle if the console grows substantially
