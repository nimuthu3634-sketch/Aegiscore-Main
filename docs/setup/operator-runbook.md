# Operator Runbook

## Purpose

This runbook is the concise day-2 operations guide for local/lab AegisCore operation in SME scope.

## Reference: Ubuntu VM lab (live Wazuh + Suricata)

The **intended connected product environment** is an **Ubuntu Server SOC host** (Docker Compose), **Wazuh** for host/log monitoring (manager + agents + FIM on monitored Ubuntu clients), **Suricata** for network monitoring (`eve.json` → **`file_tail`** connector), plus an **attacker/test VM** in VirtualBox. **Live connectors are the normal mode**; manual `POST` ingestion is test/demo-only.

Full topology, env summary, JWT `curl` examples, and **live lab verification** (one Wazuh-style example, one Suricata example): **[ubuntu-vm-lab-live-soc.md](ubuntu-vm-lab-live-soc.md)**.

## 1) First Startup

**Windows (PowerShell):**

```powershell
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
docker compose ps
```

**Ubuntu SOC host (`bash`):**

```bash
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
docker compose ps
```

Expected:

- `postgres`, `api`, `web`, and `nginx` are `healthy`
- `worker` is `healthy` after API/database are healthy

## 2) Verify Health And Readiness

Core health (via NGINX on the SOC host):

```powershell
curl http://localhost/api/health/live
curl http://localhost/api/health
curl http://localhost/api/health/ready
```

**Ubuntu / `bash` (same endpoints; replace host if remote):**

```bash
curl -s "http://localhost/api/health/live"
curl -s "http://localhost/api/health" | jq .
curl -s "http://localhost/api/health/ready" | jq .
```

Connector visibility requires a **JWT** (see [ubuntu-vm-lab-live-soc.md](ubuntu-vm-lab-live-soc.md) for `curl` + `jq` login). Example via NGINX after exporting `TOKEN`:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost/api/integrations/wazuh/connector/status" | jq .
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost/api/integrations/suricata/connector/status" | jq .
```

Operational interpretation:

- `health/live` confirms API process liveness
- `health` confirms API + DB summary
- `health/ready` confirms DB readiness plus **`dependencies.wazuh_connector`** and **`dependencies.suricata_connector`** summaries
- **`GET /integrations/*/connector/status`** (authenticated) shows last success/error, checkpoints, and **metrics** for event flow debugging

## 3) Restart After Failure

Standard recovery:

```powershell
docker compose up -d
docker compose ps
docker compose logs --tail 200 api
docker compose logs --tail 200 postgres
docker compose logs --tail 200 web
```

If API schema drift is suspected:

```powershell
docker compose exec api alembic upgrade head
```

If frontend dependencies drift after host/container changes:

```powershell
docker compose exec web npm ci
```

Continuity note:

- with persistent `postgres_data`, incident history, connector checkpoints, and integration state survive restart

## 4) Connector Troubleshooting

Wazuh connector unhealthy:

1. check `WAZUH_*` env values
2. verify URL reachability and auth mode
3. review API logs for connector poll errors

Suricata connector unhealthy:

1. verify `SURICATA_EVE_FILE_PATH` exists in API runtime context
2. verify `SURICATA_CONNECTOR_MODE=file_tail`
3. review offset/inode checkpoint behavior in connector status

Useful commands:

```powershell
docker compose logs --tail 200 api
curl http://localhost/api/integrations/wazuh/connector/status
curl http://localhost/api/integrations/suricata/connector/status
```

## 5) Backup And Restore (PostgreSQL)

Create backup:

```powershell
docker compose exec -T postgres pg_dump -U ${env:POSTGRES_USER} -d ${env:POSTGRES_DB} > aegiscore-backup.sql
```

Restore backup:

```powershell
Get-Content .\aegiscore-backup.sql | docker compose exec -T postgres psql -U ${env:POSTGRES_USER} -d ${env:POSTGRES_DB}
```

Optional compressed backup:

```powershell
docker compose exec -T postgres pg_dump -U ${env:POSTGRES_USER} -d ${env:POSTGRES_DB} | gzip > aegiscore-backup.sql.gz
```

## 6) Re-Run Validation Scenarios

Backend + frontend checks:

```powershell
docker compose run --rm --entrypoint pytest api
npm run lint:web
npm run build:web
npm run test:web:e2e
```

Threat-scenario replay:

```powershell
py -3 scripts/validate_attack_scenarios.py
```

## 7) Log Retention And Cleanup

Current Compose posture:

- service logs use `json-file` rotation (`max-size=10m`, `max-file=3`)

Practical cleanup:

```powershell
docker compose logs --tail 200 api
docker compose logs --tail 200 web
docker compose logs --tail 200 nginx
```

For space recovery after lab cycles:

```powershell
docker image prune -f
```
