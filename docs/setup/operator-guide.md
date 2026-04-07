# Operator Guide

## Purpose

This guide is for the person running AegisCore locally in an SME or lab environment. It focuses on safe startup, validation, and operator-facing safety controls rather than enterprise deployment patterns.

## Local Startup

```powershell
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
```

Primary local URLs:

- `http://localhost`
- `http://localhost/api/health`
- `http://localhost/api/health/live`
- `http://localhost/api/health/ready`
- `http://localhost:8000/health`
- `http://localhost:8000/health/ready`

## Safe Default Posture

- Keep `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=false` during local work.
- Keep `VITE_ENABLE_DEV_AUTH_BOOTSTRAP=false` unless you intentionally need automatic browser auth for a temporary local workflow.
- For normal VM/lab operation, enable live connectors (`WAZUH_CONNECTOR_ENABLED=true`, `SURICATA_CONNECTOR_ENABLED=true`) and treat manual fixture posting as test/demo-only.
- Rotate seeded demo passwords through `DEV_SEED_ADMIN_PASSWORD` and `DEV_SEED_ANALYST_PASSWORD` when sharing lab environments.

## Role Responsibilities

- `admin`:
  - can update response policy enabled state (`PATCH /policies/{id}`)
  - can submit manual ingestion events (`POST /integrations/wazuh/events`, `POST /integrations/suricata/events`)
  - can perform all analyst investigation and reporting actions
- `analyst`:
  - can investigate alerts/incidents, add notes, transition incidents, review responses, and use reports
  - cannot update response policy state
  - cannot submit manual ingestion events

## Local Validation Commands

Backend tests:

```powershell
docker compose run --rm --no-deps api pytest
```

Frontend validation:

```powershell
npm run lint:web
npm run build:web
npm run test:web:e2e
```

Scenario validation:

```powershell
py -3 scripts/validate_attack_scenarios.py
```

## Operational Health Checks

- `GET /health`: API and DB high-level health.
- `GET /health/live`: liveness endpoint that confirms the API process is serving.
- `GET /health/ready`: readiness endpoint with DB status and connector dependency states.
- Connector states can also be inspected at:
  - `GET /integrations/wazuh/connector/status`
  - `GET /integrations/suricata/connector/status`

## Restart And Recovery Flow

If the stack restarts or a service crashes:

1. Restart services:

```powershell
docker compose up -d
```

2. Confirm API readiness:

```powershell
curl http://localhost:8000/health/ready
```

3. If API is not ready, inspect logs:

```powershell
docker compose logs --tail 200 api
docker compose logs --tail 200 postgres
```

4. Re-apply migrations if needed:

```powershell
docker compose exec api alembic upgrade head
```

5. Re-seed only when user/fixture baseline is intentionally reset:

```powershell
docker compose exec api python -m app.db.seed
```

Continuity note: connector checkpoints and integration state are persisted in PostgreSQL; with a persistent `postgres_data` volume, ingestion resumes from stored state after restart.

## PostgreSQL Backup And Restore (Local/Lab)

Create backup:

```powershell
docker compose exec -T postgres pg_dump -U ${env:POSTGRES_USER} -d ${env:POSTGRES_DB} > aegiscore-backup.sql
```

Restore backup:

```powershell
Get-Content .\aegiscore-backup.sql | docker compose exec -T postgres psql -U ${env:POSTGRES_USER} -d ${env:POSTGRES_DB}
```

For JSON/CSV workflow continuity exports, use report export endpoints from the UI or `/reports/*/export`.

## Log Retention Notes (Local)

- Docker Compose services are configured with `json-file` log rotation (`max-size=10m`, `max-file=3`) to prevent unbounded local log growth.
- Use `docker compose logs --tail 200 <service>` for quick diagnostics.
- For deeper troubleshooting, capture a timestamped log snapshot before restarting services.

## Ingestion Operations

Primary operational ingestion path:

- Wazuh live connector polling (`WAZUH_CONNECTOR_ENABLED=true`)
- Suricata live connector file-tail ingestion (`SURICATA_CONNECTOR_ENABLED=true`)

Manual ingestion routes (test/demo tool):

- `POST /integrations/wazuh/events`
- `POST /integrations/suricata/events`

Connector verification routes:

- `GET /integrations/wazuh/connector/status`
- `GET /integrations/suricata/connector/status`

Supported detections only:

- `brute_force`
- `file_integrity_violation`
- `port_scan`
- `unauthorized_user_creation`

Rejected or malformed events are recorded in `ingestion_failures` for review. Duplicate source events are de-duplicated safely by `source + external_id`.

## Automated Response Operations

Supported policy actions:

- `block_ip`
- `disable_user`
- `quarantine_host_flag`
- `create_manual_review`
- `notify_admin`

Operator expectations:

- `dry-run` should be the default mode while validating policies.
- `live` mode should be used only when lab adapter gates are explicitly enabled.
- every policy evaluation and response outcome is written into response history and audit logs

Built-in adapter behavior in lab mode:

- `block_ip`: supports `ledger` (safe default) and `iptables` (guarded destructive mode)
- `disable_user`: supports `ledger` (safe default) and `linux_lock` via `passwd -l` (guarded destructive mode)
- `quarantine_host_flag`: persists containment state in backend DB and can optionally emit a safe host-tag record
- `create_manual_review`: records manual-review workflow evidence and incident audit entries
- `notify_admin`: routes through the backend notification subsystem (`log` or `smtp`)

Required live gates for lab execution:

- `AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED=true`
- `AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true`
- `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=true` only when intentionally enabling `iptables` or `linux_lock`

## Reports And Exports

The backend supports:

- daily summary
- weekly summary
- alert export
- incident export
- response export

Use CSV or JSON exports for local review and audit trails. There is no PDF or scheduled reporting workflow in this prototype.

## Known Limits

- The worker is still a shell for future replay or background execution use.
- This platform is intentionally single-tenant and should not be treated as a multi-customer SaaS control plane.
