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
- `WAZUH_BASE_URL`: future Wazuh integration base URL
- `SURICATA_SOURCE`: identifier for the Suricata source
- `VITE_API_BASE_URL`: frontend API base URL, defaulting to `/api`

## App-Specific Files

- `apps/web/.env.example`: frontend runtime variables
- `apps/api/.env.example`: API settings and integration URLs
- `apps/worker/.env.example`: worker polling and database settings
- `ai/.env.example`: AI package data and artifact settings

