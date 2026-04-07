# Wazuh Live Integration (VM Lab)

This guide enables continuous live Wazuh ingestion in AegisCore while preserving the existing backend normalization, scoring, incident creation, and response automation flow.

## Readiness Level

- **Implemented**: live Wazuh polling connector with auth modes (`basic`, `token`, `bearer`), retries, checkpointing, duplicate protection, and connector status visibility.
- **Limited mode**: compatibility currently targets common Wazuh response envelopes (`list`, `data.affected_items`, `data.items`) and may require tuning for other manager/API variants.
- **Validation baseline**: fixture-backed ingestion remains the default deterministic validation path; live Wazuh checks are optional VM/lab verification.

## Scope Guardrails

- Supported detections remain limited to:
  - `brute_force`
  - `file_integrity_violation`
  - `port_scan`
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

Use an authenticated API token and query:

```http
GET /integrations/wazuh/connector/status
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

Generate a controlled VM-lab event (for example brute force or FIM), then confirm:

1. event appears in Wazuh manager
2. connector status metrics increase (`total_fetched`, `total_ingested`)
3. alert is created in AegisCore through normal routes
4. risk scoring and incident linkage execute as expected
5. policy automation actions are recorded (dry-run/live based on policy and safety settings)

## Operational Notes

- Checkpointing stores the last timestamp and recent external IDs to reduce duplicate processing between polling cycles.
- Duplicate protection remains enforced at ingestion by `source + external_id`.
- Raw payload snapshots are preserved in `raw_alerts` and parse failures in `ingestion_failures`.
- For single-tenant SME operation, run one API instance with the connector enabled to avoid redundant polling across multiple connector workers.
