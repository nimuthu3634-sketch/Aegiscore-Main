# AegisCore AI

The AI workspace supports **risk prioritization** (post-detection scoring), not raw threat detection. The trainable path uses **TensorFlow / Keras**; see `docs/scoring.md` for runtime behavior and env vars.

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

Outputs default to `ai/models/aegiscore-risk-priority-model.keras` and `ai/models/aegiscore-risk-priority-model.metadata.json` (override with `AI_MODEL_PATH`, `AI_MODEL_METADATA_PATH`, `AI_DATASET_PATH`, `AI_MODEL_VERSION`).

## Test scoring (API unit test)

With API dev dependencies installed:

```powershell
cd apps/api
python -m pytest tests/test_scoring_ml.py -q
```

## Manual inference (CLI)

After training, with defaults or `AI_MODEL_PATH` / `AI_MODEL_METADATA_PATH` set:

```powershell
docker compose run --rm --no-deps api python /srv/ai/inference/predict_risk.py --features-file /srv/ai/datasets/sample_features.json
```

## Enable model mode in the API

Set `SCORING_STRATEGY=model` and point `SCORING_MODEL_PATH` / `SCORING_MODEL_METADATA_PATH` at the `.keras` file and paired JSON. If artifacts are missing or invalid, the API **falls back to the deterministic baseline** (see `apps/api/app/services/scoring/service.py`).
