# AGENTS.md

## Mission

AegisCore is the **final scoped v1 product** for this project: a **single-tenant** SOC console for **SME/lab** deployment. It monitors **system logs** (Wazuh) and **network traffic** (Suricata), supports only the four approved detections, and provides dashboard, risk scoring, basic automated response, and incident/response recording. It is **not an enterprise commercial SOC platform** and not a toy demo.

Business goal: deliver a defensible, testable end-to-end SOC workflow within that scope—not full commercial-grade or large-scale enterprise features.

## Required Workflow

- Use `/plan` first for every major step in this repository.
- Treat this project as the final scoped v1 product for SME/lab security teams, not as a throwaway demo or sandbox app.
- After each milestone, run validations for the changed areas and fix failures before moving on.
- After each step, summarize the changed files.
- Update docs continuously as behavior, architecture, setup, or env vars change.
- Do not leave placeholder code behind.

## Detection Scope

Only the following detections are in scope unless the user explicitly expands scope:

1. `brute_force`
2. `file_integrity_violation`
3. `port_scan`
4. `unauthorized_user_creation`

Do not add extra detection types, speculative threat modules, or enterprise-only security workflows without explicit approval.

## Core Product Capabilities

- Ingest security events from Wazuh and Suricata.
- Normalize alerts into a common schema.
- Create incidents from alerts.
- Score alerts with AI and risk logic.
- Support analyst investigation workflows.
- Support basic automated response policies.
- Store audit history, response history, and incident history.
- Provide a clean SOC dashboard frontend.

## Architecture Constraints

- Frontend must talk only to backend APIs.
- Backend handles all Wazuh and Suricata integration.
- Use modular architecture, not a monolith with random folders.
- Use environment variables for all secrets and integration URLs.
- Preserve raw source payloads for debugging and auditability.
- Keep the system single-tenant and SME-focused.
- Do not add enterprise multi-tenant SaaS complexity.

## Frontend Product And Design Rules

### Brand

Use the strict AegisCore brand theme. Do not invent a different color system.

- Primary orange: `#F97316`
- Orange hover: `#EA580C`
- Deep black: `#0A0A0A`
- Panel dark: `#111827`
- Border dark: `#1F2937`
- Text light: `#F9FAFB`
- Text soft: `#D1D5DB`
- Muted gray: `#9CA3AF`
- Danger: `#EF4444`
- Success: `#22C55E`
- Warning: `#F59E0B`

### Visual Direction

- Premium SOC console
- Dark
- Clean
- Sharp
- Minimal
- Bold

Use the AegisCore logo in frontend work.

### Figma-First Rule

Use the connected Figma plugin/tool for design system work and frontend page design whenever possible. Do not skip Figma-based design planning. If the Figma tool requires a file URL or node selection, stop and ask the user for it instead of guessing.

## Approved Tech Stack

- Frontend: React + TypeScript + Tailwind CSS + Recharts
- Backend: FastAPI + SQLAlchemy + Alembic + Pydantic
- Database: PostgreSQL
- Reverse proxy: NGINX
- Containerization: Docker + Docker Compose
- Auth: JWT
- AI: Python + scikit-learn + pandas + numpy
- Testing: Pytest + Playwright

Do not introduce incompatible replacement stacks unless the user explicitly asks for a change.

## Engineering Rules

- Create modular folders and keep files reasonably sized.
- Add tests for important backend logic.
- Add Playwright tests for critical UI flows.
- Add seed scripts only when they support local development and tests.
- Document env vars whenever they are added or changed.
- Prefer maintainable, production-appropriate implementations over mock-heavy shortcuts.

## Definition Of Done For Every Step

- Code builds.
- Lint and tests for changed areas pass.
- Docs are updated.
- Env vars are documented.
- No placeholder code is left behind.

## Implementation Guidance

- Keep integrations with Wazuh and Suricata inside backend service boundaries.
- Normalize incoming data into a common internal alert schema before incident creation or scoring.
- Preserve raw upstream payloads alongside normalized data for auditability and debugging.
- Keep automation and response capabilities basic, explainable, and appropriate for SMEs.
- Maintain clear history for audit events, incident changes, and response actions.
- Favor clear module boundaries across ingestion, normalization, scoring, incidents, response, audit, and UI layers.
