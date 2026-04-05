# AegisCore

AegisCore is a production-minded, single-tenant AI-integrated SOC platform for small and medium enterprises. This repository is structured as a clean monorepo for the core web UI, API, worker runtime, AI logic, infrastructure, scripts, and documentation.

## Monorepo Layout

- `apps/web`: React + TypeScript + Tailwind CSS + Recharts SOC dashboard shell
- `apps/api`: FastAPI + SQLAlchemy + Alembic backend with PostgreSQL wiring
- `apps/worker`: background worker runtime for future automated response workflows
- `ai`: AI and risk-scoring modules
- `infra/nginx`: NGINX configuration for frontend and API routing
- `infra/docker`: Dockerfiles used by local development services
- `scripts`: helper scripts for local workflow and validation
- `docs`: architecture and environment documentation

## Local Startup

1. Review the env examples and override values only when needed.
2. Start the local stack:

```powershell
docker compose up --build
```

3. Open the platform:

- Frontend through NGINX: `http://localhost`
- API health through NGINX: `http://localhost/api/health`
- API direct: `http://localhost:8000/health`
- Frontend direct: `http://localhost:5173`

## Services

- `postgres`: PostgreSQL 16 for local persistence
- `api`: FastAPI service with JWT auth, modular domain layers, and `/health`
- `worker`: background worker shell for future policy execution
- `web`: Vite-powered React frontend shell
- `nginx`: reverse proxy routing `/` to the frontend and `/api` to the backend

## Seed Development Data

Run the local seed command after migrations are available:

```powershell
docker compose exec api python -m app.db.seed
```

Default seeded development credentials:

- Admin: `admin` / `AegisCore123!`
- Analyst: `analyst` / `AegisCore123!`

Sample auth flow:

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/auth/login -ContentType "application/json" -Body '{"username":"admin","password":"AegisCore123!"}'
$token = $login.access_token
Invoke-RestMethod -Headers @{ Authorization = "Bearer $token" } -Uri http://localhost:8000/dashboard/summary
$alerts = Invoke-RestMethod -Headers @{ Authorization = "Bearer $token" } -Uri http://localhost:8000/alerts
Invoke-RestMethod -Headers @{ Authorization = "Bearer $token" } -Uri ("http://localhost:8000/alerts/" + $alerts.items[0].id)
$incidents = Invoke-RestMethod -Headers @{ Authorization = "Bearer $token" } -Uri http://localhost:8000/incidents
Invoke-RestMethod -Headers @{ Authorization = "Bearer $token" } -Uri ("http://localhost:8000/incidents/" + $incidents.items[0].id)
```

## Environment Files

- Root compose defaults: `.env.example`
- Web envs: `apps/web/.env.example`
- API envs: `apps/api/.env.example`
- Worker envs: `apps/worker/.env.example`
- AI envs: `ai/.env.example`

## Validation Commands

```powershell
docker compose config
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
Invoke-WebRequest http://localhost:8000/health
Invoke-WebRequest http://localhost:8000/auth/me -Headers @{ Authorization = "Bearer <token>" }
Invoke-WebRequest http://localhost:8000/alerts/<alert-id> -Headers @{ Authorization = "Bearer <token>" }
Invoke-WebRequest http://localhost:8000/incidents/<incident-id> -Headers @{ Authorization = "Bearer <token>" }
Invoke-WebRequest http://localhost/
```

## Workflow API Surface

The current backend now supports persisted analyst workflow actions on live records:

- `POST /alerts/{id}/acknowledge`
- `POST /alerts/{id}/close`
- `POST /alerts/{id}/link-incident`
- `POST /alerts/{id}/notes`
- `POST /incidents/{id}/transition`
- `POST /incidents/{id}/notes`

These operations create audit-log entries, update detail timelines, and persist analyst notes in first-class storage.

`POST /alerts/{id}/link-incident` now accepts a typed JSON body so an alert can be linked to an existing incident or used to create a new one:

```json
{
  "incident_id": "optional-existing-incident-uuid",
  "create_new": false,
  "title": "optional new incident title",
  "summary": "optional new incident summary"
}
```

Use either `incident_id` for an existing incident or `create_new: true` for a new incident, but not both.

## Automated Response

AegisCore now supports safe, policy-driven automated response after alert scoring.

- Supported detection scope: `brute_force`, `file_integrity_violation`, `port_scan`, `unauthorized_user_creation`
- Supported action types: `block_ip`, `disable_user`, `quarantine_host_flag`, `create_manual_review`, `notify_admin`
- Modes: `dry-run` and `live`
- Safety default: destructive live actions stay blocked unless `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=true`

Current policy-management and response endpoints:

- `GET /policies`
- `PATCH /policies/{id}`
- `GET /responses`

Automated responses are policy-evaluated after scoring and incident rollup updates. Every policy match, execution attempt, final result, and linked workflow change writes audit history.

Local automated-response environment variables:

- `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=false`
- `AUTOMATED_RESPONSE_MAX_RETRIES=1`
- `RESPONSE_ADAPTER_BLOCK_IP_SCRIPT=`
- `RESPONSE_ADAPTER_DISABLE_USER_SCRIPT=`
- `RESPONSE_ADAPTER_QUARANTINE_HOST_FLAG_SCRIPT=`
- `RESPONSE_ADAPTER_CREATE_MANUAL_REVIEW_SCRIPT=`
- `RESPONSE_ADAPTER_NOTIFY_ADMIN_SCRIPT=`

Manual dry-run validation example:

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/auth/login -ContentType "application/json" -Body '{"username":"admin","password":"AegisCore123!"}'
$token = $login.access_token
Invoke-RestMethod -Headers @{ Authorization = "Bearer $token" } -Uri http://localhost:8000/policies
Invoke-RestMethod -Headers @{ Authorization = "Bearer $token" } -Uri http://localhost:8000/responses
```

## Source Ingestion

AegisCore now includes hardened backend-owned ingestion entrypoints for Wazuh-style and Suricata-style events. These entrypoints normalize source payloads into the existing alert, scoring, incident, and automated-response flow without exposing source-specific schema to the frontend.

- `POST /integrations/wazuh/events`
- `POST /integrations/suricata/events`

Supported detection scope remains limited to:

- `brute_force`
- `file_integrity_violation`
- `port_scan`
- `unauthorized_user_creation`

Ingestion behavior:

- successful events create `raw_alerts` and `normalized_alerts`
- duplicate source events are de-duplicated by `source + external_id`
- malformed or unsupported payloads are recorded in `ingestion_failures`
- partial payloads can still ingest with warnings when the supported detection type is clear
- scoring and automated response policies continue to run through the normal backend flow

Useful local ingestion environment variables:

- `INGESTION_ALLOW_ASSET_AUTOCREATE=true`
- `INGESTION_DEFAULT_ASSET_CRITICALITY=medium`

Fixture-based local validation examples:

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/auth/login -ContentType "application/json" -Body '{"username":"admin","password":"AegisCore123!"}'
$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }

$wazuhBody = Get-Content .\apps\api\tests\fixtures\ingestion\wazuh_brute_force.json -Raw
$ingestedAlert = Invoke-RestMethod -Method Post -Uri http://localhost:8000/integrations/wazuh/events -Headers $headers -ContentType "application/json" -Body $wazuhBody
Invoke-RestMethod -Headers $headers -Uri ("http://localhost:8000/alerts/" + $ingestedAlert.alert.id)
Invoke-RestMethod -Headers $headers -Uri "http://localhost:8000/responses?mode=dry-run"

$suricataBody = Get-Content .\apps\api\tests\fixtures\ingestion\suricata_port_scan.json -Raw
Invoke-RestMethod -Method Post -Uri http://localhost:8000/integrations/suricata/events -Headers $headers -ContentType "application/json" -Body $suricataBody
Invoke-RestMethod -Headers $headers -Uri "http://localhost:8000/dashboard/summary"
```

## Risk Scoring

AegisCore now includes a persisted risk scoring layer for alert prioritization.

- Deterministic runtime baseline: `apps/api/app/services/scoring/baseline.py`
- Optional trainable scikit-learn model: `ai/training/train_risk_model.py`
- Scoring reference: `docs/scoring.md`

Train the local model artifact with:

```powershell
docker compose run --rm --no-deps api python /srv/ai/training/train_risk_model.py
```

## Notes

- The backend owns all external security integrations; the frontend talks only to backend APIs.
- The backend foundation now includes roles, users, assets, raw alerts, normalized alerts, risk scores, incidents, response actions, analyst notes, and audit logs.
- The ingestion layer now includes Wazuh and Suricata normalization services plus failure tracking for malformed or unsupported events.
- Incidents now own many normalized alerts, while each alert can belong to at most one incident and still exposes a clean linked-incident summary for the frontend.
- Frontend work follows the AegisCore dark SOC theme and is prepared for Figma-first design iteration in later milestones.
