# Environment Reference

## Root Compose Variables

- `POSTGRES_DB`: local database name
- `POSTGRES_USER`: local database user
- `POSTGRES_PASSWORD`: local database password
- `POSTGRES_PORT`: host port for PostgreSQL
- `API_PORT`: host port for the FastAPI service
- `WEB_PORT`: host port for the Vite frontend
- `NGINX_PORT`: host port for the reverse proxy
- `JWT_SECRET_KEY`: development JWT secret
- `JWT_ALGORITHM`: JWT signing algorithm
- `ACCESS_TOKEN_EXPIRE_MINUTES`: bearer token lifetime for API auth
- `WAZUH_BASE_URL`: Wazuh manager API base URL
- `WAZUH_USERNAME`: username for Wazuh basic or token-auth bootstrap mode
- `WAZUH_PASSWORD`: password for Wazuh basic or token-auth bootstrap mode
- `WAZUH_BEARER_TOKEN`: static bearer token for direct bearer mode
- `WAZUH_AUTH_MODE`: Wazuh auth mode, one of `basic`, `token`, `bearer`
- `WAZUH_AUTH_ENDPOINT`: token bootstrap endpoint used when `WAZUH_AUTH_MODE=token`
- `WAZUH_ALERTS_PATH`: Wazuh events endpoint path polled by the live connector
- `WAZUH_CONNECTOR_ENABLED`: enables the API background polling connector for Wazuh
- `WAZUH_POLL_INTERVAL_SECONDS`: connector polling interval for live Wazuh fetch cycles
- `WAZUH_TIMEOUT_SECONDS`: request timeout for each Wazuh API call
- `WAZUH_RETRY_ATTEMPTS`: retry attempts for transient Wazuh API failures
- `WAZUH_RETRY_BACKOFF_SECONDS`: linear backoff delay between retries
- `WAZUH_VERIFY_TLS`: whether TLS certificates are validated for Wazuh HTTPS
- `WAZUH_CA_FILE`: optional CA bundle path for custom/internal PKI validation
- `WAZUH_PAGE_SIZE`: page size requested from the live Wazuh alerts endpoint
- `WAZUH_MAX_PAGES_PER_CYCLE`: maximum Wazuh pages fetched per poll cycle
- `WAZUH_OFFSET_PARAM`: query parameter used for paged Wazuh offset fetches
- `WAZUH_SINCE_PARAM`: query parameter name used to pass the checkpoint timestamp
- `WAZUH_TIMESTAMP_FIELD`: timestamp field extracted from fetched Wazuh events
- `SURICATA_SOURCE`: identifier for the Suricata source
- `SURICATA_CONNECTOR_ENABLED`: enables live Suricata connector polling
- `SURICATA_CONNECTOR_MODE`: connector mode, currently `file_tail`
- `SURICATA_EVE_FILE_PATH`: path to Suricata `eve.json` on the API runtime host/container
- `SURICATA_POLL_INTERVAL_SECONDS`: Suricata connector poll interval
- `SURICATA_MAX_EVENTS_PER_CYCLE`: max new lines/events consumed per poll cycle
- `SURICATA_RETRY_ATTEMPTS`: retry attempts for transient Suricata connector runtime errors
- `SURICATA_RETRY_BACKOFF_SECONDS`: linear retry backoff for Suricata connector runtime errors
- `SURICATA_FAIL_WHEN_SOURCE_MISSING`: whether connector cycles fail when `SURICATA_EVE_FILE_PATH` is unavailable
- `INGESTION_ALLOW_ASSET_AUTOCREATE`: whether ingestion may create a new asset record when a payload includes a host IP or hostname that does not exist yet
- `INGESTION_DEFAULT_ASSET_CRITICALITY`: default criticality applied to auto-created assets when the source payload does not provide one
- `VITE_API_BASE_URL`: frontend API base URL, defaulting to `/api`
- `VITE_ENABLE_DEV_AUTH_BOOTSTRAP`: optional local-browser shortcut for development only; keep `false` unless you intentionally want the frontend API client to auto-login with dev credentials
- `DEV_SEED_ADMIN_USERNAME`: seeded local admin username
- `DEV_SEED_ADMIN_PASSWORD`: seeded local admin password
- `DEV_SEED_ANALYST_USERNAME`: seeded local analyst username
- `DEV_SEED_ANALYST_PASSWORD`: seeded local analyst password
- `SCORING_STRATEGY`: runtime scoring mode, either `baseline` or `model`
- `SCORING_BASELINE_VERSION`: deterministic baseline version identifier stored with scores
- `SCORING_MODEL_PATH`: model artifact path used when `SCORING_STRATEGY=model`
- `SCORING_MODEL_METADATA_PATH`: metadata JSON path paired with the model artifact
- `SCORING_MODEL_VERSION`: fallback runtime model version label for local development
- `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE`: safety gate for live destructive adapters such as `block_ip` and `disable_user`; keep `false` for local development
- `AUTOMATED_RESPONSE_MAX_RETRIES`: maximum automated execution attempts before a response action is marked failed
- `AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED`: enables first-party backend adapters for response actions
- `AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED`: explicit gate for running live lab adapters
- `AUTOMATED_RESPONSE_BLOCK_IP_BACKEND`: backend for `block_ip` (`ledger`, `iptables`, or `script`)
- `AUTOMATED_RESPONSE_DISABLE_USER_BACKEND`: backend for `disable_user` (`ledger`, `linux_lock`, or `script`)
- `AUTOMATED_RESPONSE_LEDGER_PATH`: JSONL ledger path used by built-in lab-safe action backends
- `AUTOMATED_RESPONSE_HOST_TAG_PATH`: JSONL path for optional host-tag output from quarantine action
- `AUTOMATED_RESPONSE_ENABLE_HOST_TAG_WRITE`: when true, quarantine writes an additional safe host tag entry
- `RESPONSE_ADAPTER_BLOCK_IP_SCRIPT`: optional script path for live `block_ip`
- `RESPONSE_ADAPTER_DISABLE_USER_SCRIPT`: optional script path for live `disable_user`
- `RESPONSE_ADAPTER_QUARANTINE_HOST_FLAG_SCRIPT`: optional script path for live `quarantine_host_flag`
- `RESPONSE_ADAPTER_CREATE_MANUAL_REVIEW_SCRIPT`: optional script path for live `create_manual_review`
- `RESPONSE_ADAPTER_NOTIFY_ADMIN_SCRIPT`: optional script path for live `notify_admin`
- `NOTIFICATIONS_ENABLED`: enables backend notification dispatch policy evaluation
- `NOTIFICATIONS_MODE`: delivery mode (`log` or `smtp`)
- `NOTIFICATIONS_RISK_THRESHOLD`: risk score threshold for high-risk incident notifications
- `NOTIFICATIONS_INCIDENT_STATES`: comma-separated incident states that allow notifications
- `NOTIFICATIONS_RESPONSE_STATUSES`: comma-separated response execution statuses that trigger notifications
- `NOTIFICATIONS_ADMIN_RECIPIENTS`: comma-separated recipient emails for administrator notifications
- `NOTIFICATIONS_SENDER`: sender address used in SMTP email mode
- `SMTP_HOST`: SMTP server hostname for notification email delivery
- `SMTP_PORT`: SMTP server port for notification email delivery
- `SMTP_USERNAME`: optional SMTP auth username
- `SMTP_PASSWORD`: optional SMTP auth password
- `SMTP_USE_TLS`: enable SMTPS (`SMTP_SSL`) mode
- `SMTP_USE_STARTTLS`: enable STARTTLS negotiation for plain SMTP connections
- `SMTP_TIMEOUT_SECONDS`: SMTP connection timeout in seconds
- `DB_CONNECT_MAX_ATTEMPTS`: API container startup attempts before failing when database is unavailable
- `DB_CONNECT_BACKOFF_SECONDS`: delay between API database-connect retry attempts during startup

## App-Specific Files

- `apps/web/.env.example`: frontend runtime variables
- `apps/api/.env.example`: API settings, auth values, seed credentials, and integration URLs
- `apps/worker/.env.example`: worker polling and database settings
- `ai/.env.example`: AI dataset and model artifact settings for training/inference scripts

## Frontend Auth Notes

- The normal frontend path expects operators to sign in through `/login`.
- Local browser auto-auth is opt-in rather than implicit.
- If `VITE_ENABLE_DEV_AUTH_BOOTSTRAP=true`, the frontend may request a local dev token with `VITE_DEV_API_USERNAME` and `VITE_DEV_API_PASSWORD`.
- Leave dev bootstrap disabled for most validation work so the login boundary stays realistic.

## Automated Response Safety Notes

- Automated response is policy-driven and currently scoped to `brute_force`, `file_integrity_violation`, `port_scan`, and `unauthorized_user_creation`.
- Built-in adapters are first-party and backend-owned; they do not require external scripts for lab-safe defaults.
- Live execution still requires `AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true`.
- Destructive adapters remain blocked unless `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=true`.
- `ledger` backends are safe defaults for local/lab operation and persist action evidence without destructive host changes.
- Response execution attempts, final outcomes, and policy matches are written to audit history and exposed through the response history APIs.

## Ingestion Notes

- Primary lab ingestion path is connector-driven (`WAZUH_CONNECTOR_ENABLED=true` and `SURICATA_CONNECTOR_ENABLED=true`) so events flow continuously from upstream sources.
- Fixture-friendly backend ingestion routes remain available at `POST /integrations/wazuh/events` and `POST /integrations/suricata/events` for test/demo workflows.
- Live Wazuh polling can be enabled with `WAZUH_CONNECTOR_ENABLED=true`; it continuously fetches events, applies checkpointing, and pushes each event through the same normalization/scoring/incident/response pipeline used by manual ingestion.
- Live Suricata polling can be enabled with `SURICATA_CONNECTOR_ENABLED=true`; it tails `eve.json` incrementally via stored file offsets and sends events through the same ingestion/scoring/response path.
- Successful source events are normalized into the existing alert schema and continue through scoring, incident linkage, and automated-response evaluation.
- Malformed or unsupported events are written to `ingestion_failures` with raw payload snapshots, retry counters, and error metadata for local debugging.
- Duplicate events are de-duplicated by `source + external_id` and safely return the existing normalized alert.
- Connector state and last sync telemetry are available at `GET /integrations/wazuh/connector/status`.
- Suricata connector state and last sync telemetry are available at `GET /integrations/suricata/connector/status`.

## Health And Readiness Notes

- `GET /health`: high-level API + database status.
- `GET /health/live`: process liveness signal.
- `GET /health/ready`: readiness with dependency details (database and connector status).
- Docker Compose uses service healthchecks and `depends_on` health conditions to improve local startup ordering.
