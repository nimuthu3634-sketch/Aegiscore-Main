# AegisCore alert prioritization artifacts

This directory stores locally trained **TensorFlow (Keras)** `.keras` weights plus paired **JSON metadata** for **alert prioritization** (see [docs/ai-alert-prioritization.md](../../docs/ai-alert-prioritization.md)). **No joblib or sklearn artifacts** are used.

Expected files:

- `aegiscore-risk-priority-model.keras`
- `aegiscore-risk-priority-model.metadata.json`

Retrain with `ai/training/train_risk_model.py` if metadata is missing fields required by the current API loader (for example `feature_column_names`, `numeric_means`, `numeric_stds`). Alert-dataset training sets `training_schema` to `alert_prioritization_v1` and also persists `categorical_allowed_values` for one-hot alignment at inference.

Artifacts are intentionally local-development friendly and should be recreated through the
training script instead of edited by hand.
