# Wazuh Live Integration (VM Lab)

This guide enables continuous live Wazuh ingestion in AegisCore while preserving the existing backend normalization, scoring, incident creation, and response automation flow.

For the **Ubuntu Server + VirtualBox lab topology** (SOC host, Wazuh manager, monitored agents with FIM, attacker VM), start with **[ubuntu-vm-lab-live-soc.md](ubuntu-vm-lab-live-soc.md)**—then use this page for Wazuh-specific variables and behavior.

## Readiness Level

- **Implemented**: live Wazuh polling connector with auth modes (`basic`, `token`, `bearer`), retries, checkpointing, duplicate protection, and connector status visibility.
- **Limited mode**: compatibility currently targets common Wazuh response envelopes (`list`, `data.affected_items`, `data.items`) and may require tuning for other manager/API variants.
- **Operational default**: live Wazuh polling is the normal VM/lab ingestion path when `WAZUH_CONNECTOR_ENABLED=true`; fixture posting is reserved for explicit test/demo fallback.

## Scope Guardrails

- Supported detections match the academic MVP four-category scope:
  - `brute_force`
  - `port_scan`
  - `file_integrity_violation`
  - `unauthorized_user_creation`
- Wazuh events outside that scope are rejected and logged in `ingestion_failures`.
- Frontend contracts do not change; Wazuh complexity stays inside backend integration services.

## 1) Prepare VM Lab Connectivity

- Ensure the API container or API runtime can reach the Wazuh manager API URL.
- Confirm TLS posture for your lab:
  - use trusted certs when possible
  - if internal CA is used, provide `WAZUH_CA_FILE`
- Validate auth credentials/token from the same network context as the API service.

## 2) Configure Environment Variables

Set these in your API env file or compose overrides:

- `WAZUH_BASE_URL` (for example `https://<wazuh-manager>:55000`)
- `WAZUH_CONNECTOR_ENABLED=true`
- `WAZUH_ALERTS_PATH` (default `/alerts`)
- `WAZUH_POLL_INTERVAL_SECONDS` (default `30`)
- `WAZUH_TIMEOUT_SECONDS` (default `10`)
- `WAZUH_RETRY_ATTEMPTS` (default `2`)
- `WAZUH_RETRY_BACKOFF_SECONDS` (default `1`)
- `WAZUH_VERIFY_TLS` (`true` recommended)
- `WAZUH_CA_FILE` (optional path for custom CA)
- `WAZUH_PAGE_SIZE` (default `200`)
- `WAZUH_MAX_PAGES_PER_CYCLE` (default `5`)
- `WAZUH_OFFSET_PARAM` (default `offset`)
- `WAZUH_SINCE_PARAM` (default `since`)
- `WAZUH_TIMESTAMP_FIELD` (default `timestamp`)

Auth options:

- `WAZUH_AUTH_MODE=basic` with `WAZUH_USERNAME` + `WAZUH_PASSWORD`
- `WAZUH_AUTH_MODE=token` with `WAZUH_USERNAME` + `WAZUH_PASSWORD` and token bootstrap endpoint `WAZUH_AUTH_ENDPOINT`
- `WAZUH_AUTH_MODE=bearer` with `WAZUH_BEARER_TOKEN`

## 3) Run Migrations and Start Stack

```powershell
docker compose up --build -d
docker compose exec api alembic upgrade head
```

## 4) Verify Connector Health and Sync

Use an authenticated JWT (`Authorization: Bearer …`) and query:

```http
GET /integrations/wazuh/connector/status
```

**Direct API (Ubuntu SOC host, port 8000 published):**

```bash
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_ADMIN_PASSWORD"}' | jq -r .access_token)

curl -s -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/integrations/wazuh/connector/status" | jq .
```

**Through NGINX** (default Compose): use `http://localhost/api/auth/login` and `http://localhost/api/integrations/wazuh/connector/status` with the same `Authorization` header.

**Readiness rollup** (connector state in `dependencies.wazuh_connector`):

```bash
curl -s "http://127.0.0.1:8000/health/ready" | jq .
```

Key fields:

- `enabled`
- `status` (`idle`, `running`, `healthy`, `error`)
- `last_success_at`
- `last_error_at`
- `last_error_message`
- `last_checkpoint_timestamp`
- cumulative `metrics` counters

## 5) Validate Live End-to-End Flow

**Concrete Ubuntu lab example (host / log path — e.g. `brute_force`):**

1. **Monitored Ubuntu client:** Wazuh agent enrolled; optional: Syscheck (FIM) watching test paths for `file_integrity_violation` experiments.
2. **Attacker VM (lab-only):** induce multiple failed SSH logins to the client so Wazuh raises an authentication / brute-force style alert.
3. **Wazuh manager:** confirm the alert exists for that agent.
4. **AegisCore API:** `GET /integrations/wazuh/connector/status` — after a poll cycle, `metrics.total_ingested` (and related counters) should move.
5. **AegisCore UI:** Alerts list → filter **brute_force** → open detail → confirm score, incident link, and response history per policy.

**Checklist (any MVP-scope Wazuh-driven scenario):**

1. Event appears in Wazuh manager.
2. Connector status metrics increase (`total_fetched`, `total_ingested`).
3. Alert is created in AegisCore through the live connector (not manual POST).
4. Risk scoring and incident linkage execute as expected.
5. Policy automation actions are recorded (dry-run/live based on policy and safety settings).

See also the **Live lab verification** section in [ubuntu-vm-lab-live-soc.md](ubuntu-vm-lab-live-soc.md).

## Operational Notes

- For normal VM/lab operation, keep `WAZUH_CONNECTOR_ENABLED=true` so live polling remains the default ingestion path.
- Use `POST /integrations/wazuh/events` only as an explicit fallback for deterministic tests or demo recovery when live upstream is unavailable.
- Checkpointing stores the last timestamp and recent external IDs to reduce duplicate processing between polling cycles.
- Connector polling uses page-size plus offset pagination and is bounded by `WAZUH_MAX_PAGES_PER_CYCLE` per cycle.
- Duplicate protection remains enforced at ingestion by `source + external_id`.
- Raw payload snapshots are preserved in `raw_alerts` and parse failures in `ingestion_failures`.
- For **single-tenant MVP** operation, run one API instance with the connector enabled to avoid redundant polling across multiple connector workers.
