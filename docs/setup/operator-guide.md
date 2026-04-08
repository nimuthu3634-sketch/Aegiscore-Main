# Operator Guide

## Purpose

This guide is for operators running **AegisCore**, the **final scoped v1 product** for this project (**single-tenant**, **SME/lab**; **not** an enterprise commercial SOC). It covers safe startup, validation (including **simulated-attack** replay), and safety controls—not large-scale enterprise deployment.

For a concise command-first operating sequence, use the [Operator Runbook](operator-runbook.md).

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
  - can read policy state and connector status
  - cannot update response policy state
  - cannot submit manual ingestion events
  - sees policy controls in read-only mode in the frontend

## Local Validation Commands

Backend tests:

```powershell
docker compose run --rm --entrypoint pytest api
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
docker compose logs --tail 200 web
docker compose logs --tail 200 nginx
```

4. Re-apply migrations if needed:

```powershell
docker compose exec api alembic upgrade head
```

5. Re-seed only when user/fixture baseline is intentionally reset:

```powershell
docker compose exec api python -m app.db.seed
```

6. Re-check connector health after restart:

```powershell
curl http://localhost:8000/integrations/wazuh/connector/status
curl http://localhost:8000/integrations/suricata/connector/status
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

- `block_ip`
  - does: validates source IP targets and records containment in the lab ledger (`ledger`) or inserts/verifies an `iptables` drop rule (`iptables`)
  - does not: apply destructive host firewall changes unless explicitly enabled
  - required flags: `AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED=true`, `AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true`; for `iptables`, also `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=true`
- `disable_user`
  - does: validates Linux-safe usernames and records account-disable evidence in the lab ledger (`ledger`) or executes `passwd -l` (`linux_lock`)
  - does not: lock operating-system accounts unless explicitly enabled
  - required flags: `AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED=true`, `AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true`; for `linux_lock`, also `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=true`
- `quarantine_host_flag`
  - does: persists active containment state in `containment_flags`, records incident audit entries, and can write an optional host-tag record
  - does not: isolate endpoints on the network fabric; this is a containment signal for analyst workflow
  - required flags: `AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED=true`, `AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true`; optional `AUTOMATED_RESPONSE_ENABLE_HOST_TAG_WRITE=true`
- `create_manual_review`
  - does: writes incident audit evidence and a ledger event that a manual-review workflow was opened
  - does not: create ticketing-system artifacts in external ITSM/SOAR tools
  - required flags: `AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED=true`, `AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true`
- `notify_admin`
  - does: dispatches through the backend notification subsystem with persisted delivery attempts/results
  - does not: provide paging escalation or enterprise on-call routing
  - required flags: `NOTIFICATIONS_ENABLED=true` plus configured `NOTIFICATIONS_ADMIN_RECIPIENTS`; mode is selected with `NOTIFICATIONS_MODE=log|smtp`

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

Use CSV or JSON exports for local review and audit trails. There is no PDF or scheduled reporting workflow in this scoped v1 product.

## Known Limits

- The worker is still a shell for future replay or background execution use.
- This platform is intentionally single-tenant and should not be treated as a multi-customer SaaS control plane.
