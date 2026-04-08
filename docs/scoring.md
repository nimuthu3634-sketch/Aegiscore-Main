# Risk Scoring

## Purpose

Within the **final scoped v1** product boundary (four supported detections only; SME/lab, single-tenant), AegisCore risk scoring is a prioritization layer that runs after those detections are created.
It does not replace the detector. The scoring runtime converts normalized alert context into a
0-100 risk score, a priority label, and an explanation payload that the API exposes to the
dashboard, list pages, and detail views.

## Runtime Responsibilities

### Deterministic baseline

The backend baseline engine is the production-safe default.

- Location: `apps/api/app/services/scoring/baseline.py`
- Method id: `baseline_rules`
- Version source: `SCORING_BASELINE_VERSION`
- Output: score, confidence, priority label, explanation, feature snapshot

The baseline uses explainable additive rules over approved SME SOC context:

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

### Trainable scikit-learn model

The trainable model is optional and can be enabled by setting `SCORING_STRATEGY=model`.

- Runtime loader: `apps/api/app/services/scoring/ml.py`
- Training script: `ai/training/train_risk_model.py`
- Inference utility: `ai/inference/predict_risk.py`
- Default model path: `/srv/ai/models/aegiscore-risk-priority-model.joblib`
- Default metadata path: `/srv/ai/models/aegiscore-risk-priority-model.metadata.json`

If the runtime is configured for model scoring but no model artifact is available, AegisCore
falls back to the deterministic baseline and records the fallback reason in the explanation
payload. That keeps scoring safe and available during local development.

## Priority Labels

- `low`
- `medium`
- `high`
- `critical`

Thresholds are applied over the normalized 0-100 score:

- `0-44`: low
- `45-69`: medium
- `70-84`: high
- `85-100`: critical

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

This keeps the current score auditable without adding heavy multi-version scoring history.

## Incident Rollup

Incident priority remains persisted on the incident record, but it is refreshed from linked-alert
scores when alerts are linked or rescored. The rollup uses the highest linked score, the average
linked score, and a small correlation bonus for multi-alert incidents.

## Training

Run a local training pass from the repo root:

```powershell
docker compose run --rm --no-deps api python /srv/ai/training/train_risk_model.py
```

The default training dataset is:

- `ai/datasets/risk_training_fixture.csv`

The generated artifacts land in:

- `ai/models/aegiscore-risk-priority-model.joblib`
- `ai/models/aegiscore-risk-priority-model.metadata.json`

## Manual Model Inference

Prepare a JSON feature payload shaped like the persisted `feature_snapshot` and run:

```powershell
docker compose run --rm --no-deps api python /srv/ai/inference/predict_risk.py --features-file /srv/ai/datasets/sample_features.json
```

## API Exposure

Real risk scoring data now flows through:

- `GET /alerts`
- `GET /alerts/{id}`
- `GET /incidents`
- `GET /incidents/{id}`
- `GET /dashboard/summary`

The alert list/detail responses expose persisted risk score metadata, while incident detail uses
linked-alert rollup context in the priority explanation.
