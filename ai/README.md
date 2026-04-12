# AegisCore AI

Utilities for **TensorFlow / Keras alert prioritization** (post-detection scoring): the **primary** trainable artifact is **`ai/models/aegiscore-risk-priority-model.keras`** with paired **`.metadata.json`** (3-class **low / medium / high**). There is **no** scikit-learn or joblib scoring path. **Canonical documentation:** [docs/ai-alert-prioritization.md](../docs/ai-alert-prioritization.md) — product role, threat taxonomy, labels, backend wiring, and brute-force ML automation.

## Synthetic dataset (`alert_prioritization_v1`)

`ai/datasets/alerts_dataset.csv` is a **synthetic** CSV for reproducible training. Labels are **`Low` / `Medium` / `High`**. Rows include **`normal`** (non-attack baseline) plus **`brute_force`**, **`port_scan`**, **`file_integrity`**, and **`unauthorized_user_creation`** in the `threat_type` column (aligned with the prioritization feature spec; the live API uses `file_integrity_violation` as the `DetectionType` enum).

Regenerate from repo root:

```powershell
py -3 ai/datasets/generate_alerts_dataset.py
```

Options: `--rows 2000 --seed 99 --output path/to/out.csv` · Script: `ai/datasets/generate_alerts_dataset.py`

## Layout

- `datasets/` — training CSVs and small JSON samples for the inference CLI
- `models/` — generated `.keras` + `.metadata.json` (see `ai/models/README.md`)
- `training/train_risk_model.py` — training entrypoint (shared logic in `apps/api/app/services/scoring/ml.py`)
- `inference/predict_risk.py` — score a JSON snapshot from the command line

## Runtime split

- **Production scoring:** `apps/api/app/services/scoring/`
- **This folder:** offline train/inference and datasets

## Train (Docker)

```powershell
docker compose run --rm --no-deps api python /srv/ai/training/train_risk_model.py
```

Defaults: `ai/models/aegiscore-risk-priority-model.keras` and `...metadata.json`. Overrides: `AI_DATASET_PATH`, `AI_MODEL_PATH`, `AI_MODEL_METADATA_PATH`, `AI_MODEL_VERSION`, optional `AI_EVAL_OUTPUT_DIR`.

## Unit test (TensorFlow path)

```powershell
cd apps/api
python -m pytest tests/test_scoring_ml.py -q
```

Docker (override entrypoint so pytest runs without waiting for Postgres):

```powershell
docker compose run --rm --no-deps --entrypoint python api -m pytest tests/test_scoring_ml.py -q
```

## Manual inference (CLI)

```powershell
docker compose run --rm --no-deps api python /srv/ai/inference/predict_risk.py --features-file /srv/ai/datasets/sample_features.json
docker compose run --rm --no-deps api python /srv/ai/inference/predict_risk.py --features-file /srv/ai/datasets/sample_alert_row.json
```

With `alert_prioritization_v1` metadata, output includes `predicted_label`, `confidence`, and per-class `probabilities`.

## Enable model mode in the API

Set `SCORING_STRATEGY=model` and `SCORING_MODEL_PATH` / `SCORING_MODEL_METADATA_PATH` to the `.keras` file and paired JSON. Missing artifacts → **baseline fallback** with `fallback_reason` in the explanation (`apps/api/app/services/scoring/service.py`).

## Legacy fixture (engineering only)

`risk_training_fixture.csv` + metadata schema **`legacy_risk_fixture`** remain for **tests and optional lab retrains** of an older small TensorFlow feature layout. They are **not** the primary product narrative; see [docs/ai-alert-prioritization.md](../docs/ai-alert-prioritization.md).
