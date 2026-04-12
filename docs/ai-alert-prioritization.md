# AI / ML — Alert prioritization

This document is the **canonical reference** for how AegisCore uses machine learning: **post-detection alert prioritization only**. **Wazuh and Suricata establish what happened** (normalized `detection_type` and context). **The TensorFlow model does not detect threats**; it **ranks** already-ingested alerts for analysts as **Low**, **Medium**, or **High** urgency.

## End-to-end pipeline (final design)

1. **Detection (connectors + normalization)** — In-scope threats are classified in the API as **`brute_force`**, **`port_scan`**, **`file_integrity_violation`**, and **`unauthorized_user_creation`** (see naming note below). Ingestion may also carry **benign-style** context used in training as **`normal`** rows in the synthetic CSV (not a product `detection_type`).
2. **AI prioritization (optional TensorFlow path)** — When `SCORING_STRATEGY=model` and Keras artifacts are valid, the model outputs **only** **Low / Medium / High** (softmax + mapped incident priority). **It never outputs Critical** as an ML class.
3. **Deterministic baseline (default)** — When `SCORING_STRATEGY=baseline`, or when the model path is missing/invalid, scoring uses additive rules and may still assign **Critical** from **numeric score thresholds** (that is baseline behavior, not the ML head).
4. **Built-in automated block (this project)** — Only **`brute_force`** can trigger the **ML-gated** auto **`block_ip`** rule, and only when **all** preconditions in [§5](#5-brute-force-ml-auto-block-optional) hold. Other detection types are **never** auto-blocked by this built-in rule (user policies are separate).

## Supported threat naming (use consistently in writeups)

| Concept | Values |
|--------|--------|
| **Product API `detection_type` (four in-scope threats)** | `brute_force`, `port_scan`, `file_integrity_violation`, `unauthorized_user_creation` |
| **Training CSV `threat_type` (same four + benign context)** | `brute_force`, `port_scan`, **`file_integrity`** (maps from API `file_integrity_violation`), `unauthorized_user_creation`, plus **`normal`** for non-attack examples |

Use **API names** in runtime and integration docs; use **CSV names** when discussing `alerts_dataset.csv` / `generate_alerts_dataset.py`.

## Final design (what to present)

| Topic | Behavior |
|--------|----------|
| **Role of AI** | Ranks alerts (0–100 style score + tier) **after** detections exist; explains outputs for the dashboard. **Not** raw threat detection. |
| **Trainable head** | TensorFlow / Keras MLP on `alert_prioritization_v1` features derived from normalized alerts + synthetic CSV rows. |
| **Training data** | Committed **`alerts_dataset.csv`** includes **`normal`** activity plus the **four** supported attack families (see naming table above). |
| **Training labels (CSV `label`)** | `Low`, `Medium`, `High` (display casing in the committed dataset). |
| **Model softmax** | Classes `low`, `medium`, `high` — **no “critical” class**. |
| **Incident priority from model** | Mapped to `LOW` / `MEDIUM` / `HIGH` only; the trainable path **never** assigns `CRITICAL` from ML. |
| **Deterministic baseline** | Separate rules engine; **may** yield `critical` from numeric score thresholds (85+). Still available when `SCORING_STRATEGY=baseline` or as **fallback** if the model cannot load. |
| **Automated response (built-in ML rule)** | **Only** `brute_force`; see [§5](#5-brute-force-ml-auto-block-optional). |

### `SCORING_STRATEGY` default (baseline) vs TensorFlow demo

- **Repository / Compose default:** `SCORING_STRATEGY=baseline` — prioritization works **without** shipping or mounting Keras files; scores are explainable rules; suitable for **safe local runs** and many CI/evaluation flows.
- **Final project / viva demo with ML:** set **`SCORING_STRATEGY=model`**, ensure **`ai/models/aegiscore-risk-priority-model.keras`** and **`aegiscore-risk-priority-model.metadata.json`** are present in the API container (Compose bind-mounts `ai/` to `/srv/ai` by default), and keep **`SCORING_MODEL_PATH` / `SCORING_MODEL_METADATA_PATH`** pointing at those files. If the model is missing or metadata is wrong, the API **falls back to baseline** and records **`fallback_reason`** on the score — no hard failure.
- **ML brute-force auto-block:** requires scores produced with **`tensorflow_model`** (i.e. model mode succeeded). With baseline-only scoring, the built-in ML auto-block **will not** fire even if `AUTOMATED_RESPONSE_ML_BRUTE_FORCE_ENABLED=true`.

## Repository layout

- **`ai/datasets/`** — `alerts_dataset.csv` (committed synthetic set), `generate_alerts_dataset.py`, optional small JSON samples for CLI inference.
- **`ai/training/train_risk_model.py`** — Training entrypoint (delegates to `apps/api/app/services/scoring/ml.py`).
- **`ai/inference/predict_risk.py`** — Offline scoring from a JSON feature file.
- **`apps/api/app/services/scoring/`** — Runtime baseline, feature extraction, TensorFlow load/score, service orchestration.
- **`ai/models/`** — **Primary** trainable artifacts: TensorFlow `.keras` weights, paired `.metadata.json`, and optional evaluation companions (see `ai/models/README.md`). Runtime scoring loads **only** these Keras files — not joblib or scikit-learn models.

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

1. Ensure `.keras` + `.metadata.json` exist under **`ai/models/`** on the host (Compose maps **`./ai` → `/srv/ai`** in the reference stack, so defaults `/srv/ai/models/...` resolve without extra copies).
2. Set:

   - `SCORING_STRATEGY=model`
   - `SCORING_MODEL_PATH` — path to `.keras` (default: `/srv/ai/models/aegiscore-risk-priority-model.keras`)
   - `SCORING_MODEL_METADATA_PATH` — path to paired JSON (default: `/srv/ai/models/aegiscore-risk-priority-model.metadata.json`)

3. Restart the API so settings reload.

4. If artifacts are missing or invalid, **`score_alert`** falls back to the deterministic baseline and sets **`fallback_reason`** in the explanation — scoring never hard-fails.

**Compose example (host `.env` or shell export before `docker compose up`):**

```text
SCORING_STRATEGY=model
SCORING_MODEL_PATH=/srv/ai/models/aegiscore-risk-priority-model.keras
SCORING_MODEL_METADATA_PATH=/srv/ai/models/aegiscore-risk-priority-model.metadata.json
```

Code: `apps/api/app/services/scoring/service.py` (orchestration), `ml.py` + `alert_prioritization.py` (train/load/score).

## 5. Brute-force ML auto-block (optional)

**Scope:** In this project, the **built-in** ML-driven automated response is **only** the brute-force **IP block** path. User-defined policies may target other detections; this section is **only** the ML auto-block.

Separate from user-defined policies: when **`AUTOMATED_RESPONSE_ML_BRUTE_FORCE_ENABLED=true`** (API default allows the rule; it still must pass checks), the backend may enqueue a built-in **`block_ip`** only if **all** hold:

- **`detection_type == brute_force`**
- Risk score **`scoring_method == tensorflow_model`** (TensorFlow path was used for that score)
- **`priority_label == HIGH`** (AI-assigned incident priority is High)
- Model tier in the explanation is **`high`** (`model_priority_tier` / `predicted_class`, or aligned with priority when those keys are absent)
- Feature snapshot: **`failed_logins_5m` ≥ 10**
- **Source IP** present (from feature snapshot or alert-derived resolver)
- No duplicate block already recorded for that automation rule on the alert

Implementation: `apps/api/app/services/response_automation/ml_brute_force_automation.py` and `execution.py`. Other detection types **never** trigger this built-in rule.

## Submission readiness validation

**Quick proof (host, no Docker):** from repo root, run **`py -3 scripts/validate_ai_ml_readiness.py`**. Exit code **0** means: `alerts_dataset.csv` exists with required `threat_type` / `label` contract, **`aegiscore-risk-priority-model.keras`** and **`.metadata.json`** exist, and metadata matches **TensorFlow** / **`alert_prioritization_v1`** / **3-class** labels with **`training_rows` ≥ 200** (excludes stale tiny fixtures).

**Backend + gates:** `docker compose run --rm --no-deps --entrypoint pytest api tests/test_ai_ml_readiness.py -q` (loads Keras when TensorFlow is available; skips heavy tests on sparse hosts). Brute-force ML auto-block behavior: **`tests/test_response_automation.py`** (`-k ml_brute_force`). Baseline fallback when the model is missing: **`tests/test_scoring_integration_service.py`**.

## Historical note: `sklearn_model`

The enum value **`sklearn_model`** may still appear on **old migrated database rows**. The shipped product **never** used scikit-learn for runtime scoring; current trainable scoring is **TensorFlow only**. New scores persist as **`tensorflow_model`** or **`baseline_rules`**.

---

## Final AI/ML architecture summary (viva / one-pager)

**Detectors first:** Wazuh/Suricata ingestion and normalization set **`detection_type`** for the four in-scope threats (**`brute_force`**, **`port_scan`**, **`file_integrity_violation`**, **`unauthorized_user_creation`**). **Feature extraction** builds `AlertRiskFeatures`. **Scoring:** default **`SCORING_STRATEGY=baseline`** (deterministic rules → 0–100 → may include **Critical**); optional **`SCORING_STRATEGY=model`** loads **TensorFlow/Keras** **`alert_prioritization_v1`**, which outputs **only Low / Medium / High** — **never Critical** from ML. Scores persist to **`risk_scores`** with explanation JSON (`class_probabilities` when TF). **Built-in ML automation:** **only `brute_force`**, and only when the score was produced with **`tensorflow_model`**, **`failed_logins_5m` ≥ 10**, **AI High** tier, and **source IP** present (see §5). **Training/inference** utilities live under **`ai/`**; **runtime** scoring lives in **`apps/api`**.
