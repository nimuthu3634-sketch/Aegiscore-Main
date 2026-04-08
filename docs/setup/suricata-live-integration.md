# Suricata Live Integration (VM Lab)

This guide enables continuous Suricata ingestion in AegisCore using `eve.json` tail polling.

## Readiness Level

- **Implemented**: live Suricata connector in `file_tail` mode with inode/offset checkpointing, retries, malformed-line logging, duplicate protection, and connector status visibility.
- **Limited mode**: authenticated forwarding endpoint mode is not implemented yet.
- **Operational default**: live Suricata `file_tail` ingestion is the normal VM/lab path when `SURICATA_CONNECTOR_ENABLED=true`; fixture posting is reserved for explicit test/demo fallback.

## Scope Guardrails

- Supported detections remain limited to:
  - `port_scan`
  - `brute_force` only when existing Suricata parsing safely maps signal text into in-scope detection logic
- Unsupported detections are rejected and logged into `ingestion_failures`.
- Frontend behavior remains source-agnostic; integration complexity stays in backend services.

## 1) Choose Connector Mode

Current connector mode:

- `file_tail` (recommended for VM labs)

The connector tails `eve.json`, tracks file offset + inode checkpoint state, and processes only new lines.

## 2) Configure Environment Variables

Set these in API env/compose settings:

- `SURICATA_CONNECTOR_ENABLED=true`
- `SURICATA_CONNECTOR_MODE=file_tail`
- `SURICATA_EVE_FILE_PATH=/var/log/suricata/eve.json`
- `SURICATA_POLL_INTERVAL_SECONDS=15`
- `SURICATA_MAX_EVENTS_PER_CYCLE=250`
- `SURICATA_RETRY_ATTEMPTS=2`
- `SURICATA_RETRY_BACKOFF_SECONDS=1`
- `SURICATA_FAIL_WHEN_SOURCE_MISSING=true`

Also ensure general ingestion/scoring env vars are configured per your deployment.

## 3) Mount Suricata Logs Into API Runtime

If Suricata runs on a separate VM/container, expose or mount `eve.json` to the API runtime path configured in `SURICATA_EVE_FILE_PATH`.

For Docker-based local lab setups, bind a host or shared volume path into the API container.

## 4) Start and Migrate

```powershell
docker compose up --build -d
docker compose exec api alembic upgrade head
```

## 5) Verify Connector Health

With authenticated API access:

```http
GET /integrations/suricata/connector/status
```

Key fields:

- `enabled`
- `status` (`idle`, `running`, `healthy`, `error`)
- `source_path`
- `checkpoint_offset` and `checkpoint_inode`
- cumulative `metrics`

## 6) End-to-End Lab Validation

1. generate a controlled port scan in the monitored network segment
2. confirm event lands in Suricata `eve.json`
3. check connector status counters increment (`total_fetched`, `total_ingested`)
4. verify alert appears in AegisCore and inherits normal scoring/incident/response behavior

## Operational Notes

- For normal VM/lab operation, keep `SURICATA_CONNECTOR_ENABLED=true` so live file-tail polling stays the default ingestion path.
- Use `POST /integrations/suricata/events` only as an explicit fallback for deterministic tests or demo recovery when live `eve.json` access is unavailable.
- When `SURICATA_FAIL_WHEN_SOURCE_MISSING=true`, connector status reports errors if the `eve.json` source path is unavailable.
- Duplicate protection remains enforced by `source + external_id` in ingestion.
- Raw source payloads are preserved in `raw_alerts`.
- Malformed `eve.json` lines are logged into `ingestion_failures` with line/offset metadata.
- For single-tenant SME operation, run one connector-enabled API instance to avoid duplicate tailing from multiple pollers.
