from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.models.enums import ScoreMethod
from app.services.scoring.baseline import priority_from_score
from app.services.scoring.constants import (
    MODEL_CATEGORICAL_FEATURES,
    MODEL_FEATURE_COLUMNS,
    MODEL_NUMERIC_FEATURES,
    RISK_PRIORITY_ANCHORS,
)
from app.services.scoring.types import AlertRiskFeatures, ScoringResult


class ModelArtifactUnavailableError(RuntimeError):
    pass


def _normalize_training_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
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


def build_training_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                MODEL_CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                StandardScaler(),
                MODEL_NUMERIC_FEATURES,
            ),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                ),
            ),
        ]
    )


def train_priority_model(
    *,
    dataset_path: Path,
    model_output_path: Path,
    metadata_output_path: Path,
    requested_version: str | None = None,
) -> dict[str, Any]:
    dataset = pd.read_csv(dataset_path)
    frame = _normalize_training_frame(dataset)
    pipeline = build_training_pipeline()
    pipeline.fit(frame[MODEL_FEATURE_COLUMNS], frame["priority_label"])

    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_output_path)

    model_version = requested_version or datetime.now(UTC).strftime("risk_model_%Y%m%d_%H%M%S")
    metadata = {
        "model_version": model_version,
        "trained_at": datetime.now(UTC).isoformat(),
        "training_rows": int(len(frame)),
        "train_accuracy": round(
            float(pipeline.score(frame[MODEL_FEATURE_COLUMNS], frame["priority_label"])),
            4,
        ),
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "categorical_columns": MODEL_CATEGORICAL_FEATURES,
        "numeric_columns": MODEL_NUMERIC_FEATURES,
        "label_classes": [str(label) for label in pipeline.classes_],
    }
    metadata_output_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def load_priority_model(
    *,
    model_path: str | Path,
    metadata_path: str | Path,
) -> tuple[Pipeline, dict[str, Any]]:
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

    pipeline = joblib.load(resolved_model_path)
    metadata = json.loads(resolved_metadata_path.read_text(encoding="utf-8"))
    return pipeline, metadata


def score_with_model(
    *,
    features: AlertRiskFeatures,
    pipeline: Pipeline,
    metadata: dict[str, Any],
) -> ScoringResult:
    frame = pd.DataFrame([features.to_model_input()])
    probabilities = pipeline.predict_proba(frame)[0]
    classes = [str(label) for label in getattr(pipeline, "classes_", metadata.get("label_classes", []))]
    class_probabilities = {
        label: round(float(probability), 4)
        for label, probability in zip(classes, probabilities, strict=False)
    }

    weighted_score = sum(
        class_probabilities.get(label, 0.0) * anchor
        for label, anchor in RISK_PRIORITY_ANCHORS.items()
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
        "label": "Trainable model score",
        "summary": (
            f"Model version {metadata.get('model_version', 'unknown')} predicted "
            f"{priority_label.value} priority at {rounded_score}/100."
        ),
        "rationale": (
            "The scikit-learn model evaluates categorical detection context and "
            "numeric recurrence features from normalized alert telemetry."
        ),
        "factors": factors,
        "class_probabilities": class_probabilities,
        "score": rounded_score,
        "priority_label": priority_label.value,
        "scoring_method": ScoreMethod.SKLEARN_MODEL.value,
        "model_version": metadata.get("model_version"),
    }

    return ScoringResult(
        score=rounded_score,
        confidence=confidence,
        priority_label=priority_label,
        scoring_method=ScoreMethod.SKLEARN_MODEL,
        reasoning=(
            f"Model version {metadata.get('model_version', 'unknown')} predicted "
            f"{priority_label.value} priority with {round(confidence * 100)}% confidence."
        ),
        explanation=explanation,
        feature_snapshot=features.to_snapshot(),
        baseline_version=None,
        model_version=metadata.get("model_version"),
    )
