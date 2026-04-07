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
- `http://localhost:8000/health`

## Safe Default Posture

- Keep `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=false` during local work.
- Keep `VITE_ENABLE_DEV_AUTH_BOOTSTRAP=false` unless you intentionally need automatic browser auth for a temporary local workflow.
- Use fixture-backed ingestion first before pointing AegisCore at any real security infrastructure.

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

## Ingestion Operations

Supported ingestion routes:

- `POST /integrations/wazuh/events`
- `POST /integrations/suricata/events`

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

- There is no live Wazuh or Suricata polling loop yet.
- The worker is still a shell for future replay or background execution use.
- This platform is intentionally single-tenant and should not be treated as a multi-customer SaaS control plane.
