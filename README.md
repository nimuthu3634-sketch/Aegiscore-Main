# AegisCore SOC Platform

**AegisCore** is a centralized Security Operations Centre (SOC) platform — a single-tenant web system built with React + TypeScript, FastAPI, PostgreSQL, and TensorFlow/Keras for AI-powered alert prioritization.

The platform delivers security monitoring (Wazuh and Suricata), alert handling, incident investigation workflows, explainable risk scoring, reporting and export, and policy-driven automated response with full audit trails.

**Supported detection types:**

- `brute_force`
- `port_scan`
- `file_integrity_violation`
- `unauthorized_user_creation`

---

## Quick Start

### 1. Create the root `.env` file

Create a `.env` file in the repo root (this file is intentionally excluded from Git):

```env
SCORING_STRATEGY=model
AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true
NOTIFICATIONS_ENABLED=true
```

### 2. Start the stack

```bash
docker compose up --build -d
```

### 3. Run migrations and seed data

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
```

### 4. Open the platform

| URL | Description |
| --- | --- |
| `http://localhost:5173` | Frontend dashboard (direct) |
| `http://localhost` | Frontend via NGINX |
| `http://localhost:8000/health` | API health check |
| `http://localhost/api/health` | API health via NGINX |

**Default credentials:**

- `admin / AegisCore123!`
- `analyst / AegisCore123!`

---

## AI / ML — Alert Prioritization

The TensorFlow model ranks already-detected alerts as Low / Medium / High / Critical. It does not replace Wazuh or Suricata — it prioritizes what they detect.

**Model details:**

- Architecture: 4-layer MLP with BatchNormalization (Dense 256→128→64→32)
- Training dataset: 10,000 rows, 4 classes, 5 threat types
- Test accuracy: 98.6%

**Quick commands:**

```bash
# Generate training dataset
py -3.12 ai/datasets/generate_alerts_dataset.py

# Train the model
py -3.12 ai/training/train_risk_model.py

# Run attack simulations (API must be running)
py -3.12 scripts/validate_attack_scenarios.py
```

To use the AI model, set `SCORING_STRATEGY=model` in the root `.env`. Default is `baseline` (no Keras required).

**Built-in brute-force auto-block:** fires only when all gates pass — TensorFlow-scored brute_force alert, High AI tier, `failed_logins_5m ≥ 10`, and source IP present.

---

## Validation

```bash
# AI/ML readiness check
py -3.12 scripts/validate_ai_ml_readiness.py

# Backend tests
docker compose run --rm --entrypoint pytest api

# Frontend lint and build
npm run lint:web
npm run build:web

# Four-scenario attack simulation
py -3.12 scripts/validate_attack_scenarios.py
```

---

## Automated Response Policies

Four response policies are configured for the supported detection types:

| Detection | Action | Threshold |
| --- | --- | --- |
| `brute_force` | `block_ip` | 85 |
| `file_integrity_violation` | `create_manual_review` | 80 |
| `unauthorized_user_creation` | `notify_admin` | 90 |
| `port_scan` | `notify_admin` | 75 |

Policies can be enabled or disabled from the **Rules** page (admin session required).

---

## Repository Structure

```text
apps/web        React + TypeScript + Tailwind SOC console
apps/api        FastAPI + SQLAlchemy + Alembic backend
apps/worker     Worker shell for background execution
ai/             Training scripts, datasets, and model artifacts
infra/nginx     Local reverse proxy configuration
infra/docker    Dockerfiles for the local stack
scripts/        Validation and helper scripts
docs/           Architecture, setup, and release guides
```

---

## API Endpoints

**Ingestion (admin only):**

- `POST /integrations/wazuh/events`
- `POST /integrations/suricata/events`

**Alert workflow:**

- `POST /alerts/{id}/acknowledge`
- `POST /alerts/{id}/close`
- `POST /alerts/{id}/link-incident`
- `POST /alerts/{id}/notes`

**Incident workflow:**

- `POST /incidents/{id}/transition`
- `POST /incidents/{id}/notes`

**Policies and responses:**

- `GET /policies`
- `PATCH /policies/{id}` (admin only)
- `GET /responses`

**Reports:**

- `GET /reports/daily-summary`
- `GET /reports/weekly-summary`
- `GET /reports/alerts/export`
- `GET /reports/incidents/export`
- `GET /reports/responses/export`

**Health:**

- `GET /health`
- `GET /health/live`
- `GET /health/ready`

---

## User Roles

| Role | Access |
| --- | --- |
| `admin` | Full access including policy management and manual ingestion |
| `analyst` | Investigation, reporting, alerts, incidents, responses, assets, dashboard |

---

## Safety Notes

- Automated response is policy-driven and limited to the four supported detection types
- Destructive live actions remain blocked unless `AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=true`
- The platform is single-tenant and optimized for SOC operations

---

## Documentation

- [Architecture](docs/architecture.md)
- [AI / ML — Alert Prioritization](docs/ai-alert-prioritization.md)
- [Scoring](docs/scoring.md)
- [Operator Guide](docs/setup/operator-guide.md)
- [Analyst Guide](docs/setup/analyst-guide.md)
- [Operator Runbook](docs/setup/operator-runbook.md)
- [Ubuntu VM Lab Setup](docs/setup/ubuntu-vm-lab-live-soc.md)
- [Wazuh Integration](docs/setup/wazuh-live-integration.md)
- [Suricata Integration](docs/setup/suricata-live-integration.md)
- [Notifications Setup](docs/setup/notifications.md)
- [End-to-End Validation](docs/testing/end-to-end-validation.md)
- [Requirement Compliance Matrix](docs/requirement-compliance-matrix.md)
- [Release Readiness](docs/release-readiness.md)

---

## Academic Supervision

This project was guided and supervised by Ann Roshanie Appuhamy as part of undergraduate coursework.
