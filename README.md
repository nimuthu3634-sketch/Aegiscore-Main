# AegisCore

AegisCore is a production-minded, single-tenant AI-integrated SOC platform for small and medium enterprises. This repository is structured as a clean monorepo for the core web UI, API, worker runtime, AI logic, infrastructure, scripts, and documentation.

## Monorepo Layout

- `apps/web`: React + TypeScript + Tailwind CSS + Recharts SOC dashboard shell
- `apps/api`: FastAPI + SQLAlchemy + Alembic backend with PostgreSQL wiring
- `apps/worker`: background worker runtime for future automated response workflows
- `ai`: AI and risk-scoring modules
- `infra/nginx`: NGINX configuration for frontend and API routing
- `infra/docker`: Dockerfiles used by local development services
- `scripts`: helper scripts for local workflow and validation
- `docs`: architecture and environment documentation

## Local Startup

1. Review the env examples and override values only when needed.
2. Start the local stack:

```powershell
docker compose up --build
```

3. Open the platform:

- Frontend through NGINX: `http://localhost`
- API health through NGINX: `http://localhost/api/health`
- API direct: `http://localhost:8000/health`
- Frontend direct: `http://localhost:5173`

## Services

- `postgres`: PostgreSQL 16 for local persistence
- `api`: FastAPI service with modular app structure and `/health`
- `worker`: background worker shell for future policy execution
- `web`: Vite-powered React frontend shell
- `nginx`: reverse proxy routing `/` to the frontend and `/api` to the backend

## Environment Files

- Root compose defaults: `.env.example`
- Web envs: `apps/web/.env.example`
- API envs: `apps/api/.env.example`
- Worker envs: `apps/worker/.env.example`
- AI envs: `ai/.env.example`

## Validation Commands

```powershell
docker compose config
docker compose up --build -d
Invoke-WebRequest http://localhost:8000/health
Invoke-WebRequest http://localhost/
```

## Notes

- The backend owns all external security integrations; the frontend talks only to backend APIs.
- Raw payload preservation, normalized alerts, incidents, audit history, and response history are reflected in the initial backend schema.
- Frontend work follows the AegisCore dark SOC theme and is prepared for Figma-first design iteration in later milestones.

