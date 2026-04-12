"""
TensorFlow training + inference helpers for the **alert prioritization** dataset
(`ai/datasets/alerts_dataset.csv`). Schema version: `alert_prioritization_v1`.

This path is separate from the **legacy** `risk_training_fixture.csv` feature schema
defined in `constants.py` (MODEL_* columns).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import tensorflow as tf

from app.models.enums import ScoreMethod
from app.services.scoring.baseline import incident_priority_from_three_class_tier
from app.services.scoring.constants import ALERT_PRIORITY_ANCHORS
from app.services.scoring.types import AlertRiskFeatures, ScoringResult

TRAINING_SCHEMA = "alert_prioritization_v1"
LABEL_COLUMN = "label"
REQUIRED_COLUMNS = [
    "timestamp",
    "threat_type",
    "source_ip",
    "target_host",
    "username",
    "failed_logins_1m",
    "failed_logins_5m",
    "unique_ports_1m",
    "integrity_change",
    "new_user_created",
    "off_hours",
    "privileged_account",
    "asset_criticality",
    "wazuh_rule_level",
    "suricata_severity",
    "blacklisted_ip",
    LABEL_COLUMN,
]

NUMERIC_COLUMNS = [
    "failed_logins_1m",
    "failed_logins_5m",
    "unique_ports_1m",
    "new_user_created",
    "off_hours",
    "privileged_account",
    "wazuh_rule_level",
    "suricata_severity",
    "blacklisted_ip",
    "hour_utc",
]

CATEGORICAL_COLUMNS = [
    "threat_type",
    "integrity_change",
    "asset_criticality",
    "target_host",
    "username",
    "source_ip",
]

CATEGORY_CAPS: dict[str, int] = {
    "target_host": 28,
    "username": 28,
    "source_ip": 40,
}

CANONICAL_LABELS = ("low", "medium", "high")


def is_alert_prioritization_dataset(frame: pd.DataFrame) -> bool:
    cols = {c.strip().lower() for c in frame.columns}
    if LABEL_COLUMN not in cols:
        return False
    if "threat_type" not in cols:
        return False
    return True


def _rename_columns_clean(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out.columns = [c.strip() for c in out.columns]
    rename = {}
    for want in REQUIRED_COLUMNS:
        if want in out.columns:
            continue
        wlow = want.lower()
        for c in out.columns:
            if c.lower() == wlow:
                rename[c] = want
                break
    if rename:
        out = out.rename(columns=rename)
    return out


def _normalize_labels(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.lower()
    allowed = set(CANONICAL_LABELS)
    bad = sorted(set(s.unique()) - allowed)
    if bad:
        raise ValueError(
            f"Dataset labels must be only {sorted(allowed)}; found extra values: {bad}"
        )
    return s


def _hour_from_timestamp(series: pd.Series) -> pd.Series:
    ts = pd.to_datetime(series, utc=True, errors="coerce")
    hours = ts.dt.hour
    return hours.fillna(12).astype(int)


def normalize_alerts_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    df = _rename_columns_clean(frame)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Alert dataset missing columns: {missing}")
    df = df[REQUIRED_COLUMNS].copy()
    df[LABEL_COLUMN] = _normalize_labels(df[LABEL_COLUMN])
    for col in NUMERIC_COLUMNS:
        if col == "hour_utc":
            continue
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["hour_utc"] = _hour_from_timestamp(df["timestamp"])
    for col in CATEGORICAL_COLUMNS:
        df[col] = df[col].fillna("").astype(str).str.strip()
        df[col] = df[col].replace("", "unknown")
    return df


def _allowed_categories(train_series: pd.Series, cap: int) -> list[str]:
    top = train_series.astype(str).value_counts().nlargest(cap).index.astype(str).tolist()
    if "unknown" not in top:
        top.append("unknown")
    return sorted(set(top))


def _apply_cap(series: pd.Series, allowed: list[str]) -> pd.Series:
    allowed_set = set(allowed)
    s = series.astype(str)
    return s.where(s.isin(allowed_set), other="other")


def _categorical_allowed_from_train(train: pd.DataFrame) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for col in CATEGORICAL_COLUMNS:
        cap = CATEGORY_CAPS.get(col, 32)
        out[col] = _allowed_categories(train[col], cap)
    return out


def _frame_with_categorical_caps(frame: pd.DataFrame, caps: dict[str, list[str]]) -> pd.DataFrame:
    f = frame.copy()
    for col in CATEGORICAL_COLUMNS:
        f[col] = _apply_cap(f[col], caps[col])
    return f


def _dummies(frame: pd.DataFrame, categorical_columns: list[str]) -> pd.DataFrame:
    parts = []
    for col in categorical_columns:
        d = pd.get_dummies(frame[col].astype(str), prefix=col, prefix_sep="__", dtype=float)
        parts.append(d)
    return pd.concat(parts, axis=1) if parts else pd.DataFrame(index=frame.index)


def _numeric_matrix(frame: pd.DataFrame, numeric_columns: list[str]) -> pd.DataFrame:
    return frame[numeric_columns].astype(float)


def build_alert_design_matrix(
    frame: pd.DataFrame,
    *,
    categorical_allowed: dict[str, list[str]],
    numeric_means: dict[str, float],
    numeric_stds: dict[str, float],
    feature_column_names: list[str] | None,
) -> tuple[np.ndarray, list[str]]:
    capped = _frame_with_categorical_caps(frame, categorical_allowed)
    cats = _dummies(capped, CATEGORICAL_COLUMNS)
    numeric = _numeric_matrix(capped, NUMERIC_COLUMNS)
    means = pd.Series({k: float(numeric_means[k]) for k in NUMERIC_COLUMNS})
    stds = pd.Series({k: float(numeric_stds[k]) if float(numeric_stds[k]) != 0 else 1.0 for k in NUMERIC_COLUMNS})
    numeric_norm = (numeric - means) / stds.replace(0, 1.0)
    design = pd.concat([cats.reset_index(drop=True), numeric_norm.reset_index(drop=True)], axis=1)
    if feature_column_names is not None:
        design = design.reindex(columns=feature_column_names, fill_value=0.0)
        names = feature_column_names
    else:
        names = list(design.columns)
    return design.values.astype(np.float32), names


def _stratified_split_indices(y: np.ndarray, *, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_idx: list[int] = []
    val_idx: list[int] = []
    test_idx: list[int] = []
    for c in np.unique(y):
        idx = np.where(y == c)[0].tolist()
        rng.shuffle(idx)
        n = len(idx)
        if n == 1:
            train_idx.extend(idx)
            continue
        if n == 2:
            train_idx.append(idx[0])
            val_idx.append(idx[1])
            continue
        n_train = max(1, int(round(n * 0.6)))
        n_val = max(1, int(round(n * 0.2)))
        n_test = n - n_train - n_val
        while n_test < 1 and n_train > 1:
            n_train -= 1
            n_test = n - n_train - n_val
        if n_test < 1:
            n_val = max(1, n_val - 1)
            n_test = n - n_train - n_val
        train_idx.extend(idx[:n_train])
        val_idx.extend(idx[n_train : n_train + n_val])
        test_idx.extend(idx[n_train + n_val :])
    rng.shuffle(train_idx)
    rng.shuffle(val_idx)
    rng.shuffle(test_idx)
    return (
        np.asarray(train_idx, dtype=int),
        np.asarray(val_idx, dtype=int),
        np.asarray(test_idx, dtype=int),
    )


def _build_keras_mlp(input_dim: int, num_classes: int) -> tf.keras.Model:
    inputs = tf.keras.Input(shape=(input_dim,), name="alert_features")
    x = tf.keras.layers.Dense(128, activation="relu", name="dense_1")(inputs)
    x = tf.keras.layers.Dropout(0.2, name="dropout_1")(x)
    x = tf.keras.layers.Dense(64, activation="relu", name="dense_2")(x)
    x = tf.keras.layers.Dropout(0.1, name="dropout_2")(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="priority_probs")(x)
    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="aegiscore_alert_prioritization")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def _confusion_matrix_counts(y_true: np.ndarray, y_pred: np.ndarray, labels: list[str]) -> np.ndarray:
    label_to_i = {lab: i for i, lab in enumerate(labels)}
    mat = np.zeros((len(labels), len(labels)), dtype=int)
    for t, p in zip(y_true, y_pred, strict=True):
        mat[label_to_i[str(t)], label_to_i[str(p)]] += 1
    return mat


def _classification_report_text(
    y_true: list[str], y_pred: list[str], labels: list[str]
) -> str:
    lines = ["precision  recall  f1-score  support", "-" * 44]
    supports: dict[str, int] = {lab: y_true.count(lab) for lab in labels}
    tp_fp_fn: dict[str, tuple[int, int, int]] = {}
    for lab in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == lab and p == lab)
        fp = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t != lab and p == lab)
        fn = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == lab and p != lab)
        tp_fp_fn[lab] = (tp, fp, fn)

    def pr_f1(lab: str) -> tuple[float, float, float]:
        tp, fp, fn = tp_fp_fn[lab]
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        return prec, rec, f1

    for lab in labels:
        prec, rec, f1 = pr_f1(lab)
        sup = supports[lab]
        lines.append(
            f"{lab:8}  {prec:0.2f}    {rec:0.2f}    {f1:0.2f}     {sup}"
        )
    acc = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == p) / max(len(y_true), 1)
    lines.append("-" * 44)
    lines.append(f"accuracy (micro) {acc:0.4f}  total {len(y_true)}")
    return "\n".join(lines)


def _write_eval_outputs(
    out_dir: Path,
    *,
    confusion: np.ndarray,
    labels: list[str],
    report_text: str,
    test_accuracy: float,
    class_dist: dict[str, Any],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    header = ",".join(["true\\pred"] + labels)
    lines = [header]
    for i, row_label in enumerate(labels):
        row = ",".join([row_label] + [str(int(x)) for x in confusion[i].tolist()])
        lines.append(row)
    (out_dir / "confusion_matrix.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "classification_report.txt").write_text(report_text + "\n", encoding="utf-8")
    metrics = {"test_accuracy": test_accuracy, "class_distribution": class_dist}
    (out_dir / "evaluation_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )


def train_alert_prioritization_model(
    *,
    dataset_path: Path,
    model_output_path: Path,
    metadata_output_path: Path,
    requested_version: str | None = None,
    eval_output_dir: Path | None = None,
    random_seed: int = 42,
) -> dict[str, Any]:
    tf.random.set_seed(random_seed)
    np.random.seed(random_seed)

    raw = pd.read_csv(dataset_path)
    frame = normalize_alerts_dataframe(raw)

    label_classes = list(CANONICAL_LABELS)
    label_to_index = {lab: i for i, lab in enumerate(label_classes)}
    y_all = frame[LABEL_COLUMN].map(label_to_index).astype(np.int32).values

    train_idx, val_idx, test_idx = _stratified_split_indices(y_all, seed=random_seed)
    if len(test_idx) == 0 and len(train_idx) > 10:
        rng = np.random.default_rng(random_seed + 99)
        pick = rng.choice(train_idx, size=min(50, len(train_idx) // 5), replace=False)
        test_idx = np.sort(pick)
        train_idx = np.array([i for i in train_idx if i not in set(test_idx)], dtype=int)
    train_df = frame.iloc[train_idx].reset_index(drop=True)
    val_df = frame.iloc[val_idx].reset_index(drop=True)
    test_df = frame.iloc[test_idx].reset_index(drop=True)

    categorical_allowed = _categorical_allowed_from_train(train_df)

    train_c = _frame_with_categorical_caps(train_df, categorical_allowed)
    numeric_train = _numeric_matrix(train_c, NUMERIC_COLUMNS)
    means = {k: float(v) for k, v in numeric_train.mean().items()}
    stds = {
        k: float(v) if float(v) != 0 else 1.0 for k, v in numeric_train.std(ddof=0).items()
    }

    x_train, feature_column_names = build_alert_design_matrix(
        train_df,
        categorical_allowed=categorical_allowed,
        numeric_means=means,
        numeric_stds=stds,
        feature_column_names=None,
    )
    x_val, _ = build_alert_design_matrix(
        val_df,
        categorical_allowed=categorical_allowed,
        numeric_means=means,
        numeric_stds=stds,
        feature_column_names=feature_column_names,
    )
    x_test, _ = build_alert_design_matrix(
        test_df,
        categorical_allowed=categorical_allowed,
        numeric_means=means,
        numeric_stds=stds,
        feature_column_names=feature_column_names,
    )

    y_train = train_df[LABEL_COLUMN].map(label_to_index).astype(np.int32).values
    y_val = val_df[LABEL_COLUMN].map(label_to_index).astype(np.int32).values
    y_test = test_df[LABEL_COLUMN].map(label_to_index).astype(np.int32).values

    input_dim = int(x_train.shape[1])
    model = _build_keras_mlp(input_dim, len(label_classes))

    cb = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=12, restore_best_weights=True
        )
    ]
    model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=120,
        batch_size=min(64, max(16, len(train_df) // 4)),
        verbose=0,
        callbacks=cb,
    )

    _, train_acc = model.evaluate(x_train, y_train, verbose=0)
    _, val_acc = model.evaluate(x_val, y_val, verbose=0)
    _, test_acc = model.evaluate(x_test, y_test, verbose=0)

    pred_idx = np.argmax(model.predict(x_test, verbose=0), axis=1)
    index_to_label = {i: lab for lab, i in label_to_index.items()}
    y_test_labels = [index_to_label[int(i)] for i in y_test]
    y_pred_labels = [index_to_label[int(i)] for i in pred_idx]
    conf_mat = _confusion_matrix_counts(y_test_labels, y_pred_labels, label_classes)
    report = _classification_report_text(y_test_labels, y_pred_labels, label_classes)

    class_dist = {
        "train": train_df[LABEL_COLUMN].value_counts().sort_index().to_dict(),
        "validation": val_df[LABEL_COLUMN].value_counts().sort_index().to_dict(),
        "test": test_df[LABEL_COLUMN].value_counts().sort_index().to_dict(),
    }

    if eval_output_dir is not None:
        _write_eval_outputs(
            eval_output_dir,
            confusion=conf_mat,
            labels=label_classes,
            report_text=report,
            test_accuracy=float(test_acc),
            class_dist=class_dist,
        )

    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_output_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_output_path)

    model_version = requested_version or datetime.now(UTC).strftime("alert_model_%Y%m%d_%H%M%S")
    metadata: dict[str, Any] = {
        "training_schema": TRAINING_SCHEMA,
        "model_version": model_version,
        "trained_at": datetime.now(UTC).isoformat(),
        "framework": "tensorflow",
        "ml_framework": "tensorflow",
        "training_rows": int(len(frame)),
        "train_rows": int(len(train_df)),
        "validation_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "metrics": {
            "train_accuracy": round(float(train_acc), 4),
            "validation_accuracy": round(float(val_acc), 4),
            "test_accuracy": round(float(test_acc), 4),
        },
        "label_classes": label_classes,
        "label_to_index": label_to_index,
        "feature_column_names": feature_column_names,
        "numeric_columns": NUMERIC_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "numeric_means": means,
        "numeric_stds": stds,
        "categorical_allowed_values": categorical_allowed,
        "evaluation_artifacts_dir": str(eval_output_dir) if eval_output_dir else None,
    }
    metadata_output_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def dataframe_from_alert_payload(payload: dict[str, Any]) -> pd.DataFrame:
    """Single-row frame matching training columns (label optional, ignored for X)."""
    row = {k: payload.get(k) for k in REQUIRED_COLUMNS if k != LABEL_COLUMN}
    if LABEL_COLUMN in payload:
        row[LABEL_COLUMN] = payload[LABEL_COLUMN]
    else:
        row[LABEL_COLUMN] = "low"
    return pd.DataFrame([row])


def vectorize_alert_payload(metadata: dict[str, Any], payload: dict[str, Any]) -> np.ndarray:
    if metadata.get("training_schema") != TRAINING_SCHEMA:
        raise ValueError("Metadata is not alert_prioritization_v1; cannot vectorize this payload.")
    frame = normalize_alerts_dataframe(dataframe_from_alert_payload(payload))
    x, _ = build_alert_design_matrix(
        frame,
        categorical_allowed=metadata["categorical_allowed_values"],
        numeric_means=metadata["numeric_means"],
        numeric_stds=metadata["numeric_stds"],
        feature_column_names=metadata["feature_column_names"],
    )
    return x


def alert_row_from_risk_features(features: AlertRiskFeatures) -> dict[str, Any]:
    """Map API `AlertRiskFeatures` into CSV-style fields for the prioritization MLP."""
    det = features.detection_type
    if det == "file_integrity_violation":
        threat = "file_integrity"
    else:
        threat = det
    integrity = features.integrity_change or (
        "important" if features.sensitive_file_flag else "none"
    )
    new_user = max(
        int(features.new_user_created),
        1 if det == "unauthorized_user_creation" else 0,
    )
    off = int(features.off_hours)
    suri = int(features.suricata_severity)
    if suri == 0 and features.source_type.lower() == "suricata":
        suri = int(features.source_severity)
    bl = int(features.blacklisted_ip)
    if bl == 0 and features.repeated_source_ip > 3:
        bl = 1
    f5 = max(int(features.failed_logins_5m), int(features.repeated_failed_logins))
    f1 = max(int(features.failed_logins_1m), min(f5, int(features.repeated_failed_logins)))
    uports = int(features.unique_ports_1m)
    if uports <= 0 and features.has_destination_port:
        uports = int(features.destination_port)
    if uports <= 0:
        uports = max(int(features.time_window_density), int(features.repeated_event_count), 0)
    return {
        "timestamp": features.observed_at.isoformat(),
        "threat_type": threat,
        "source_ip": (features.source_ip or "unknown").strip() or "unknown",
        "target_host": (features.asset_hostname or "unknown.host").strip() or "unknown.host",
        "username": (features.username or "").strip() or "unknown",
        "failed_logins_1m": min(f1, 60),
        "failed_logins_5m": min(f5, 120),
        "unique_ports_1m": min(uports, 200),
        "integrity_change": integrity,
        "new_user_created": new_user,
        "off_hours": off,
        "privileged_account": int(features.privileged_account_flag),
        "asset_criticality": str(features.asset_criticality).lower(),
        "wazuh_rule_level": int(features.source_rule_level),
        "suricata_severity": suri,
        "blacklisted_ip": bl,
    }


def score_alert_model_with_features(
    *,
    features: AlertRiskFeatures,
    model: tf.keras.Model,
    metadata: dict[str, Any],
) -> ScoringResult:
    row = alert_row_from_risk_features(features)
    x_row = vectorize_alert_payload(metadata, row)
    probabilities = model.predict(x_row, verbose=0)[0]
    classes = [str(x) for x in metadata["label_classes"]]
    if len(classes) != len(probabilities):
        raise ValueError("Model output size does not match label_classes in metadata.")
    class_probabilities = {
        label: round(float(probability), 4) for label, probability in zip(classes, probabilities, strict=True)
    }
    weighted_score = sum(
        class_probabilities.get(lab, 0.0) * ALERT_PRIORITY_ANCHORS[lab] for lab in classes
    )
    top_label_str = max(class_probabilities, key=class_probabilities.get)
    confidence = round(float(class_probabilities[top_label_str]), 2)
    priority_label = incident_priority_from_three_class_tier(top_label_str)
    rounded_score = min(round(float(weighted_score), 2), 84.0)

    factors = [
        f"Model probability for {lab} class: {round(prob * 100, 1)}%"
        for lab, prob in sorted(class_probabilities.items(), key=lambda kv: kv[1], reverse=True)
    ]
    explanation = {
        "label": "Trainable alert prioritization model",
        "summary": (
            f"Model version {metadata.get('model_version', 'unknown')} predicted "
            f"{priority_label.value} priority at {rounded_score}/100 "
            f"(3-class TensorFlow output: {top_label_str})."
        ),
        "rationale": (
            "TensorFlow (Keras) MLP on one-hot categorical caps and z-scored numeric "
            "features derived from normalized alert telemetry (alert_prioritization_v1). "
            "Threat type comes from connectors/normalization; the model assigns only "
            "low / medium / high priority (never critical as a class)."
        ),
        "factors": factors,
        "class_probabilities": class_probabilities,
        "score": rounded_score,
        "priority_label": priority_label.value,
        "model_priority_tier": top_label_str,
        "predicted_class": top_label_str,
        "alert_model_input": row,
        "scoring_method": ScoreMethod.TENSORFLOW_MODEL.value,
        "model_version": metadata.get("model_version"),
    }

    return ScoringResult(
        score=rounded_score,
        confidence=confidence,
        priority_label=priority_label,
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        reasoning=(
            f"Model version {metadata.get('model_version', 'unknown')} assigned "
            f"{priority_label.value} priority (TensorFlow 3-class tier: {top_label_str}) "
            f"with {round(confidence * 100)}% confidence on the predicted tier."
        ),
        explanation=explanation,
        feature_snapshot=features.to_snapshot(),
        baseline_version=None,
        model_version=metadata.get("model_version"),
    )


def predict_alert_model_json(
    *,
    model: tf.keras.Model,
    metadata: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    x_row = vectorize_alert_payload(metadata, payload)
    probabilities = model.predict(x_row, verbose=0)[0]
    classes = [str(x) for x in metadata["label_classes"]]
    class_probabilities = {
        lab: round(float(p), 4) for lab, p in zip(classes, probabilities, strict=True)
    }
    pred_idx = int(np.argmax(probabilities))
    predicted = classes[pred_idx]
    confidence = round(float(probabilities[pred_idx]), 4)
    return {
        "predicted_label": predicted,
        "confidence": confidence,
        "probabilities": class_probabilities,
        "model_version": metadata.get("model_version"),
        "training_schema": metadata.get("training_schema"),
    }
