# AegisCore Demo Script

## Demo Goal

Show AegisCore as a serious SME-focused SOC platform prototype with a real end-to-end workflow for the four supported detections:

- `brute_force`
- `file_integrity_violation`
- `port_scan`
- `unauthorized_user_creation`

This demo script assumes the local stack is already running and seeded.

## Before The Demo

Run these commands before the presentation:

```powershell
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
npm run test:web:e2e
py -3 scripts/validate_attack_scenarios.py
```

If you want fresh supported-detection events in the UI immediately before the demo, run the validation script again. It creates unique fixture identifiers so the backend treats each run as a new ingestion event.

## Opening Statement

What to say:

"AegisCore is a single-tenant SOC platform prototype for small and medium enterprises. It ingests security events from Wazuh and Suricata, normalizes them into a common schema, assigns risk scores, groups incidents, evaluates safe automated-response policies, and exposes the workflow through a live analyst console."

## Step 1. Login

Screen:

- open `http://localhost`
- show the login page

What to do:

- sign in with `admin / AegisCore123!`

What to say:

"The system uses backend JWT authentication. Even in local development, the normal operator path is an explicit login flow."

## Step 2. Overview Dashboard

Screen:

- Overview Dashboard

What to show:

- total alerts
- high-risk alerts
- open incidents
- active assets
- recent responses
- alert volume and distribution charts
- latest incidents and top affected assets

What to say:

"This overview is intended for quick SOC triage rather than decoration. It summarizes live alert, incident, asset, and response data from the backend."

## Step 3. Alerts List

Screen:

- Alerts page

What to show:

- live filters for severity, detection type, source type, and date range
- dense table layout
- score-based prioritization and linked navigation

What to say:

"Alerts are normalized into a backend-owned schema so the frontend never needs to understand raw Wazuh or Suricata formats directly."

## Step 4. Alert Detail

Screen:

- open one alert detail page

What to show:

- normalized metadata
- raw payload viewer
- score explanation
- linked incident summary
- related response actions
- analyst note area

What to say:

"The alert detail view combines normalized evidence, preserved raw payloads, explainable scoring, and workflow context. This is where the platform bridges from detection into investigation."

## Step 5. Incident Detail

Screen:

- open the linked incident from the alert

What to show:

- incident summary
- linked alerts
- affected assets
- timeline
- response history
- analyst notes

What to say:

"Incidents now support multi-alert ownership, so related evidence can be grouped into one investigation record instead of remaining isolated alerts."

## Step 6. Response History

Screen:

- Responses page

What to show:

- policy name
- action type
- target
- dry-run or live mode
- execution status
- result summary

What to say:

"Automated response in this prototype is deliberately conservative and auditable. Every policy-driven action is persisted, visible, and reviewable."

## Step 7. Rules Or Policies

Screen:

- Rules / Policies page

What to show:

- detection type
- action type
- score threshold
- mode
- enabled state

What to say:

"Policies are backend-owned and detection-specific. This keeps automation explainable and aligned to the project’s limited threat scope."

## Step 8. Reports

Screen:

- Reports page

What to show:

- daily summary
- weekly summary
- charts and top assets
- export buttons for alerts, incidents, and responses

What to say:

"Reports are practical rather than enterprise-heavy. The system supports real backend summaries and safe CSV or JSON exports for SME review workflows."

## Step 9. Short Scenario Paths

### Brute Force

What to show:

- alert with `brute_force`
- high or critical score
- linked incident
- related response action

What to say:

"This scenario shows failed-login behavior being ingested, normalized, prioritized, linked into incident workflow, and exposed in reporting."

### File Integrity Violation

What to show:

- alert with `file_integrity_violation`
- normalized sensitive file path
- score explanation drivers
- response or manual-review context

What to say:

"This path shows that sensitive file changes are preserved in normalized form and influence the alert’s prioritization."

### Port Scan

What to show:

- alert with `port_scan`
- Suricata source type
- linked incident and response history

What to say:

"Port scan events come through the Suricata ingestion path and still enter the same normalized scoring and incident workflow as host-based events."

### Unauthorized User Creation

What to show:

- alert with `unauthorized_user_creation`
- normalized username
- incident and response visibility

What to say:

"This path demonstrates host-level administrative account creation being normalized and escalated through the same analyst workflow."

## Step 10. Closing Statement

What to say:

"Within its defined scope, AegisCore now demonstrates a complete backend-owned SOC workflow: ingestion, normalization, scoring, incident handling, auditable response automation, reporting, and analyst-facing UI coverage."

## Demo-Safe Fallback Notes

- If live connectors are unavailable, use the fixture-backed validation path. This is still a real backend flow, not a frontend mock.
- Run `py -3 scripts/validate_attack_scenarios.py` shortly before the demo to ensure fresh events exist for all four supported detections.
- If browser state is stale, sign out by clearing local storage or reopen the login page and authenticate again.
- If asked about unsupported detections, state clearly that the prototype scope is intentionally limited to the four supported scenarios.

## Manual Confirmation Checklist Before Presentation

- the local stack is up
- seeded credentials work
- the overview dashboard loads
- at least one alert and incident for each supported detection is present
- the Reports page exports successfully
- the Responses page shows policy-driven execution records
