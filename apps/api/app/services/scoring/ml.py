"""TensorFlow (Keras) alert prioritization: ``alert_prioritization_v1`` (primary) or legacy fixture schema.

Threat / detection context comes from ingestion and :mod:`app.services.scoring.features`.
The **primary** trainable head (``alert_prioritization_v1``) uses a **3-class** softmax
(**low / medium / high** only — no critical class). A separate **LEGACY** TensorFlow path
supports ``risk_training_fixture.csv`` (``legacy_risk_fixture``) for regression tests;
it is not the product default. **There is no scikit-learn or joblib model path.**
"""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import tensorflow as tf

from app.models.enums import ScoreMethod
from app.services.scoring import alert_prioritization as ap  # enterprise v2 schema
from app.services.scoring.baseline import priority_from_score
from app.services.scoring.constants import (
    MODEL_CATEGORICAL_FEATURES,
    MODEL_FEATURE_COLUMNS,
    MODEL_NUMERIC_FEATURES,
    RISK_PRIORITY_ANCHORS,
)
from app.services.scoring.types import AlertRiskFeatures, ScoringResult

# LEGACY: second TensorFlow training schema (`risk_training_fixture.csv`, MODEL_* columns).
LEGACY_TRAINING_SCHEMA = "legacy_risk_fixture"


class ModelArtifactUnavailableError(RuntimeError):
    pass


def _set_deterministic_seed(seed: int = 42) -> None:
    tf.random.set_seed(seed)
    np.random.seed(seed)


def _normalize_training_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    """LEGACY: normalize rows for `risk_training_fixture.csv` (MODEL_* columns)."""
    frame = dataframe.copy()
    missing_columns = [column for column in MODEL_FEATURE_COLUMNS if column not in frame.columns]
    if missing_columns:
        raise ValueError(
            f"Training dataset is missing required columns: {', '.join(missing_columns)}"
        )

    for column in MODEL_NUMERIC_FEATURES:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)

    for column in MODEL_CATEGORICAL_FEATURES:
        frame[column] = frame[column].fillna("unknown").astype(str)

    if "priority_label" not in frame.columns:
        raise ValueError("Training dataset requires a priority_label column.")

    frame["priority_label"] = frame["priority_label"].astype(str)
    return frame


def _build_design_matrices(
    frame: pd.DataFrame,
    *,
    numeric_means: dict[str, float] | None = None,
    numeric_stds: dict[str, float] | None = None,
    feature_column_names: list[str] | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """LEGACY: one-hot MODEL_* categoricals + z-scored numerics."""
    cats = pd.get_dummies(
        frame[MODEL_CATEGORICAL_FEATURES].astype(str),
        prefix=MODEL_CATEGORICAL_FEATURES,
        prefix_sep="__",
    )
    numeric = frame[MODEL_NUMERIC_FEATURES].astype(float)
    if numeric_means is None or numeric_stds is None:
        means = numeric.mean()
        stds = numeric.std().replace(0, 1.0)
        numeric_means = {k: float(v) for k, v in means.items()}
        numeric_stds = {k: float(v) if float(v) != 0 else 1.0 for k, v in stds.items()}
    means_series = pd.Series(numeric_means)
    stds_series = pd.Series(numeric_stds)
    numeric_norm = (numeric - means_series) / stds_series.replace(0, 1.0)
    design = pd.concat([cats.reset_index(drop=True), numeric_norm.reset_index(drop=True)], axis=1)

    if feature_column_names is not None:
        design = design.reindex(columns=feature_column_names, fill_value=0.0)
    else:
        feature_column_names = list(design.columns)

    meta = {
        "feature_column_names": feature_column_names,
        "numeric_means": numeric_means,
        "numeric_stds": numeric_stds,
    }
    return design.values.astype(np.float32), meta


def _build_training_matrix(frame: pd.DataFrame) -> tuple[np.ndarray, dict[str, Any]]:
    return _build_design_matrices(frame, numeric_means=None, numeric_stds=None, feature_column_names=None)


def _frame_from_model_input(row: dict[str, Any]) -> pd.DataFrame:
    """LEGACY: single row for MODEL_* inference."""
    frame = pd.DataFrame([row])
    for column in MODEL_NUMERIC_FEATURES:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)
    for column in MODEL_CATEGORICAL_FEATURES:
        frame[column] = frame[column].fillna("unknown").astype(str)
    return frame


def _row_from_features(
    features: AlertRiskFeatures,
    preprocessing: dict[str, Any],
) -> np.ndarray:
    frame = _frame_from_model_input(features.to_model_input())
    x_matrix, _ = _build_design_matrices(
        frame,
        numeric_means=preprocessing["numeric_means"],
        numeric_stds=preprocessing["numeric_stds"],
        feature_column_names=preprocessing["feature_column_names"],
    )
    return x_matrix


def _build_keras_classifier(input_dim: int, num_classes: int) -> tf.keras.Model:
    """LEGACY fixture model: smaller MLP."""
    inputs = tf.keras.Input(shape=(input_dim,), name="risk_features")
    x = tf.keras.layers.Dense(64, activation="relu", name="dense_1")(inputs)
    x = tf.keras.layers.Dropout(0.1, name="dropout")(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="priority_probs")(x)
    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="aegiscore_risk_priority")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def _train_legacy_fixture_tensorflow_model(
    *,
    dataset_path: Path,
    model_output_path: Path,
    metadata_output_path: Path,
    requested_version: str | None = None,
) -> dict[str, Any]:
    _set_deterministic_seed(42)
    dataset = pd.read_csv(dataset_path)
    frame = _normalize_training_frame(dataset)
    x_train, prep_meta = _build_training_matrix(frame)

    label_classes = sorted(frame["priority_label"].unique().tolist())
    if len(label_classes) < 2:
        raise ValueError("Training dataset needs at least two distinct priority_label values.")
    label_to_index = {label: idx for idx, label in enumerate(label_classes)}
    y_train = frame["priority_label"].map(label_to_index).astype(np.int32).values

    input_dim = int(x_train.shape[1])
    num_classes = len(label_classes)
    model = _build_keras_classifier(input_dim, num_classes)

    model.fit(
        x_train,
        y_train,
        epochs=60,
        batch_size=min(32, len(frame)),
        verbose=0,
    )

    _, train_accuracy = model.evaluate(x_train, y_train, verbose=0)

    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_output_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_output_path)

    model_version = requested_version or datetime.now(UTC).strftime("risk_model_%Y%m%d_%H%M%S")
    metadata = {
        "training_schema": LEGACY_TRAINING_SCHEMA,
        "model_version": model_version,
        "trained_at": datetime.now(UTC).isoformat(),
        "training_rows": int(len(frame)),
        "train_accuracy": round(float(train_accuracy), 4),
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "categorical_columns": MODEL_CATEGORICAL_FEATURES,
        "numeric_columns": MODEL_NUMERIC_FEATURES,
        "label_classes": label_classes,
        "label_to_index": label_to_index,
        "ml_framework": "tensorflow",
        "framework": "tensorflow",
        "feature_column_names": prep_meta["feature_column_names"],
        "numeric_means": prep_meta["numeric_means"],
        "numeric_stds": prep_meta["numeric_stds"],
    }
    metadata_output_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def train_priority_model(
    *,
    dataset_path: Path,
    model_output_path: Path,
    metadata_output_path: Path,
    requested_version: str | None = None,
) -> dict[str, Any]:
    dataset = pd.read_csv(dataset_path)
    if ap.is_alert_prioritization_dataset(dataset):
        eval_dir_raw = os.getenv("AI_EVAL_OUTPUT_DIR")
        default_eval = dataset_path.resolve().parent.parent / "outputs" / "alert_prioritization"
        eval_output_dir = Path(eval_dir_raw) if eval_dir_raw else default_eval
        return ap.train_alert_prioritization_model(
            dataset_path=dataset_path,
            model_output_path=model_output_path,
            metadata_output_path=metadata_output_path,
            requested_version=requested_version,
            eval_output_dir=eval_output_dir,
            random_seed=42,
        )
    return _train_legacy_fixture_tensorflow_model(
        dataset_path=dataset_path,
        model_output_path=model_output_path,
        metadata_output_path=metadata_output_path,
        requested_version=requested_version,
    )


def load_priority_model(
    *,
    model_path: str | Path,
    metadata_path: str | Path,
) -> tuple[tf.keras.Model, dict[str, Any]]:
    resolved_model_path = Path(model_path)
    resolved_metadata_path = Path(metadata_path)
    if not resolved_model_path.exists():
        raise ModelArtifactUnavailableError(
            f"Risk model artifact does not exist at {resolved_model_path}."
        )
    if not resolved_metadata_path.exists():
        raise ModelArtifactUnavailableError(
            f"Risk model metadata does not exist at {resolved_metadata_path}."
        )

    metadata = json.loads(resolved_metadata_path.read_text(encoding="utf-8"))
    schema = metadata.get("training_schema")
    if schema == ap.TRAINING_SCHEMA:
        required_keys = (
            "feature_column_names",
            "numeric_means",
            "numeric_stds",
            "label_classes",
            "categorical_allowed_values",
        )
    else:
        required_keys = ("feature_column_names", "numeric_means", "numeric_stds", "label_classes")

    missing = [key for key in required_keys if key not in metadata]
    if missing:
        raise ModelArtifactUnavailableError(
            f"Model metadata is missing TensorFlow preprocessing keys: {', '.join(missing)}. "
            "Retrain with ai/training/train_risk_model.py."
        )

    suffix = resolved_model_path.suffix.lower()
    if suffix not in (".keras", ".h5"):
        raise ModelArtifactUnavailableError(
            f"Expected TensorFlow Keras model file (.keras or .h5); got {suffix!r}. "
            "Scikit-learn joblib dumps are not supported; the primary artifact is a .keras file."
        )

    model = tf.keras.models.load_model(resolved_model_path, compile=False)
    return model, metadata


def _score_legacy_tensorflow_model(
    *,
    features: AlertRiskFeatures,
    model: tf.keras.Model,
    metadata: dict[str, Any],
) -> ScoringResult:
    x_row = _row_from_features(features, metadata)
    probabilities = model.predict(x_row, verbose=0)[0]
    classes = [str(label) for label in metadata.get("label_classes", [])]
    if len(classes) != len(probabilities):
        raise ModelArtifactUnavailableError(
            "Model output size does not match label_classes in metadata."
        )
    class_probabilities = {
        label: round(float(probability), 4)
        for label, probability in zip(classes, probabilities, strict=True)
    }

    weighted_score = sum(
        class_probabilities.get(label, 0.0) * RISK_PRIORITY_ANCHORS.get(label, 0)
        for label in classes
    )
    top_label = max(class_probabilities, key=class_probabilities.get)
    confidence = round(float(class_probabilities[top_label]), 2)
    priority_label = priority_from_score(weighted_score)
    rounded_score = round(float(weighted_score), 2)

    factors = [
        f"Model probability for {label} priority: {round(probability * 100, 1)}%"
        for label, probability in sorted(
            class_probabilities.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:3]
    ]
    if features.privileged_account_flag:
        factors.append("Privileged account context was present in the feature set.")
    if features.sensitive_file_flag:
        factors.append("Sensitive file context contributed to the model features.")
    if features.repeated_event_count > 1:
        factors.append(
            f"Repeated event count reached {features.repeated_event_count} in the model window."
        )

    explanation = {
        "label": "Trainable model score (legacy fixture schema)",
        "summary": (
            f"Model version {metadata.get('model_version', 'unknown')} predicted "
            f"{priority_label.value} priority at {rounded_score}/100."
        ),
        "rationale": (
            "LEGACY TensorFlow (Keras) classifier on MODEL_* one-hot categoricals and "
            "z-scored numerics from risk_training_fixture.csv."
        ),
        "factors": factors,
        "class_probabilities": class_probabilities,
        "score": rounded_score,
        "priority_label": priority_label.value,
        "scoring_method": ScoreMethod.TENSORFLOW_MODEL.value,
        "model_version": metadata.get("model_version"),
        "training_schema": metadata.get("training_schema", LEGACY_TRAINING_SCHEMA),
    }

    return ScoringResult(
        score=rounded_score,
        confidence=confidence,
        priority_label=priority_label,
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        reasoning=(
            f"Model version {metadata.get('model_version', 'unknown')} predicted "
            f"{priority_label.value} priority with {round(confidence * 100)}% confidence."
        ),
        explanation=explanation,
        feature_snapshot=features.to_snapshot(),
        baseline_version=None,
        model_version=metadata.get("model_version"),
    )


def score_with_model(
    *,
    features: AlertRiskFeatures,
    model: tf.keras.Model,
    metadata: dict[str, Any],
) -> ScoringResult:
    if metadata.get("training_schema") == ap.TRAINING_SCHEMA:
        return ap.score_alert_model_with_features(
            features=features,
            model=model,
            metadata=metadata,
        )
    return _score_legacy_tensorflow_model(
        features=features,
        model=model,
        metadata=metadata,
    )
