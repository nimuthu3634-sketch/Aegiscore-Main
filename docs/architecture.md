# Architecture Overview

## Product Direction

AegisCore is a single-tenant SOC platform for SMEs. It centralizes alert review, incident investigation, explainable prioritization, safe automated response, and practical reporting without introducing enterprise multi-tenant complexity.

## Runtime Boundaries

- `apps/web` is the analyst-facing frontend and communicates only with backend APIs.
- `apps/api` owns ingestion, normalization, scoring, incident behavior, policies, reporting, and auditability.
- `apps/worker` remains available for background execution or replay workflows that should not block API requests.
- `ai` contains the deterministic baseline scorer, the scikit-learn training pipeline, and inference helpers used by the API.
- `postgres` stores users, assets, alerts, incidents, scores, notes, responses, policies, reports, and audit history.
- `nginx` is the local reverse-proxy entrypoint for `/` and `/api`.

## Core Request Flow

1. Wazuh-style or Suricata-style events enter the backend ingestion routes.
2. The backend preserves the raw payload and normalizes supported detections into the shared alert schema.
3. Alert scoring runs through the backend-owned deterministic baseline or optional ML scorer.
4. Matching response policies evaluate alert or incident context and create auditable response actions.
5. Alerts can remain standalone or link into multi-alert incidents.
6. Frontend list, detail, dashboard, rules, response-history, and reporting pages consume only the normalized backend contracts.

## Backend Modules

- `app/api`: typed REST routes and dependency wiring
- `app/core`: configuration, auth, and security helpers
- `app/db`: database engine, session, and seed entrypoints
- `app/models`: SQLAlchemy persistence model layer
- `app/repositories`: database access per aggregate
- `app/schemas`: Pydantic request and response contracts
- `app/services`: business logic for auth, alerts, incidents, ingestion, reporting, scoring, and automated response

## Data Model

- `roles`: single-tenant `admin` and `analyst`
- `users`: JWT-authenticated operators
- `assets`: monitored endpoints and servers
- `raw_alerts`: immutable source payload storage
- `normalized_alerts`: frontend-safe normalized alert records
- `ingestion_failures`: malformed or unsupported event ledger
- `risk_scores`: persisted score value, method, version, and explanation metadata
- `incidents`: one incident owning many linked alerts plus a retained primary alert for summary views
- `response_policies`: enabled or disabled automation rules by target, detection, threshold, action, and mode
- `response_actions`: auditable execution history with policy linkage and result fields
- `analyst_notes`: first-class notes for alerts and incidents
- `audit_logs`: lifecycle, policy, export, and workflow traceability

## Workflow Model

- Alerts support acknowledge, close, link-to-incident, and analyst-note writes.
- Incidents support validated state transitions across `new`, `triaged`, `investigating`, `contained`, `resolved`, and `false_positive`.
- Alert-to-incident linking supports either creating a new incident or attaching the alert to an existing incident.
- Every mutation writes audit history, and incident detail timelines are built from those persisted events plus first-class note and response records.

## Auth And Roles

- Authentication is JWT-based and required for all non-health API routes.
- Roles are intentionally limited to `admin` and `analyst`.
- `admin` can mutate response policies and submit manual ingestion events.
- `analyst` can execute investigation workflows and read operational/reporting surfaces, but cannot mutate policy state or submit manual ingestion events.
- The role model is explicit and scoped for single-tenant SME operation; there is no enterprise RBAC matrix, tenant hierarchy, or custom role builder.

## Scoring And Response Model

- Supported detection scope remains limited to `brute_force`, `file_integrity_violation`, `port_scan`, and `unauthorized_user_creation`.
- Risk scoring is a prioritization layer after detection, not the detector itself.
- The deterministic baseline is the production-safe default.
- The optional scikit-learn model stays loadable and auditable through stored model metadata.
- Safe internal actions such as `notify_admin`, `create_manual_review`, and `quarantine_host_flag` can complete without an external script.
- `block_ip` and `disable_user` now have built-in lab adapters with safe `ledger` backends by default; destructive backends require explicit safety flags.
- Destructive live actions remain blocked by default in development.

## Reporting Model

- Daily summaries focus on short-window SOC review.
- Weekly summaries support broader SME operational review.
- Alert, incident, and response exports are explicit, typed, and auditable.
- The reports surface stays operational and compact instead of adding enterprise BI complexity.

## Dev And Operator Boundaries

- Browser authentication remains explicit by default.
- Optional local browser auto-auth is gated behind `VITE_ENABLE_DEV_AUTH_BOOTSTRAP=true`.
- Raw payloads remain backend-owned and never need to be interpreted directly by the frontend.
- Validation uses the real API surface with fixture-backed ingestion as the deterministic baseline, and optional live connector polling in VM/lab environments.

## Known Limitations

- Browser tests validate core read paths and major write paths, but not every role-restriction or edge-path branch yet.
- Some asset enrichment remains backend-derived rather than source-owned because the project stays intentionally SME-scoped.
