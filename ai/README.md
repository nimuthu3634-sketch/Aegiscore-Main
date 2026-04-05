# AegisCore AI

The AI workspace supports AegisCore risk prioritization, not raw detection.

## Layout

- `datasets`: fixture and future training datasets
- `models`: locally generated scikit-learn artifacts
- `training/train_risk_model.py`: baseline training entrypoint
- `inference/predict_risk.py`: utility to score a JSON feature payload with a trained model

## Runtime split

- Production scoring runtime: `apps/api/app/services/scoring`
- Training and manual inference utilities: `ai/...`

## Local training

```powershell
docker compose run --rm --no-deps api python /srv/ai/training/train_risk_model.py
```

The trained artifact and metadata are written into `ai/models`.
