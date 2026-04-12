# Risk Scoring

**Final product context:** Risk scoring is a component of the **AegisCore** SOC platform MVP (see **[final-product.md](final-product.md)**).

**AI scope:** Machine learning performs **alert prioritization** after detections exist — not raw detection. Canonical end-to-end description: **[ai-alert-prioritization.md](ai-alert-prioritization.md)** (dataset, train, inference, API wiring, brute-force automation).

## Purpose

Within the **MVP** boundary (four validated `DetectionType` values in [final-product.md](final-product.md); single-tenant deployment), AegisCore risk scoring is a **prioritization layer** that runs after alerts are normalized.

**Dependency note:** `tensorflow-cpu` constrains **NumPy** to a range below 2.2; the API package pins NumPy/Pandas so installs resolve cleanly (including Windows).

The scoring runtime produces a **0–100** style numeric score, a **priority label**, confidence, and an **explanation** payload for list/detail/dashboard views. It does **not** replace Wazuh/Suricata detectors.

## `SCORING_STRATEGY` default: baseline vs model

- **Default (`SCORING_STRATEGY=baseline`, including Docker Compose):** deterministic rules only. Works **without** TensorFlow artifacts; appropriate for **safe** local stacks, CI, and demos that focus on ingestion/incidents without ML. Baseline may still label **`critical`** from high numeric scores (see thresholds below).
- **TensorFlow path (`SCORING_STRATEGY=model`):** loads **`SCORING_MODEL_PATH`** (`.keras`) and **`SCORING_MODEL_METADATA_PATH`**. The **`alert_prioritization_v1`** head outputs **Low / Medium / High** only — **never Critical** from ML. Use this for the **final ML demo** when Keras files are present under `ai/models/`.
- **Fallback:** if `model` is set but artifacts are missing or invalid, scoring **falls back to baseline** and records **`fallback_reason`** in the explanation.

Full narrative: **[ai-alert-prioritization.md](ai-alert-prioritization.md)**.

## Runtime Responsibilities

### Deterministic baseline

The baseline engine is the **Compose / repository default** and remains the **production-safe** path when ML artifacts are absent.

- Location: `apps/api/app/services/scoring/baseline.py`
- Method id: `baseline_rules`
- Version source: `SCORING_BASELINE_VERSION`
- Output: score, confidence, priority label, explanation, feature snapshot

The baseline uses explainable additive rules over normalized context:

- source type
- detection type
- source severity and rule level
- repeated event count
- short-window density
- asset criticality
- privileged account context
- sensitive file context
- repeated source IP observations
- repeated failed login volume
- recurrence history
- destination port context

Baseline scores map through **numeric thresholds** (see below) and may label an alert **`critical`** when the score is high enough.

### Trainable TensorFlow (Keras) model (primary AI path)

Optional; enable with `SCORING_STRATEGY=model`. **Committed product artifacts are `.keras` + `.metadata.json` only** — not joblib or scikit-learn.

- Runtime loader + training helpers: `apps/api/app/services/scoring/ml.py`, `alert_prioritization.py`
- Training entrypoint: `ai/training/train_risk_model.py`
- Inference CLI: `ai/inference/predict_risk.py`
- Default model path: `/srv/ai/models/aegiscore-risk-priority-model.keras`
- Default metadata path: `/srv/ai/models/aegiscore-risk-priority-model.metadata.json`

The **primary** trainable schema is **`alert_prioritization_v1`**: softmax classes **`low` / `medium` / `high`** only (no “critical” class). Outputs map to **`LOW` / `MEDIUM` / `HIGH`** incident priorities.

If `SCORING_STRATEGY=model` but artifacts are missing or invalid, the API **falls back to the baseline** and records **`fallback_reason`** in the explanation.

### Historical DB string: `sklearn_model` (not a runtime stack)

The value **`sklearn_model`** exists only as a **historical `ScoreMethod` enum / DB string** on migrated rows. The product stack uses **TensorFlow** for trainable scoring; **no `.joblib` artifacts** and **no scikit-learn inference path** are shipped. New scores are stored as **`tensorflow_model`** or **`baseline_rules`**.

## Priority labels

### From the deterministic baseline

Baseline maps **rounded 0–100 score** to incident priority:

| Score range | Priority |
|-------------|----------|
| 0–44 | `low` |
| 45–69 | `medium` |
| 70–84 | `high` |
| 85–100 | `critical` |

### From the TensorFlow alert prioritization model (`alert_prioritization_v1`)

The model emits **three** classes only. Mapping never produces **`critical`** from ML:

| Model class | Incident priority |
|-------------|-------------------|
| `low` | `low` |
| `medium` | `medium` |
| `high` | `high` |

## Persistence

Scores are stored in `risk_scores` with:

- `score`
- `confidence`
- `priority_label`
- `scoring_method`
- `baseline_version`
- `model_version`
- `reasoning`
- `explanation`
- `feature_snapshot`
- `calculated_at`

## Incident rollup

Incident priority on the incident record is refreshed from linked-alert scores when alerts are linked or rescored. Rollup uses max/avg linked scores plus a small multi-alert bonus (see `apps/api/app/services/scoring/rollup.py`).

## Training and inference (quick links)

Full commands and environment variables: **[ai-alert-prioritization.md](ai-alert-prioritization.md)** and **[ai/README.md](../ai/README.md)**.

Training (Docker):

```powershell
docker compose run --rm --no-deps api python /srv/ai/training/train_risk_model.py
```

Default outputs:

- `ai/models/aegiscore-risk-priority-model.keras`
- `ai/models/aegiscore-risk-priority-model.metadata.json`

Optional evaluation outputs when training the alert dataset: set **`AI_EVAL_OUTPUT_DIR`**.

### Legacy fixture schema (tests / lab only)

To train the **small** `risk_training_fixture.csv` (metadata `legacy_risk_fixture`, older `MODEL_*` column layout used only for regression tests), set:

`AI_DATASET_PATH=/srv/ai/datasets/risk_training_fixture.csv`

That path is **not** the product’s primary scoring story; keep it internal to engineering unless you explicitly label it legacy in a viva.

## Manual model inference

- **`alert_prioritization_v1`**: JSON may use CSV-style fields (`threat_type`, `timestamp`, …) or API-style snapshots; the CLI maps into the training schema.
- **`legacy_risk_fixture`**: JSON shaped like persisted **`feature_snapshot`** rows (see `sample_features.json`).

Examples:

```powershell
docker compose run --rm --no-deps api python /srv/ai/inference/predict_risk.py --features-file /srv/ai/datasets/sample_features.json
docker compose run --rm --no-deps api python /srv/ai/inference/predict_risk.py --features-file /srv/ai/datasets/sample_alert_row.json
```

## API exposure

Risk scoring surfaces through:

- `GET /alerts`
- `GET /alerts/{id}`
- `GET /incidents`
- `GET /incidents/{id}`
- `GET /dashboard/summary`

Alert list/detail return persisted risk score metadata; incident detail includes rollup context in the priority explanation.
