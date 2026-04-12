# AegisCore — Final product definition

This document states the **final software deliverable** for the project in terms that align with the **original proposal requirements** and the **implemented repository**.

## Final product (proposal deliverable)

**AegisCore** is the **final application product** for this coursework: a **centralized Security Operations Center (SOC) platform MVP** delivered as a **single-tenant web system** (React + TypeScript console, FastAPI + SQLAlchemy + Alembic API, PostgreSQL, optional TensorFlow/Keras artifacts for trainable risk scoring, NGINX in reference deployment).

The product provides:

- **Monitoring and ingestion** — Wazuh (host/log) and Suricata (network) telemetry into a normalized alert model, with raw payload retention for auditability.
- **Alert handling** — triage, acknowledgement, closure, analyst notes, and linkage to incidents over authenticated APIs.
- **Incident workflows** — incident queue, state transitions, timelines, and investigation surfaces in the console.
- **Explainable AI-assisted alert prioritization** — deterministic baseline by default; optional **TensorFlow (Keras)** trainable ranker when artifacts and configuration are present (post-detection only), with persisted score metadata and explanations.
- **Reporting and export** — operational summaries and exports for alerts, incidents, and responses.
- **Controlled automated response** — policy-driven actions (including safe defaults and explicit gates for destructive paths), with auditable execution history.

The **academic release** is **intentionally limited** to **four validated threat detections** (enforced in ingestion and documentation):

1. `brute_force`
2. `port_scan`
3. `file_integrity_violation`
4. `unauthorized_user_creation`

**Standard description:** The current academic MVP validates four core threat categories: brute-force attacks, port scans, file integrity violations, and unauthorized user account creation. **Additional detection categories are future roadmap items**, not part of the current implementation.

No further detection types are claimed for this release. Items outside this catalog (for example ransomware-specific pipelines, phishing campaigns, or APT product lines) are **out of scope** for the submitted product.

## Relationship to the repository

The monorepo under this documentation root **is** the final product source: `apps/web` (console), `apps/api` (platform backend), `ai` (training and inference utilities aligned with API scoring), `infra` (reference deployment), and `docs` (architecture, compliance, and operational evidence).

For examiner and panel use, start from the [README](../README.md), then [architecture](architecture.md), [requirement-compliance-matrix](requirement-compliance-matrix.md), and [project-status-summary](project-status-summary.md).
