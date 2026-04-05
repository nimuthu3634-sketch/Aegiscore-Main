# Architecture Overview

## Product Direction

AegisCore is a single-tenant SOC platform for SMEs. The platform centralizes security monitoring, alert prioritization, investigation workflows, and basic automated response without introducing enterprise multi-tenant complexity.

## Service Boundaries

- `apps/web` is the frontend shell and only communicates with backend APIs.
- `apps/api` owns integration boundaries, alert normalization, incident creation, auditability, and API delivery.
- `apps/worker` is reserved for asynchronous policy execution and background automation.
- `ai` holds scoring logic and model-related code used by backend services.
- `postgres` stores normalized alerts, incidents, response history, and audit history.
- `nginx` is the single local entrypoint that routes `/` to the frontend and `/api` to the backend.

## Initial Backend Modules

- `app/api/routes`: HTTP route definitions
- `app/core`: configuration
- `app/db`: database engine and session setup
- `app/models`: SQLAlchemy models for alerts, incidents, response actions, and audit events
- `app/schemas`: API response schemas
- `app/services`: service-layer logic such as health checks

## Detection Scope

Only these detections are represented in the initial schema and UI shell:

1. `brute_force`
2. `file_integrity_violation`
3. `port_scan`
4. `unauthorized_user_creation`

