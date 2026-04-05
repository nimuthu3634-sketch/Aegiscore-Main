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

- `app/api/routes`: typed REST endpoints for auth, dashboard, assets, alerts, incidents, responses, and health
- `app/api/deps`: database and current-user dependencies
- `app/api/routes`: HTTP route definitions
- `app/core`: configuration
- `app/core/security`: JWT and password hashing helpers
- `app/db`: database engine and session setup
- `app/models`: SQLAlchemy models for roles, users, assets, raw alerts, normalized alerts, incidents, risk scores, response actions, analyst notes, and audit logs
- `app/repositories`: database access by aggregate or resource
- `app/schemas`: API response schemas
- `app/services`: auth, dashboard, alerts, incidents, response actions, seed logic, serializers, and health checks

## Backend Data Model

- `roles`: single-tenant access roles limited to `admin` and `analyst`
- `users`: authenticated platform users with JWT-backed login
- `assets`: monitored SME systems represented in the SOC
- `raw_alerts`: preserved source payloads from integrations such as Wazuh and Suricata
- `normalized_alerts`: alert records transformed into the common AegisCore schema
- `risk_scores`: explainable alert risk-scoring records
- `incidents`: analyst-facing incident records generated from normalized alerts, with one incident able to own multiple linked alerts and a primary alert retained for summary views
- `response_actions`: basic automated or analyst-triggered response activity
- `analyst_notes`: persisted notes attached directly to alert or incident investigations
- `audit_logs`: security and workflow history for traceability

## Workflow State Model

- Alert lifecycle actions are persisted through explicit APIs for acknowledge, close, and link-to-incident workflows.
- Alert-to-incident linkage supports either attaching an alert to an existing incident or creating a new incident from the alert workflow entrypoint.
- Alert display state remains frontend-friendly through derived labels such as `triaged`, `contained`, and `pending_response`.
- Incident workflow state is modeled directly as `new`, `triaged`, `investigating`, `contained`, `resolved`, and `false_positive`.
- Every workflow mutation writes an audit entry, and note creation also persists a first-class analyst note record.

## Detection Scope

Only these detections are represented in the initial schema and UI shell:

1. `brute_force`
2. `file_integrity_violation`
3. `port_scan`
4. `unauthorized_user_creation`
