# AI / ML — Alert prioritization

This document is the **canonical reference** for how AegisCore uses machine learning: **post-detection alert prioritization only**. The model does **not** perform raw threat detection; Wazuh/Suricata ingestion and normalization establish `detection_type` and context, then scoring ranks urgency for analysts.

## Final design (what to present)

| Topic | Behavior |
|--------|----------|
| **Role of AI** | Ranks alerts (0–100 style score + tier) after detections exist; explains outputs for the dashboard. |
| **Trainable head** | TensorFlow / Keras MLP on `alert_prioritization_v1` features derived from normalized alerts + synthetic CSV rows. |
| **Supported threat families (training CSV `threat_type`)** | `normal` (benign-style baseline traffic), `brute_force`, `port_scan`, `file_integrity`, `unauthorized_user_creation`. |
| **API `DetectionType` (product)** | `brute_force`, `port_scan`, `file_integrity_violation`, `unauthorized_user_creation` — maps to features the model sees (e.g. integrity → `file_integrity` in the training row builder). |
| **Training labels (CSV `label`)** | `Low`, `Medium`, `High` (display casing in the committed dataset). |
| **Model softmax** | Classes `low`, `medium`, `high` — **no “critical” class**. |
| **Incident priority from model** | Mapped to `LOW` / `MEDIUM` / `HIGH` only; the trainable path **never** assigns `CRITICAL` from ML. |
| **Deterministic baseline** | Separate rules engine; can still yield `critical` from numeric score thresholds (85+). |
| **Automated response (ML)** | Built-in **IP block** automation applies **only** to `brute_force` when TensorFlow scoring + strict gates pass; other detection types are never auto-blocked by this rule. |

## Repository layout

- **`ai/datasets/`** — `alerts_dataset.csv` (committed synthetic set), `generate_alerts_dataset.py`, optional small JSON samples for CLI inference.
- **`ai/training/train_risk_model.py`** — Training entrypoint (delegates to `apps/api/app/services/scoring/ml.py`).
- **`ai/inference/predict_risk.py`** — Offline scoring from a JSON feature file.
- **`apps/api/app/services/scoring/`** — Runtime baseline, feature extraction, TensorFlow load/score, service orchestration.
- **`ai/models/`** — Default output paths for `.keras` weights and `.metadata.json` (gitignored generated files; see `ai/models/README.md`).

## 1. Generate the dataset

From repo root (stdlib only; fixed seed by default):

```powershell
py -3 ai/datasets/generate_alerts_dataset.py
```

Options: `--rows 1240 --seed 42 --output path/to/alerts_dataset.csv`

The committed **`ai/datasets/alerts_dataset.csv`** is the reference training file for submissions; regenerate when you need a fresh draw with the same schema.

## 2. Train the model

**Docker (recommended):**

```powershell
docker compose run --rm --no-deps api python /srv/ai/training/train_risk_model.py
```

**Local** (with API dev dependencies + TensorFlow installed, from `apps/api` or with `PYTHONPATH` set):

```powershell
cd apps/api
py -3 ../../ai/training/train_risk_model.py
```

Artifacts (defaults):

- `ai/models/aegiscore-risk-priority-model.keras`
- `ai/models/aegiscore-risk-priority-model.metadata.json`

Environment variables (see also `ai/.env.example` and [environment.md](environment.md)):

- `AI_DATASET_PATH` — CSV path (default: alert prioritization dataset).
- `AI_MODEL_PATH`, `AI_MODEL_METADATA_PATH`, `AI_MODEL_VERSION` — outputs and version label.
- `AI_EVAL_OUTPUT_DIR` — optional evaluation artifacts (confusion matrix, classification report) for `alert_prioritization_v1` training.

### Legacy training fixture (optional)

A small second schema (`risk_training_fixture.csv`, metadata `legacy_risk_fixture`) exists **only** for regression tests and backward-compatible TensorFlow experiments. It is **not** the product scoring path. Do not use it for final demos unless you intentionally document it as a lab curiosity.

## 3. Run inference (CLI)

After training:

```powershell
docker compose run --rm --no-deps api python /srv/ai/inference/predict_risk.py --features-file /srv/ai/datasets/sample_features.json
docker compose run --rm --no-deps api python /srv/ai/inference/predict_risk.py --features-file /srv/ai/datasets/sample_alert_row.json
```

For `alert_prioritization_v1`, the CLI prints **`predicted_label`** (`low` / `medium` / `high`), **`confidence`**, and per-class **`probabilities`**.

## 4. Backend scoring with the model

1. Build or copy `.keras` + `.metadata.json` into paths visible to the API container (defaults under `/srv/ai/models/...` in Compose).
2. Set:

   - `SCORING_STRATEGY=model`
   - `SCORING_MODEL_PATH` — path to `.keras`
   - `SCORING_MODEL_METADATA_PATH` — path to paired JSON

3. If artifacts are missing or invalid, **`score_alert`** falls back to the deterministic baseline and sets **`fallback_reason`** in the explanation — scoring never hard-fails.

Code: `apps/api/app/services/scoring/service.py` (orchestration), `ml.py` + `alert_prioritization.py` (train/load/score).

## 5. Brute-force ML auto-block (optional)

Separate from user-defined policies: when **`AUTOMATED_RESPONSE_ML_BRUTE_FORCE_ENABLED=true`**, the backend may enqueue a built-in **`block_ip`** only if **all** hold:

- `detection_type == brute_force`
- Risk score produced with **`tensorflow_model`**
- Incident-style priority is **High** and model tier / explanation indicates **high**
- Feature snapshot shows **`failed_logins_5m` ≥ 10**
- A **source IP** is resolvable
- No duplicate policy already blocking the same IP for that alert

Implementation: `apps/api/app/services/response_automation/ml_brute_force_automation.py` and `execution.py`. Other detection types with High ML tier **do not** trigger this path.

## Historical note: `sklearn_model`

The enum value **`sklearn_model`** may still appear on **old migrated database rows**. The shipped product **never** used scikit-learn for runtime scoring; current trainable scoring is **TensorFlow only**. New scores persist as **`tensorflow_model`** or **`baseline_rules`**.

---

## Final AI/ML architecture summary (viva / one-pager)

**Ingestion** produces normalized alerts with `detection_type` and payloads. **Feature extraction** turns each alert into `AlertRiskFeatures` (telemetry + recurrence + asset context). **Scoring strategy**: either **deterministic baseline** (additive rules → 0–100 → low/medium/high/**critical**) or **TensorFlow alert prioritization** (`alert_prioritization_v1`: 3-class softmax **low/medium/high** → mapped to incident priorities **without critical**). Scores persist to **`risk_scores`** with explanation JSON (including `class_probabilities` for TF). **Automated response**: user policies apply by detection and threshold; **additionally**, an optional **ML-only brute-force IP block** runs under tight gates. **Training/inference utilities** live under `ai/`; **runtime scoring** lives in `apps/api` so the web app never talks to Wazuh/Suricata or model files directly beyond what the API exposes.
