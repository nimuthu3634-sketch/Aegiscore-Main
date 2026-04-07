# Final Submission Checklist

This checklist is the final handoff gate for AegisCore scoped v1 submission.

## 1) Pre-Submission Checks

Run and record:

```powershell
docker compose run --rm --no-deps api pytest
npm run lint:web
npm run build:web
npm run test:web:e2e
py -3 scripts/validate_attack_scenarios.py
```

Expected outcome:

- backend tests pass
- frontend lint/build pass
- Playwright run is green (or any failure is documented as blocker)
- scenario validation passes for all four supported detections

## 2) Demo-Day Checks

Startup:

```powershell
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
```

Health and readiness:

- `http://localhost/api/health`
- `http://localhost/api/health/live`
- `http://localhost/api/health/ready`

Login and route flow:

- `/login`
- `/overview`
- `/alerts` and `/alerts/{alertId}`
- `/incidents` and `/incidents/{incidentId}`
- `/assets`
- `/responses`
- `/rules`
- `/reports`

Fallback:

- if live connectors are unavailable, run `py -3 scripts/validate_attack_scenarios.py` and continue with fixture-backed deterministic flow.

## 3) Known Limitations (Must Be Stated Honestly)

- Suricata live ingestion is limited to `file_tail` (`eve.json`) mode.
- Wazuh live compatibility is tuned for common lab envelope variants.
- deterministic acceptance validation is fixture-backed by default.
- destructive live automated-response actions are safety-gated by explicit flags.
- role model remains intentionally minimal (`admin`, `analyst`).

## 4) Must-Have Files And Docs

- `README.md`
- `docs/project-status-summary.md`
- `docs/demo-script.md`
- `docs/viva-qa.md`
- `docs/requirement-compliance-matrix.md`
- `docs/release-readiness.md`
- `docs/setup/operator-guide.md`
- `docs/setup/analyst-guide.md`
- `docs/setup/operator-runbook.md`

## 5) Freeze Result Record (2026-04-07, Post-Remediation Re-Run)

- backend tests: passed (`98 passed`, `1 warning`) via `docker compose run --rm --no-deps --entrypoint pytest api`
- frontend lint: passed
- frontend build: passed
- Playwright: passed (`13 passed`)
- attack scenario validation: passed (all four scenarios)

Blockers remediated in this freeze cycle:

- Playwright startup/login instability (`/auth/login` proxy socket-hang-up)
- scenario-validation daily-report mismatch for `brute_force`

## 6) Submission Decision Gate

Mark one before handoff:

- [x] **Submission-ready**: all verification checks pass, or only non-blocker lab constraints remain and are documented.
- [ ] **Conditionally ready pending blocker re-check**: at least one blocker remains and must be revalidated before final submission packaging.
