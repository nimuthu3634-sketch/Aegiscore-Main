"""
AegisCore Enterprise — TensorFlow Alert Prioritization
======================================================
Schema: alert_prioritization_v2

4-class priority output: critical / high / medium / low

Model architecture (enterprise MLP):
    Input
    → Dense(256, relu) → BatchNorm → Dropout(0.3)
    → Dense(128, relu) → BatchNorm → Dropout(0.2)
    → Dense(64,  relu) → BatchNorm → Dropout(0.1)
    → Dense(32,  relu)
    → Dense(4, softmax)

Training:
    - Stratified 60/20/20 train/val/test split
    - Inverse-frequency class weights (handles critical imbalance)
    - EarlyStopping  (patience=20, monitor=val_loss, restore_best_weights=True)
    - ReduceLROnPlateau (patience=10, factor=0.5, min_lr=1e-6)
    - Evaluation: confusion matrix, per-class F1/precision/recall, test accuracy

Feature set (enterprise — no synthetic high-cardinality identifiers):
    Categorical: source_type, threat_type, asset_criticality, integrity_change
    Numeric:     wazuh_rule_level, suricata_severity,
                 failed_logins_1m, failed_logins_5m, unique_ports_1m,
                 repeated_event_count, time_window_density, recurrence_history,
                 new_user_created, off_hours, privileged_account, blacklisted_ip
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import tensorflow as tf

from app.models.enums import IncidentPriority, ScoreMethod
from app.services.scoring.constants import ALERT_PRIORITY_ANCHORS
from app.services.scoring.types import AlertRiskFeatures, ScoringResult

TRAINING_SCHEMA = "alert_prioritization_v2"
LABEL_COLUMN    = "label"
CANONICAL_LABELS = ("low", "medium", "high", "critical")

# ── feature definitions ────────────────────────────────────────────────────

REQUIRED_COLUMNS = [
    "source_type", "threat_type", "asset_criticality", "integrity_change",
    "wazuh_rule_level", "suricata_severity",
    "failed_logins_1m", "failed_logins_5m", "unique_ports_1m",
    "repeated_event_count", "time_window_density", "recurrence_history",
    "new_user_created", "off_hours", "privileged_account", "blacklisted_ip",
    LABEL_COLUMN,
]

CATEGORICAL_COLUMNS = [
    "source_type",
    "threat_type",
    "asset_criticality",
    "integrity_change",
]

NUMERIC_COLUMNS = [
    "wazuh_rule_level",
    "suricata_severity",
    "failed_logins_1m",
    "failed_logins_5m",
    "unique_ports_1m",
    "repeated_event_count",
    "time_window_density",
    "recurrence_history",
    "new_user_created",
    "off_hours",
    "privileged_account",
    "blacklisted_ip",
]

# ── schema detection ───────────────────────────────────────────────────────

def is_alert_prioritization_dataset(frame: pd.DataFrame) -> bool:
    cols = {c.strip().lower() for c in frame.columns}
    return LABEL_COLUMN in cols and "threat_type" in cols and "source_type" in cols


# ── data normalisation ─────────────────────────────────────────────────────

def _rename_columns_clean(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out.columns = [c.strip() for c in out.columns]
    rename = {}
    for want in REQUIRED_COLUMNS:
        if want in out.columns:
            continue
        for c in out.columns:
            if c.lower() == want.lower():
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


def normalize_alerts_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    df = _rename_columns_clean(frame)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Alert dataset missing columns: {missing}")
    df = df[REQUIRED_COLUMNS].copy()
    df[LABEL_COLUMN] = _normalize_labels(df[LABEL_COLUMN])
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)
    for col in CATEGORICAL_COLUMNS:
        df[col] = df[col].fillna("unknown").astype(str).str.strip().replace("", "unknown")
    return df


# ── design matrix ──────────────────────────────────────────────────────────

def build_alert_design_matrix(
    frame: pd.DataFrame,
    *,
    numeric_means: dict[str, float],
    numeric_stds: dict[str, float],
    feature_column_names: list[str] | None,
) -> tuple[np.ndarray, list[str]]:
    cats = pd.get_dummies(
        frame[CATEGORICAL_COLUMNS].astype(str),
        prefix=CATEGORICAL_COLUMNS,
        prefix_sep="__",
        dtype=float,
    )
    numeric = frame[NUMERIC_COLUMNS].astype(float)
    means  = pd.Series({k: float(numeric_means[k]) for k in NUMERIC_COLUMNS})
    stds   = pd.Series({k: max(float(numeric_stds[k]), 1e-8) for k in NUMERIC_COLUMNS})
    numeric_norm = (numeric - means) / stds
    design = pd.concat([cats.reset_index(drop=True), numeric_norm.reset_index(drop=True)], axis=1)
    if feature_column_names is not None:
        design = design.reindex(columns=feature_column_names, fill_value=0.0)
        names = feature_column_names
    else:
        names = list(design.columns)
    return design.values.astype(np.float32), names


# ── stratified 60/20/20 split ──────────────────────────────────────────────

def _stratified_split(y: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_idx, val_idx, test_idx = [], [], []
    for cls in np.unique(y):
        idx = np.where(y == cls)[0].tolist()
        rng.shuffle(idx)
        n = len(idx)
        n_train = max(1, int(round(n * 0.60)))
        n_val   = max(1, int(round(n * 0.20)))
        n_test  = n - n_train - n_val
        if n_test < 1:
            n_val  = max(1, n_val - 1)
            n_test = n - n_train - n_val
        train_idx.extend(idx[:n_train])
        val_idx.extend(idx[n_train:n_train + n_val])
        test_idx.extend(idx[n_train + n_val:])
    for lst in (train_idx, val_idx, test_idx):
        rng.shuffle(lst)
    return (np.array(train_idx), np.array(val_idx), np.array(test_idx))


# ── model architecture ─────────────────────────────────────────────────────

def _build_enterprise_mlp(input_dim: int, num_classes: int) -> tf.keras.Model:
    """
    Enterprise 4-layer MLP with BatchNormalization and progressive Dropout.

    Layer 1: Dense(256) → BatchNorm → Dropout(0.3)
    Layer 2: Dense(128) → BatchNorm → Dropout(0.2)
    Layer 3: Dense(64)  → BatchNorm → Dropout(0.1)
    Layer 4: Dense(32)
    Output:  Dense(num_classes, softmax)
    """
    inputs = tf.keras.Input(shape=(input_dim,), name="alert_features")

    x = tf.keras.layers.Dense(256, activation="relu", name="dense_1")(inputs)
    x = tf.keras.layers.BatchNormalization(name="bn_1")(x)
    x = tf.keras.layers.Dropout(0.3, name="dropout_1")(x)

    x = tf.keras.layers.Dense(128, activation="relu", name="dense_2")(x)
    x = tf.keras.layers.BatchNormalization(name="bn_2")(x)
    x = tf.keras.layers.Dropout(0.2, name="dropout_2")(x)

    x = tf.keras.layers.Dense(64, activation="relu", name="dense_3")(x)
    x = tf.keras.layers.BatchNormalization(name="bn_3")(x)
    x = tf.keras.layers.Dropout(0.1, name="dropout_3")(x)

    x = tf.keras.layers.Dense(32, activation="relu", name="dense_4")(x)

    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="priority_probs")(x)

    model = tf.keras.Model(
        inputs=inputs, outputs=outputs, name="aegiscore_enterprise_alert_priority"
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


# ── evaluation helpers ─────────────────────────────────────────────────────

def _confusion_matrix(y_true: list[str], y_pred: list[str], labels: list[str]) -> np.ndarray:
    idx = {l: i for i, l in enumerate(labels)}
    mat = np.zeros((len(labels), len(labels)), dtype=int)
    for t, p in zip(y_true, y_pred, strict=True):
        mat[idx[t], idx[p]] += 1
    return mat


def _classification_report(y_true: list[str], y_pred: list[str], labels: list[str]) -> str:
    lines = [f"{'':12s} {'precision':>9} {'recall':>7} {'f1':>6} {'support':>8}", "-" * 48]
    for lab in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == lab and p == lab)
        fp = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t != lab and p == lab)
        fn = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == lab and p != lab)
        sup = tp + fn
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec  = tp / (tp + fn) if (tp + fn) else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        lines.append(f"{lab:12s} {prec:9.4f} {rec:7.4f} {f1:6.4f} {sup:8d}")
    acc = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == p) / max(len(y_true), 1)
    lines += ["-" * 48, f"{'accuracy':12s} {acc:9.4f}  total: {len(y_true)}"]
    return "\n".join(lines)


def _write_eval_outputs(
    out_dir: Path, *, conf: np.ndarray, labels: list[str],
    report: str, metrics: dict[str, Any],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    header = ",".join(["true\\pred"] + labels)
    lines  = [header] + [
        ",".join([labels[i]] + [str(int(conf[i, j])) for j in range(len(labels))])
        for i in range(len(labels))
    ]
    (out_dir / "confusion_matrix.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "classification_report.txt").write_text(report + "\n", encoding="utf-8")
    (out_dir / "evaluation_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")


# ── training ───────────────────────────────────────────────────────────────

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

    raw   = pd.read_csv(dataset_path)
    frame = normalize_alerts_dataframe(raw)

    label_classes  = list(CANONICAL_LABELS)
    label_to_index = {lab: i for i, lab in enumerate(label_classes)}
    y_all = frame[LABEL_COLUMN].map(label_to_index).astype(np.int32).values

    train_idx, val_idx, test_idx = _stratified_split(y_all, random_seed)
    train_df = frame.iloc[train_idx].reset_index(drop=True)
    val_df   = frame.iloc[val_idx].reset_index(drop=True)
    test_df  = frame.iloc[test_idx].reset_index(drop=True)

    # Compute normalisation stats from training set only
    numeric_train = train_df[NUMERIC_COLUMNS].astype(float)
    means = {k: float(v) for k, v in numeric_train.mean().items()}
    stds  = {k: max(float(v), 1e-8) for k, v in numeric_train.std(ddof=0).items()}

    x_train, feature_names = build_alert_design_matrix(
        train_df, numeric_means=means, numeric_stds=stds, feature_column_names=None
    )
    x_val, _  = build_alert_design_matrix(
        val_df,  numeric_means=means, numeric_stds=stds, feature_column_names=feature_names
    )
    x_test, _ = build_alert_design_matrix(
        test_df, numeric_means=means, numeric_stds=stds, feature_column_names=feature_names
    )

    y_train = train_df[LABEL_COLUMN].map(label_to_index).astype(np.int32).values
    y_val   = val_df[LABEL_COLUMN].map(label_to_index).astype(np.int32).values
    y_test  = test_df[LABEL_COLUMN].map(label_to_index).astype(np.int32).values

    # Inverse-frequency class weights — prevents model ignoring rare critical class
    counts = Counter(y_train.tolist())
    total  = sum(counts.values())
    class_weight = {idx: total / (len(counts) * cnt) for idx, cnt in counts.items()}

    model = _build_enterprise_mlp(int(x_train.shape[1]), len(label_classes))

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=20,
            restore_best_weights=True, verbose=0,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5,
            patience=10, min_lr=1e-6, verbose=0,
        ),
    ]

    history = model.fit(
        x_train, y_train,
        validation_data=(x_val, y_val),
        epochs=150,
        batch_size=64,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=0,
    )
    epochs_trained = len(history.history["loss"])

    _, train_acc = model.evaluate(x_train, y_train, verbose=0)
    _, val_acc   = model.evaluate(x_val,   y_val,   verbose=0)
    _, test_acc  = model.evaluate(x_test,  y_test,  verbose=0)

    # Per-class evaluation on test set
    pred_idx       = np.argmax(model.predict(x_test, verbose=0), axis=1)
    idx_to_label   = {i: l for l, i in label_to_index.items()}
    y_test_labels  = [idx_to_label[int(i)] for i in y_test]
    y_pred_labels  = [idx_to_label[int(i)] for i in pred_idx]
    conf_mat       = _confusion_matrix(y_test_labels, y_pred_labels, label_classes)
    report_text    = _classification_report(y_test_labels, y_pred_labels, label_classes)

    # Per-class accuracy
    per_class_acc = {}
    for lab in label_classes:
        idxs = [i for i, t in enumerate(y_test_labels) if t == lab]
        if idxs:
            correct = sum(1 for i in idxs if y_pred_labels[i] == lab)
            per_class_acc[lab] = round(correct / len(idxs), 4)
        else:
            per_class_acc[lab] = None

    class_dist = {
        "train":      train_df[LABEL_COLUMN].value_counts().sort_index().to_dict(),
        "validation": val_df[LABEL_COLUMN].value_counts().sort_index().to_dict(),
        "test":       test_df[LABEL_COLUMN].value_counts().sort_index().to_dict(),
    }

    if eval_output_dir is not None:
        metrics_dict = {
            "train_accuracy": round(float(train_acc), 6),
            "validation_accuracy": round(float(val_acc), 6),
            "test_accuracy": round(float(test_acc), 6),
            "per_class_test_accuracy": per_class_acc,
            "class_distribution": class_dist,
            "confusion_matrix": {
                label_classes[i]: {label_classes[j]: int(conf_mat[i, j]) for j in range(len(label_classes))}
                for i in range(len(label_classes))
            },
            "label_classes": label_classes,
        }
        _write_eval_outputs(
            eval_output_dir, conf=conf_mat, labels=label_classes,
            report=report_text, metrics=metrics_dict,
        )

    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_output_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_output_path)

    now = datetime.now(UTC)
    model_version = requested_version or now.strftime("enterprise_model_%Y%m%d_%H%M%S")

    metadata: dict[str, Any] = {
        "model_name":              "aegiscore_enterprise_alert_prioritization_v2",
        "training_schema":         TRAINING_SCHEMA,
        "model_version":           model_version,
        "model_architecture":      "MLP_4layer_BatchNorm_Enterprise",
        "layers":                  "Dense(256)+BN+Drop(0.3)→Dense(128)+BN+Drop(0.2)→Dense(64)+BN+Drop(0.1)→Dense(32)→Dense(4,softmax)",
        "trained_at":              now.isoformat(),
        "framework":               "tensorflow",
        "ml_framework":            "tensorflow",
        "training_rows":           int(len(train_df)),
        "validation_rows":         int(len(val_df)),
        "test_rows":               int(len(test_df)),
        "epochs_trained":          epochs_trained,
        "train_accuracy":          round(float(train_acc), 6),
        "validation_accuracy":     round(float(val_acc), 6),
        "test_accuracy":           round(float(test_acc), 6),
        "per_class_test_accuracy": per_class_acc,
        "label_classes":           label_classes,
        "label_to_index":          label_to_index,
        "feature_column_names":    feature_names,
        "numeric_columns":         NUMERIC_COLUMNS,
        "categorical_columns":     CATEGORICAL_COLUMNS,
        "numeric_means":           means,
        "numeric_stds":            stds,
        "class_distribution":      class_dist,
        "confusion_matrix": {
            label_classes[i]: {label_classes[j]: int(conf_mat[i, j]) for j in range(len(label_classes))}
            for i in range(len(label_classes))
        },
    }
    metadata_output_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


# ── inference ──────────────────────────────────────────────────────────────

def incident_priority_from_model_tier(tier: str) -> IncidentPriority:
    """Map 4-class model output to IncidentPriority."""
    key = (tier or "low").strip().lower()
    if key == "critical": return IncidentPriority.CRITICAL
    if key == "high":     return IncidentPriority.HIGH
    if key == "medium":   return IncidentPriority.MEDIUM
    return IncidentPriority.LOW


def alert_row_from_risk_features(features: AlertRiskFeatures) -> dict[str, Any]:
    """Map API AlertRiskFeatures to CSV-style row for model inference."""
    det = features.detection_type
    threat = "file_integrity" if det == "file_integrity_violation" else det
    integrity = features.integrity_change or (
        "important" if features.sensitive_file_flag else "none"
    )
    new_user = max(int(features.new_user_created), 1 if det == "unauthorized_user_creation" else 0)
    suri = int(features.suricata_severity)
    if suri == 0 and features.source_type.lower() == "suricata":
        suri = int(features.source_severity)
    bl   = int(features.blacklisted_ip)
    if bl == 0 and features.repeated_source_ip > 3:
        bl = 1
    f5   = max(int(features.failed_logins_5m), int(features.repeated_failed_logins))
    f1   = max(int(features.failed_logins_1m), min(f5, int(features.repeated_failed_logins)))
    up   = int(features.unique_ports_1m)
    if up <= 0:
        up = max(int(features.time_window_density), int(features.repeated_event_count), 0)
    return {
        "source_type":          features.source_type,
        "threat_type":          threat,
        "asset_criticality":    str(features.asset_criticality).lower(),
        "integrity_change":     integrity,
        "wazuh_rule_level":     int(features.source_rule_level),
        "suricata_severity":    suri,
        "failed_logins_1m":     min(f1, 60),
        "failed_logins_5m":     min(f5, 120),
        "unique_ports_1m":      min(up, 200),
        "repeated_event_count": int(features.repeated_event_count),
        "time_window_density":  int(features.time_window_density),
        "recurrence_history":   int(features.recurrence_history),
        "new_user_created":     new_user,
        "off_hours":            int(features.off_hours),
        "privileged_account":   int(features.privileged_account_flag),
        "blacklisted_ip":       bl,
        LABEL_COLUMN:           "low",   # placeholder for inference
    }


def vectorize_alert_payload(metadata: dict[str, Any], payload: dict[str, Any]) -> np.ndarray:
    if metadata.get("training_schema") != TRAINING_SCHEMA:
        raise ValueError(f"Metadata schema is not {TRAINING_SCHEMA}; cannot vectorize.")
    frame = pd.DataFrame([payload])
    df    = normalize_alerts_dataframe(frame)
    x, _  = build_alert_design_matrix(
        df,
        numeric_means=metadata["numeric_means"],
        numeric_stds=metadata["numeric_stds"],
        feature_column_names=metadata["feature_column_names"],
    )
    return x


def score_alert_model_with_features(
    *,
    features: AlertRiskFeatures,
    model: tf.keras.Model,
    metadata: dict[str, Any],
) -> ScoringResult:
    row           = alert_row_from_risk_features(features)
    x_row         = vectorize_alert_payload(metadata, row)
    probabilities = model.predict(x_row, verbose=0)[0]
    classes       = [str(x) for x in metadata["label_classes"]]

    class_probs = {
        lab: round(float(prob), 4)
        for lab, prob in zip(classes, probabilities, strict=True)
    }
    weighted_score = sum(
        class_probs.get(lab, 0.0) * ALERT_PRIORITY_ANCHORS.get(lab, 0)
        for lab in classes
    )
    top_label_str  = max(class_probs, key=class_probs.get)
    confidence     = round(float(class_probs[top_label_str]), 2)
    priority_label = incident_priority_from_model_tier(top_label_str)
    rounded_score  = round(float(weighted_score), 2)

    factors = [
        f"Model probability for {lab} priority: {round(p * 100, 1)}%"
        for lab, p in sorted(class_probs.items(), key=lambda kv: kv[1], reverse=True)
    ]
    arch = metadata.get("model_architecture", "MLP_4layer_BatchNorm_Enterprise")
    explanation = {
        "label":              "Enterprise alert prioritization model",
        "model_architecture": arch,
        "summary": (
            f"Model {metadata.get('model_version', 'unknown')} predicted "
            f"{priority_label.value} priority at {rounded_score}/100."
        ),
        "rationale": (
            f"TensorFlow Keras {arch}: one-hot categorical features "
            "(source_type, threat_type, asset_criticality, integrity_change) "
            "and z-scored numeric behavioural features. BatchNormalization + "
            "progressive Dropout prevent overfitting. 4-class output includes critical."
        ),
        "factors":             factors,
        "class_probabilities": class_probs,
        "score":               rounded_score,
        "priority_label":      priority_label.value,
        "scoring_method":      ScoreMethod.TENSORFLOW_MODEL.value,
        "model_version":       metadata.get("model_version"),
    }

    return ScoringResult(
        score=rounded_score,
        confidence=confidence,
        priority_label=priority_label,
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        reasoning=(
            f"Enterprise model {metadata.get('model_version', 'unknown')} predicted "
            f"{priority_label.value} with {round(confidence * 100)}% confidence."
        ),
        explanation=explanation,
        feature_snapshot=features.to_snapshot(),
        baseline_version=None,
        model_version=metadata.get("model_version"),
    )


def predict_alert_model_json(
    *, model: tf.keras.Model, metadata: dict[str, Any], payload: dict[str, Any],
) -> dict[str, Any]:
    x_row         = vectorize_alert_payload(metadata, payload)
    probabilities = model.predict(x_row, verbose=0)[0]
    classes       = [str(x) for x in metadata["label_classes"]]
    class_probs   = {lab: round(float(p), 4) for lab, p in zip(classes, probabilities, strict=True)}
    pred_idx      = int(np.argmax(probabilities))
    return {
        "predicted_label":   classes[pred_idx],
        "confidence":        round(float(probabilities[pred_idx]), 4),
        "probabilities":     class_probs,
        "model_version":     metadata.get("model_version"),
        "training_schema":   metadata.get("training_schema"),
    }
