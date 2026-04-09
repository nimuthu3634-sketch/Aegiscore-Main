# AegisCore Demo Script

**AegisCore is the final scoped v1 product for single-tenant SME/lab deployment.**

## Demo Goal

Present AegisCore as the **final scoped v1 product** for this project (**single-tenant**, **SME/lab**; **not** an enterprise commercial SOC), with honest boundaries and a real end-to-end workflow for **only** these detections:

- `brute_force`
- `file_integrity_violation`
- `port_scan`
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
   - show totals, high-risk indicators, recent activity panels, and the **v1 threat scope** callout (four detections + analyst review order)
   - say: "This is a live summary of normalized in-scope SOC data—not a generic enterprise dashboard."
3. **Alert -> Incident (`/alerts` then `/alerts/{id}` then `/incidents/{id}`)**
   - open one high-risk alert, show score explanation + raw payload + linked incident
   - open linked incident and show timeline/response history
   - say: "This demonstrates ingestion -> scoring -> incident workflow continuity."
4. **Response + Rules + Report (`/responses`, `/rules`, `/reports`)**
   - show auditable response outcomes
   - show policy table with role-aware controls
   - trigger one export on Reports
   - say: "Automation is policy-driven and auditable, with practical reporting for SMEs."

## 7-10 Minute Demo Path (Full Review)

Use this when examiners want evidence depth.

1. **Open with positioning (20-30s)**
   - say: "AegisCore is a final scoped v1 SME/lab SOC product, not enterprise SaaS."
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
- Why not enterprise: intentionally single-tenant SME/lab design boundary.
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
