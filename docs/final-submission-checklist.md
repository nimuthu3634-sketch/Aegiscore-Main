# Final Submission Checklist

**Final product:** **AegisCore** is the **submitted end deliverable**—the **centralized SOC platform MVP** (single-tenant web application: console, API, database, optional TensorFlow scoring artifacts) implementing **monitoring**, **alerts**, **incidents**, **explainable AI-assisted risk scoring**, **reporting**, and **controlled automated response**, scoped to **`brute_force`**, **`port_scan`**, **`file_integrity_violation`**, and **`unauthorized_user_creation`**. See **[final-product.md](final-product.md)**.

This checklist is the final handoff gate for that product, with **no overstated claims** of broader coverage or full production completeness beyond the academic release.

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

## 5) Verification record

### 2026-04-09 (host frontend + doc alignment)

- frontend lint: **passed** — `npm run lint:web`
- frontend build: **passed** — `npm run build:web`
- backend pytest / Playwright / scenario script: *run on your machine* (requires Docker + API); not re-recorded in the doc-only pass environment

### 2026-04-08 (full five-step release-candidate run)

- backend tests: passed — **`103 passed`**, `1 warning` — `docker compose run --rm --entrypoint pytest api`
- frontend lint: passed — `npm run lint:web`
- frontend build: passed — `npm run build:web`
- Playwright: passed — **16 passed**, 0 skipped — `npm run test:web:e2e` with Compose API on `127.0.0.1:8000` and `docker compose exec api python -m app.db.seed`
- attack scenario validation: passed (all four scenarios) — `py -3 scripts/validate_attack_scenarios.py`

**Suite note:** the repo now includes **17** Playwright tests. After pulling latest, re-run e2e once so your local snapshot matches the current tree.

Prior freeze-cycle blockers (now closed): Playwright `/auth/login` proxy stability; `brute_force` daily-report alignment in the scenario validator.

## 6) Submission Decision Gate

Mark one before handoff:

- [ ] **Full gate green (recommended for viva):** all five commands in section 1 succeeded on **your** machine **after** pulling the latest commit (including **17** Playwright tests if using current tree).
- [x] **Documentation / product story ready:** scope, limitations, integrations, notifications, and automated response are consistent across `README.md`, `release-readiness.md`, this checklist, `requirement-compliance-matrix.md`, and `demo-script.md` (2026-04-09 alignment pass).
- [ ] **Not ready:** a verification step failed or prerequisites are missing.

**Honest stance:** Materials are **submission- and demo-ready** from a **documentation and frontend build** perspective. **Formal “all automated checks green”** requires you to run the Docker-backed commands in section 1 on hardware where Docker and the API are available. The **2026-04-08** row above is the last recorded full five-step success.

See [release-candidate-note.md](release-candidate-note.md) for the one-line RC stance.
