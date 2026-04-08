# Final Submission Checklist

This checklist is the final handoff gate for AegisCore as the **final scoped v1 product** for this project: **single-tenant**, **SME/lab**, **not an enterprise commercial SOC platform**, with threat scope limited to the four supported detections only.

## 1) Pre-Submission Checks

Run and record:

```powershell
docker compose run --rm --entrypoint pytest api
npm run lint:web
npm run build:web
docker compose up -d postgres api
docker compose exec api python -m app.db.seed
npm run test:web:e2e
py -3 scripts/validate_attack_scenarios.py
```

Expected outcome:

- backend tests pass
- frontend lint/build pass
- Playwright run is green with the API reachable at `127.0.0.1:8000` (or any failure is documented as a blocker)
- scenario validation passes for all four supported detections against the same API

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

- threat detection is limited to **`brute_force`**, **`file_integrity_violation`**, **`port_scan`**, and **`unauthorized_user_creation`** only; ransomware, phishing, APT, zero-day, and large-scale enterprise SOC claims are out of scope.
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
- `docs/release-candidate-note.md`
- `docs/setup/operator-guide.md`
- `docs/setup/analyst-guide.md`
- `docs/setup/operator-runbook.md`

## 5) Freeze Result Record (2026-04-08, Release-Candidate Verification)

- backend tests: passed — **`103 passed`**, `1 warning` — `docker compose run --rm --entrypoint pytest api`
- frontend lint: passed — `npm run lint:web`
- frontend build: passed — `npm run build:web`
- Playwright: passed — **16 passed**, 0 skipped — `npm run test:web:e2e` with Compose API on `127.0.0.1:8000` and `docker compose exec api python -m app.db.seed`
- attack scenario validation: passed (all four scenarios) — `py -3 scripts/validate_attack_scenarios.py`

Prior freeze-cycle blockers (now closed): Playwright `/auth/login` proxy stability; `brute_force` daily-report alignment in the scenario validator.

## 6) Submission Decision Gate

Mark one before handoff:

- [x] **Release-candidate / submission-ready**: the 2026-04-08 verification sequence completed successfully in the documented environment; remaining limits are documented as scope constraints, not open blockers.
- [ ] **Not ready**: a verification step failed or the environment does not match the documented prerequisites.

See [release-candidate-note.md](release-candidate-note.md) for the one-line RC stance.
