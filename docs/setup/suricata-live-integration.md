# Suricata Live Integration (VM Lab)

This guide enables continuous Suricata ingestion in AegisCore using `eve.json` tail polling.

For the **Ubuntu SOC host + VirtualBox lab** (sensor VM or co-located Suricata, bind-mounted `eve.json`), see **[ubuntu-vm-lab-live-soc.md](ubuntu-vm-lab-live-soc.md)** first.

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

With authenticated JWT:

```http
GET /integrations/suricata/connector/status
```

**Direct API (Ubuntu SOC host):**

```bash
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_ADMIN_PASSWORD"}' | jq -r .access_token)

curl -s -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/integrations/suricata/connector/status" | jq .
```

**Through NGINX:** `http://localhost/api/integrations/suricata/connector/status` with the same header.

**Readiness:** `GET /health/ready` → `dependencies.suricata_connector`.

Key fields:

- `enabled`
- `status` (`idle`, `running`, `healthy`, `error`)
- `source_path`
- `checkpoint_offset` and `checkpoint_inode`
- cumulative `metrics`

## 6) End-to-End Lab Validation

**Concrete Ubuntu lab example (`port_scan`):**

1. **Suricata** observes the lab segment; `eve.json` is mounted into the AegisCore **`api`** container at `SURICATA_EVE_FILE_PATH`.
2. **Attacker VM (lab-only):** run a TCP scan toward a visible target, e.g. `nmap -sS <target-ip> -p 22,3389`.
3. On the sensor: `tail` / `grep` `eve.json` and confirm a **Suricata alert** JSON line was appended.
4. **AegisCore:** `GET /integrations/suricata/connector/status` — `total_ingested` increases and checkpoint advances.
5. **AegisCore UI:** Alerts → **`port_scan`** (or parser-mapped in-scope type) → detail → scoring, incident, responses.

**Short checklist:**

1. Controlled port scan (or other in-scope network test) in the monitored segment.
2. Event lands in Suricata `eve.json`.
3. Connector status counters increment (`total_fetched`, `total_ingested`).
4. Alert appears in AegisCore with normal scoring/incident/response behavior.

See [ubuntu-vm-lab-live-soc.md](ubuntu-vm-lab-live-soc.md) for the full lab role diagram.

## Operational Notes

- For normal VM/lab operation, keep `SURICATA_CONNECTOR_ENABLED=true` so live file-tail polling stays the default ingestion path.
- Use `POST /integrations/suricata/events` only as an explicit fallback for deterministic tests or demo recovery when live `eve.json` access is unavailable.
- When `SURICATA_FAIL_WHEN_SOURCE_MISSING=true`, connector status reports errors if the `eve.json` source path is unavailable.
- Duplicate protection remains enforced by `source + external_id` in ingestion.
- Raw source payloads are preserved in `raw_alerts`.
- Malformed `eve.json` lines are logged into `ingestion_failures` with line/offset metadata.
- For single-tenant SME operation, run one connector-enabled API instance to avoid duplicate tailing from multiple pollers.
