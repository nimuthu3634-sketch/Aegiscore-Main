# AegisCore Demo Script

**Final product:** **AegisCore** is the **submitted centralized SOC platform MVP** (single-tenant web app)—**monitoring**, **alerts**, **incidents**, **explainable AI-assisted scoring** (baseline + optional **TensorFlow**), **reporting**, **controlled automated response**—scoped to four detections. See **[final-product.md](final-product.md)**.

## Demo Goal

Present **AegisCore** as that **final product**: a **transparent academic release** with a real end-to-end workflow for **only** these **validated** detections:

- `brute_force`
- `port_scan`
- `file_integrity_violation`
- `unauthorized_user_creation`

## Pre-Demo Setup

Run before presentation:

```powershell
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
npm run test:web:e2e
py -3 scripts/validate_attack_scenarios.py
```

### Optional: TensorFlow scoring + ML brute-force story

By default **`SCORING_STRATEGY=baseline`** (see `docker-compose.yml`). That is **intentional**: the stack runs without depending on Keras artifacts.

To narrate **detection → AI prioritization (Low/Medium/High only) → brute-force-only ML auto-block** in line with **[ai-alert-prioritization.md](ai-alert-prioritization.md)**:

1. Ensure **`ai/models/aegiscore-risk-priority-model.keras`** and **`aegiscore-risk-priority-model.metadata.json`** exist (train with `ai/training/train_risk_model.py` if needed).
2. Set **`SCORING_STRATEGY=model`** for the `api` service (host `.env`, export, or Compose override) and restart **`docker compose up -d api`**.
3. Keep **`AUTOMATED_RESPONSE_ML_BRUTE_FORCE_ENABLED=true`** (default) if you want the built-in rule **evaluated**; it still fires **only** for **`brute_force`** alerts scored with **`tensorflow_model`**, **High** tier, **`failed_logins_5m` ≥ 10**, and **source IP** present.

Say explicitly: **Wazuh/Suricata detect**; **ML only ranks**; **Critical** can appear from **baseline** thresholds, **not** from the TensorFlow softmax.

If you need fresh events just before demo, rerun:

```powershell
py -3 scripts/validate_attack_scenarios.py
```

## Route Map Used In Demo

All steps below use real frontend routes in `apps/web/src/App.tsx`:

- login: `/login`
- dashboard: `/overview`
- alerts: `/alerts`
- alert detail: `/alerts/{alertId}`
- incidents: `/incidents`
- incident detail: `/incidents/{incidentId}`
- assets: `/assets`
- responses: `/responses`
- rules: `/rules`
- reports: `/reports`

## 3-Minute Demo Path (Fast Track)

Use this for tight viva time windows.

1. **Login (`/login`)**
   - sign in as `admin / AegisCore123!`
   - say: "Authentication is real JWT-based access, not a mocked bypass."
2. **Dashboard (`/overview`)**
   - show totals, high-risk indicators, recent activity panels, and the **academic MVP threat scope** callout (four validated categories + analyst review order)
   - say: "This is a live summary of normalized SOC data for the **academic MVP**—**MVP-focused** triage across the **four validated threat categories**."
3. **Alert -> Incident (`/alerts` then `/alerts/{id}` then `/incidents/{id}`)**
   - open one high-risk alert, show score explanation + raw payload + linked incident
   - open linked incident and show timeline/response history
   - say: "This demonstrates ingestion -> scoring -> incident workflow continuity."
4. **Response + Rules + Report (`/responses`, `/rules`, `/reports`)**
   - show auditable response outcomes
   - show policy table with role-aware controls
   - trigger one export on Reports
   - say: "Automation is policy-driven and auditable, with **operator-grade** exports suitable for incident review and governance evidence."

## 7-10 Minute Demo Path (Full Review)

Use this when examiners want evidence depth.

1. **Open with positioning (20-30s)**
   - say: "AegisCore is a **commercial-style SOC platform MVP** for this university project: **single-tenant**, **enterprise-inspired workflow**, **four validated detections** in the **current academic release**—**transparent** scope, not an unlimited production catalogue."
2. **Login and role model (`/login`)**
   - sign in as admin
   - note admin/analyst split and backend enforcement
3. **Dashboard (`/overview`)**
   - show alert pressure, incident count, asset and response visibility
4. **Alerts (`/alerts`)**
   - demonstrate filters (severity/detection/source/date)
   - open one supported detection item
5. **Alert detail (`/alerts/{id}`)**
   - show normalized fields, raw payload, score explanation, related responses
   - mention duplicate protection and normalized backend contract
6. **Incident detail (`/incidents/{id}`)**
   - show linked alerts, timeline, notes, response history, notification evidence if present
7. **Responses (`/responses`)**
   - explain dry-run vs live behavior and safety gates
   - emphasize auditable result summaries
8. **Rules (`/rules`)**
   - show detection-specific policy rows
   - mention analyst view is read-only, admin can mutate
9. **Reports (`/reports`)**
   - show daily/weekly cards and export actions
10. **Close with scope statement (30s)**
   - four detections only
   - live connectors are implemented with documented limits
   - deterministic validation remains fixture-backed by design

## Fallback If Live Connectors Are Unavailable

If Wazuh/Suricata lab connectivity is down, keep the demo valid with fixture-backed validation:

1. seed deterministic scenarios:
   - `py -3 scripts/validate_attack_scenarios.py`
2. confirm API/process health:
   - `http://localhost/api/health`
   - `http://localhost/api/health/live`
   - `http://localhost/api/health/ready`
3. confirm connector status visibility still works:
   - `http://localhost/api/integrations/wazuh/connector/status`
   - `http://localhost/api/integrations/suricata/connector/status`
4. state clearly:
   - "Live connector path exists, but this demo run uses fixture-backed deterministic validation."

This remains a real backend flow (ingestion, normalization, scoring, incidenting, response, reporting), not a frontend-only mock.

## Viva-Defense Notes During Demo

- Why valid final product: complete scoped workflow is implemented and validated end-to-end.
- MVP design choice: **single-tenant** architecture and **bounded detection catalog** keep the submission **defensible, testable, and panel-ready** while preserving a **scale-out direction**.
- Why four detections: explicit requirement boundary to keep implementation defensible and testable.
- Where Q&A is documented: [viva-qa.md](viva-qa.md).

## Manual Checklist Before Presentation

- local stack is up and healthy
- seeded credentials work
- `/overview` loads correctly
- at least one alert/incident per supported detection is available
- `/responses` shows policy execution records
- `/reports` export triggers successfully
- demo fallback command (`py -3 scripts/validate_attack_scenarios.py`) is ready
