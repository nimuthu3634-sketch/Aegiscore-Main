# Ubuntu VM Lab — Live SOC With AegisCore

This document is the **reference topology** for running AegisCore as a **real connected SOC product** in an **Ubuntu-based VirtualBox lab**: live **Wazuh** polling for host/log events and live **Suricata** `file_tail` for network events. Fixture `POST` ingestion remains **test/demo-only** (see [Operator guide](operator-guide.md)).

## Intended lab posture

| VM role | Typical OS | Stack | Role in the product |
| --- | --- | --- | --- |
| **SOC server** | **Ubuntu Server** | Docker Engine + Compose, AegisCore (`api`, `web`, `postgres`, `nginx`, …) | Single-tenant console, JWT auth, PostgreSQL, **live connectors** |
| **Wazuh manager** | Ubuntu Server (dedicated VM recommended) | Wazuh manager + dashboard API | Source of truth for **agent/FIM/auth** events AegisCore polls |
| **Monitored host** | Ubuntu Desktop or Server | **Wazuh agent**, **Syscheck (FIM)** enabled | Generates in-scope host events (`brute_force`, `file_integrity_violation`, `unauthorized_user_creation`) when rules match |
| **Network sensor** | Ubuntu Server (SOC host or inline VM) | **Suricata** writing **`eve.json`** | Network visibility; primary in-scope path for **`port_scan`** |
| **Attacker / test** | Ubuntu or Kali | `hydra`, `nmap`, etc. (lab-only) | Controlled replay to prove **end-to-end** detection → AegisCore alert |

**VirtualBox:** use a host-only or internal network, static IPs, and NTP/time sync so Wazuh timestamps and AegisCore checkpoints stay coherent.

**Product scope:** only the four supported detections (`brute_force`, `file_integrity_violation`, `port_scan`, `unauthorized_user_creation`). Tune Wazuh rules and Suricata signatures so lab noise maps into those categories where possible.

## Normal operating mode (live connectors)

For VM/lab production-style operation:

- Set **`WAZUH_CONNECTOR_ENABLED=true`** so the API **polls** the Wazuh manager alerts API (see [wazuh-live-integration.md](wazuh-live-integration.md)).
- Set **`SURICATA_CONNECTOR_ENABLED=true`** and **`SURICATA_CONNECTOR_MODE=file_tail`** so the API **tails** `eve.json` (see [suricata-live-integration.md](suricata-live-integration.md)).

Manual **`POST /integrations/wazuh/events`** and **`POST /integrations/suricata/events`** are **admin-only fallbacks** for CI, demos when upstream is down, or deterministic replay—not the primary operational story.

## Environment variables (summary)

Full reference: [environment.md](../environment.md). Minimum to wire an Ubuntu lab:

**Wazuh (live polling)**

- `WAZUH_BASE_URL` — e.g. `https://<wazuh-manager-ip>:55000` (reachable from the **`api` container**)
- `WAZUH_CONNECTOR_ENABLED=true`
- `WAZUH_AUTH_MODE` + `WAZUH_USERNAME` / `WAZUH_PASSWORD` **or** `WAZUH_BEARER_TOKEN`
- Optional: `WAZUH_VERIFY_TLS`, `WAZUH_CA_FILE`, poll/page tuning (`WAZUH_POLL_INTERVAL_SECONDS`, …)

**Suricata (live `file_tail`)**

- `SURICATA_CONNECTOR_ENABLED=true`
- `SURICATA_CONNECTOR_MODE=file_tail`
- `SURICATA_EVE_FILE_PATH` — path **inside the API container** (usually bind-mount host `eve.json`)
- Optional: `SURICATA_POLL_INTERVAL_SECONDS`, `SURICATA_FAIL_WHEN_SOURCE_MISSING`

**Bind-mount example (host `docker-compose.override.yml` on the SOC server)**

```yaml
services:
  api:
    volumes:
      - /var/log/suricata/eve.json:/var/log/suricata/eve.json:ro
```

Adjust the host path to match where Suricata writes `eve.json` on your sensor VM (NFS, SSHFS, or co-located Suricata on the same host are all valid if the file is stable and readable).

## Ubuntu SOC host — first start

```bash
cd /path/to/Aegiscore-Main
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
docker compose ps
```

Use `http://<soc-server-ip>/` (via NGINX) or `http://<soc-server-ip>:8000` for direct API checks from the lab network.

## Connector health and readiness (documented, usable)

Connector routes require an authenticated JWT (same as the rest of the API).

### 1) Obtain a token (Ubuntu / `curl`)

```bash
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"AegisCore123!"}' | jq -r .access_token)
```

(Use your seeded credentials; through NGINX use `http://localhost/api/auth/login` with the same JSON body.)

### 2) Wazuh connector status

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/integrations/wazuh/connector/status" | jq .
```

### 3) Suricata connector status

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/integrations/suricata/connector/status" | jq .
```

Inspect `enabled`, `status`, `last_success_at` / `last_error_at`, `metrics` (`total_fetched`, `total_ingested`, …), and Suricata `checkpoint_offset` / `source_path`.

### 4) Readiness (DB + connector dependency rollup)

```bash
curl -s "http://127.0.0.1:8000/health/ready" | jq .
```

`dependencies.wazuh_connector` and `dependencies.suricata_connector` reflect enabled flag plus last known connector state from PostgreSQL (see API implementation). Use this for a **single** “is the stack wired?” check; use the **integration status** URLs above for **deep** connector debugging.

### 5) UI

Analysts with appropriate roles can use the same backend data through the SOC console; connector-specific JSON is most detailed via the API.

## Live lab verification

Perform only on isolated lab networks with explicit authorization.

### Example A — Wazuh host-side signal (e.g. `brute_force`)

**Goal:** Prove **host/log path**: Wazuh → AegisCore poll → normalized alert → score → incident/response as configured.

1. On the **monitored Ubuntu client**, ensure the **Wazuh agent** is enrolled and reporting to the manager.
2. On the **attacker VM**, generate **failed SSH logins** against the client (e.g. repeated wrong passwords)—**lab scope only**.
3. In **Wazuh** (UI or API), confirm an authentication / brute-force style alert exists for the agent.
4. On the **SOC server**, call **`GET .../integrations/wazuh/connector/status`** and confirm **`total_ingested`** (or relevant metrics) increases after a poll cycle.
5. In **AegisCore**, open **Alerts**, filter by **`brute_force`** (or your mapped detection), and confirm the new alert, score explanation, and linked incident/response if policies apply.

**Alternative in-scope host test:** trigger **FIM** (`file_integrity_violation`) by modifying a file under a Syscheck-watched path on the monitored host (per your Wazuh FIM rules).

### Example B — Suricata network signal (`port_scan`)

**Goal:** Prove **network path**: Suricata `eve.json` → AegisCore tail → normalized alert → score → incident/response.

1. Ensure Suricata is seeing traffic on the lab segment and appending **alert** (or mapped) events to **`eve.json`**.
2. From the **attacker VM**, run a **TCP port scan** toward a monitored target (e.g. `nmap -sS <target-ip> -p 22,3389`—lab only).
3. On the sensor, `grep` / `tail` `eve.json` and confirm a **Suricata alert** line was written.
4. Call **`GET .../integrations/suricata/connector/status`** and confirm **`total_ingested`** increases and checkpoint advances.
5. In **AegisCore**, confirm a **`port_scan`** (or parser-mapped in-scope) alert appears with expected evidence (e.g. destination port context).

> **Note:** In-scope **Suricata** parsing is centered on **`port_scan`**; other Wazuh-centric detections are expected primarily from **Wazuh** (see [suricata-live-integration.md](suricata-live-integration.md) scope guardrails).

## Manual POST ingestion (fallback only)

- **`POST /integrations/wazuh/events`** / **`POST /integrations/suricata/events`**: **admin** role; use for **tests**, **CI**, or **demo recovery** when live connectors or lab generators are unavailable.
- Does **not** replace live connectors for the documented Ubuntu lab story.

## Related documentation

- [Wazuh live integration](wazuh-live-integration.md)
- [Suricata live integration](suricata-live-integration.md)
- [Operator guide](operator-guide.md)
- [Operator runbook](operator-runbook.md)
- [Analyst guide](analyst-guide.md)
- [Environment reference](../environment.md)

## Remaining lab-only limitations

- **Suricata:** only **`file_tail`** is implemented; no authenticated forwarding receiver mode.
- **Wazuh:** polling targets **common** manager API response shapes; unusual filters or envelopes may need env tuning.
- **Single-tenant:** one connector-enabled API instance; avoid duplicate pollers against the same manager/file.
- **TLS:** internal lab CAs require `WAZUH_CA_FILE` (or equivalent trust) when `WAZUH_VERIFY_TLS=true`.
