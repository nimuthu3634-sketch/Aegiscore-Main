# AegisCore AI

The AI workspace supports **risk prioritization** (post-detection scoring), not raw threat detection. The trainable path uses **TensorFlow / Keras**; see `docs/scoring.md` for runtime behavior and env vars.

## Synthetic alert prioritization dataset (academic prototype)

`ai/datasets/alerts_dataset.csv` is a **synthetic, structured** CSV used to prototype **AI alert prioritization** (labels `Low` / `Medium` / `High`). It is **not** production telemetry; it exists for reproducible experiments and teaching-style model training. Regenerate it anytime (same columns, fixed default seed) with:

```powershell
py -3 ai/datasets/generate_alerts_dataset.py
```

Optional: `--rows 2000 --seed 99 --output path/to/out.csv`. The generator lives at `ai/datasets/generate_alerts_dataset.py`. For runtime detections, the product maps integrity events to `file_integrity_violation`; this CSV uses `file_integrity` as the `threat_type` value for that class so the training file stays aligned with the prioritization spec.

## Layout

- `datasets`: fixture and future training datasets
- `models`: locally generated TensorFlow Keras **`.keras`** weights plus **`*.metadata.json`** (preprocessing + label map)
- `training/train_risk_model.py`: training entrypoint (calls shared logic in `apps/api/.../scoring/ml.py`)
- `inference/predict_risk.py`: CLI to score a JSON feature snapshot with a trained model

## Runtime split

- Production scoring runtime: `apps/api/app/services/scoring`
- Training and manual inference utilities: `ai/...`

## Train the model (Docker)

From repo root:

```powershell
docker compose run --rm --no-deps api python /srv/ai/training/train_risk_model.py
```

Outputs default to `ai/models/aegiscore-risk-priority-model.keras` and `ai/models/aegiscore-risk-priority-model.metadata.json`. Overrides: `AI_MODEL_PATH`, `AI_MODEL_METADATA_PATH`, `AI_DATASET_PATH` (defaults to `alerts_dataset.csv`), `AI_MODEL_VERSION`. Training the alert dataset also writes evaluation files under `ai/outputs/alert_prioritization/` unless `AI_EVAL_OUTPUT_DIR` is set.

## Test scoring (API unit test)

With API dev dependencies installed:

```powershell
cd apps/api
python -m pytest tests/test_scoring_ml.py -q
```

In Docker, override the API entrypoint (otherwise the container waits for Postgres and never runs pytest):

```powershell
docker compose run --rm --no-deps --entrypoint python api -m pytest tests/test_scoring_ml.py -q
```

## Manual inference (CLI)

After training, with defaults or `AI_MODEL_PATH` / `AI_MODEL_METADATA_PATH` set:

```powershell
docker compose run --rm --no-deps api python /srv/ai/inference/predict_risk.py --features-file /srv/ai/datasets/sample_features.json
docker compose run --rm --no-deps api python /srv/ai/inference/predict_risk.py --features-file /srv/ai/datasets/sample_alert_row.json
```

With `alert_prioritization_v1` metadata, the CLI prints `predicted_label`, `confidence`, and per-class `probabilities`. API-shaped JSON (`detection_type`, …) is accepted and mapped automatically.

## Enable model mode in the API

Set `SCORING_STRATEGY=model` and point `SCORING_MODEL_PATH` / `SCORING_MODEL_METADATA_PATH` at the `.keras` file and paired JSON. If artifacts are missing or invalid, the API **falls back to the deterministic baseline** (see `apps/api/app/services/scoring/service.py`).
