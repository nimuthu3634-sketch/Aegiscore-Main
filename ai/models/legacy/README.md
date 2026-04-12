# Legacy model material (not runtime primary)

The API **only** loads trainable scoring from **`ai/models/aegiscore-risk-priority-model.keras`** plus **`aegiscore-risk-priority-model.metadata.json`** (TensorFlow/Keras, schema **`alert_prioritization_v1`**, **3-class** `low` / `medium` / `high`).

**Scikit-learn `joblib` dumps are not supported** and must not use the primary `aegiscore-risk-priority-model.*` basename. Older sklearn-era artifacts were removed from the repository; this folder exists so optional lab-only exports or notes can live **outside** the default loader paths without being mistaken for the product model.

For the small **`legacy_risk_fixture`** TensorFlow training CSV (`risk_training_fixture.csv`), see [docs/ai-alert-prioritization.md](../../../docs/ai-alert-prioritization.md) — that path is still **Keras**, not sklearn.
