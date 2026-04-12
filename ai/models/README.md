# AegisCore alert prioritization artifacts

**Primary product path:** **TensorFlow / Keras** **3-class** alert prioritization (`low` / `medium` / `high` softmax), schema **`alert_prioritization_v1`**. This directory holds the **`.keras`** weight file and paired **`.metadata.json`** (see [docs/ai-alert-prioritization.md](../../docs/ai-alert-prioritization.md)).

**Do not** place `*.joblib` or other scikit-learn model dumps here — the API **only** loads `.keras` (or `.h5`) via `load_priority_model` in `apps/api/app/services/scoring/ml.py`.

Expected files:

- `aegiscore-risk-priority-model.keras`
- `aegiscore-risk-priority-model.metadata.json`
- `alert_prioritization_evaluation_metrics.json` (train/val/test accuracy, confusion matrix, class counts; mirrors the last training run)
- `alert_prioritization_confusion_matrix.csv`
- `alert_prioritization_classification_report.txt`

Retrain with `ai/training/train_risk_model.py` if metadata is missing fields required by the current API loader (for example `feature_column_names`, `numeric_means`, `numeric_stds`). Alert-dataset training sets `training_schema` to `alert_prioritization_v1` and also persists `categorical_allowed_values` for one-hot alignment at inference.

During training, metrics may also be written under `ai/outputs/` (gitignored). After a run, copy or regenerate the companion files above next to the `.keras` model if you need them committed.

## `legacy/` folder

See [legacy/README.md](legacy/README.md) for how non-primary or historical material is kept separate from the shipped TensorFlow artifact names.

Artifacts are intentionally local-development friendly and should be recreated through the
training script instead of edited by hand.
