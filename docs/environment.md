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
- `WAZUH_BASE_URL`: future Wazuh integration base URL
- `SURICATA_SOURCE`: identifier for the Suricata source
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
- `RESPONSE_ADAPTER_BLOCK_IP_SCRIPT`: optional script path for live `block_ip`
- `RESPONSE_ADAPTER_DISABLE_USER_SCRIPT`: optional script path for live `disable_user`
- `RESPONSE_ADAPTER_QUARANTINE_HOST_FLAG_SCRIPT`: optional script path for live `quarantine_host_flag`
- `RESPONSE_ADAPTER_CREATE_MANUAL_REVIEW_SCRIPT`: optional script path for live `create_manual_review`
- `RESPONSE_ADAPTER_NOTIFY_ADMIN_SCRIPT`: optional script path for live `notify_admin`

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
- Destructive live actions are intentionally blocked unless `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=true`.
- If a live adapter script path is unset for a supported action, AegisCore records a warning or internal completion event rather than silently failing.
- Response execution attempts, final outcomes, and policy matches are written to audit history and exposed through the response history APIs.

## Ingestion Notes

- Fixture-friendly backend ingestion routes are available at `POST /integrations/wazuh/events` and `POST /integrations/suricata/events`.
- Successful source events are normalized into the existing alert schema and continue through scoring, incident linkage, and automated-response evaluation.
- Malformed or unsupported events are written to `ingestion_failures` with raw payload snapshots, retry counters, and error metadata for local debugging.
- Duplicate events are de-duplicated by `source + external_id` and safely return the existing normalized alert.
