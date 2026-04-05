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
- `VITE_API_BASE_URL`: frontend API base URL, defaulting to `/api`
- `DEV_SEED_ADMIN_USERNAME`: seeded local admin username
- `DEV_SEED_ADMIN_PASSWORD`: seeded local admin password
- `DEV_SEED_ANALYST_USERNAME`: seeded local analyst username
- `DEV_SEED_ANALYST_PASSWORD`: seeded local analyst password
- `SCORING_STRATEGY`: runtime scoring mode, either `baseline` or `model`
- `SCORING_BASELINE_VERSION`: deterministic baseline version identifier stored with scores
- `SCORING_MODEL_PATH`: model artifact path used when `SCORING_STRATEGY=model`
- `SCORING_MODEL_METADATA_PATH`: metadata JSON path paired with the model artifact
- `SCORING_MODEL_VERSION`: fallback runtime model version label for local development

## App-Specific Files

- `apps/web/.env.example`: frontend runtime variables
- `apps/api/.env.example`: API settings, auth values, seed credentials, and integration URLs
- `apps/worker/.env.example`: worker polling and database settings
- `ai/.env.example`: AI dataset and model artifact settings for training/inference scripts
