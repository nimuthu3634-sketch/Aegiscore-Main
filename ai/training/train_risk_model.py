"""
AegisCore Enterprise — Standalone Model Training Script
=======================================================
Runs WITHOUT needing the API stack (no SQLAlchemy, FastAPI, etc.)

Usage (from repo root):
    python ai/training/train_risk_model.py

Environment variables (all optional):
    AI_DATASET_PATH          default: ai/datasets/alerts_dataset.csv
    AI_MODEL_PATH            default: ai/models/aegiscore-risk-priority-model.keras
    AI_MODEL_METADATA_PATH   default: ai/models/aegiscore-risk-priority-model.metadata.json
    AI_MODEL_VERSION         default: auto timestamp
    AI_SEED                  default: 42
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import tensorflow as tf

# ── constants ──────────────────────────────────────────────────────────────

TRAINING_SCHEMA = "alert_prioritization_v2"
CANONICAL_LABELS: list[str] = ["low", "medium", "high", "critical"]
LABEL_COLUMN = "label"

CATEGORICAL_COLUMNS: list[str] = [
    "source_type",
    "threat_type",
    "asset_criticality",
    "integrity_change",
]

NUMERIC_COLUMNS: list[str] = [
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

REQUIRED_COLUMNS: list[str] = CATEGORICAL_COLUMNS + NUMERIC_COLUMNS + [LABEL_COLUMN]


# ── data helpers ───────────────────────────────────────────────────────────

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame.columns = pd.Index([str(c).strip() for c in frame.columns])
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"Dataset missing columns: {missing}")
    frame[LABEL_COLUMN] = (
        frame[LABEL_COLUMN].astype(str).str.strip().str.lower()
    )
    bad = sorted(set(frame[LABEL_COLUMN].unique()) - set(CANONICAL_LABELS))
    if bad:
        raise ValueError(f"Unknown labels in dataset: {bad}")
    for col in NUMERIC_COLUMNS:
        series = pd.to_numeric(frame[col], errors="coerce")
        frame[col] = series.fillna(0.0).astype(float)
    for col in CATEGORICAL_COLUMNS:
        frame[col] = (
            frame[col].fillna("unknown").astype(str).str.strip()
        )
    return frame


def build_design_matrix(
    frame: pd.DataFrame,
    means: Optional[dict[str, float]] = None,
    stds: Optional[dict[str, float]] = None,
    feature_cols: Optional[list[str]] = None,
) -> tuple[np.ndarray, dict[str, float], dict[str, float], list[str]]:
    cats = pd.get_dummies(
        frame[CATEGORICAL_COLUMNS].astype(str),
        prefix=CATEGORICAL_COLUMNS,
        prefix_sep="__",
        dtype=float,
    )
    numeric = frame[NUMERIC_COLUMNS].astype(float)

    computed_means: dict[str, float]
    computed_stds: dict[str, float]

    if means is None or stds is None:
        computed_means = {
            k: float(v) for k, v in numeric.mean().items()
        }
        computed_stds = {
            k: max(float(v), 1e-8)
            for k, v in numeric.std(ddof=0).items()
        }
    else:
        computed_means = means
        computed_stds = stds

    numeric_norm = (numeric - pd.Series(computed_means)) / pd.Series(
        computed_stds
    )
    design = pd.concat(
        [cats.reset_index(drop=True), numeric_norm.reset_index(drop=True)],
        axis=1,
    )

    final_cols: list[str]
    if feature_cols is not None:
        design = design.reindex(columns=feature_cols, fill_value=0.0)
        final_cols = feature_cols
    else:
        final_cols = list(design.columns)

    return (
        design.values.astype(np.float32),
        computed_means,
        computed_stds,
        final_cols,
    )


def stratified_split(
    y: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_idx: list[int] = []
    val_idx: list[int] = []
    test_idx: list[int] = []
    for cls in np.unique(y):
        idx: list[int] = np.where(y == cls)[0].tolist()
        rng.shuffle(idx)
        n = len(idx)
        n_tr = max(1, int(round(n * 0.60)))
        n_va = max(1, int(round(n * 0.20)))
        n_te = n - n_tr - n_va
        if n_te < 1:
            n_va -= 1
            n_te = n - n_tr - n_va
        train_idx.extend(idx[:n_tr])
        val_idx.extend(idx[n_tr : n_tr + n_va])
        test_idx.extend(idx[n_tr + n_va :])
    rng.shuffle(train_idx)
    rng.shuffle(val_idx)
    rng.shuffle(test_idx)
    return (
        np.array(train_idx),
        np.array(val_idx),
        np.array(test_idx),
    )


# ── model architecture ─────────────────────────────────────────────────────

def build_model(input_dim: int, num_classes: int) -> tf.keras.Model:
    """
    Enterprise 4-layer MLP:
        Dense(256) -> BatchNorm -> Dropout(0.3)
        Dense(128) -> BatchNorm -> Dropout(0.2)
        Dense(64)  -> BatchNorm -> Dropout(0.1)
        Dense(32)
        Dense(num_classes, softmax)
    """
    inp = tf.keras.Input(shape=(input_dim,), name="alert_features")

    x = tf.keras.layers.Dense(256, activation="relu", name="dense_1")(inp)
    x = tf.keras.layers.BatchNormalization(name="bn_1")(x)
    x = tf.keras.layers.Dropout(0.3, name="dropout_1")(x)

    x = tf.keras.layers.Dense(128, activation="relu", name="dense_2")(x)
    x = tf.keras.layers.BatchNormalization(name="bn_2")(x)
    x = tf.keras.layers.Dropout(0.2, name="dropout_2")(x)

    x = tf.keras.layers.Dense(64, activation="relu", name="dense_3")(x)
    x = tf.keras.layers.BatchNormalization(name="bn_3")(x)
    x = tf.keras.layers.Dropout(0.1, name="dropout_3")(x)

    x = tf.keras.layers.Dense(32, activation="relu", name="dense_4")(x)
    out = tf.keras.layers.Dense(
        num_classes, activation="softmax", name="priority_probs"
    )(x)

    model = tf.keras.Model(
        inp, out, name="aegiscore_enterprise_alert_priority"
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


# ── evaluation helpers ─────────────────────────────────────────────────────

def confusion_matrix_counts(
    y_true: list[str], y_pred: list[str], labels: list[str]
) -> np.ndarray:
    label_idx = {lab: i for i, lab in enumerate(labels)}
    mat = np.zeros((len(labels), len(labels)), dtype=int)
    for true_lbl, pred_lbl in zip(y_true, y_pred):
        mat[label_idx[true_lbl], label_idx[pred_lbl]] += 1
    return mat


def per_class_accuracy(
    y_true: list[str], y_pred: list[str], labels: list[str]
) -> dict[str, Optional[float]]:
    result: dict[str, Optional[float]] = {}
    for lab in labels:
        indices = [i for i, t in enumerate(y_true) if t == lab]
        if indices:
            correct = sum(1 for i in indices if y_pred[i] == lab)
            result[lab] = round(correct / len(indices), 4)
        else:
            result[lab] = None
    return result


def classification_report_text(
    y_true: list[str], y_pred: list[str], labels: list[str]
) -> str:
    header = f"{'':12s} {'precision':>9} {'recall':>7} {'f1':>6} {'support':>8}"
    separator = "-" * 48
    lines = [header, separator]
    for lab in labels:
        tp = sum(
            1 for t, p in zip(y_true, y_pred) if t == lab and p == lab
        )
        fp = sum(
            1 for t, p in zip(y_true, y_pred) if t != lab and p == lab
        )
        fn = sum(
            1 for t, p in zip(y_true, y_pred) if t == lab and p != lab
        )
        support = tp + fn
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1_score = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        lines.append(
            f"{lab:12s} {precision:9.4f} {recall:7.4f}"
            f" {f1_score:6.4f} {support:8d}"
        )
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / max(
        len(y_true), 1
    )
    lines += [separator, f"{'accuracy':12s} {accuracy:9.4f}  total: {len(y_true)}"]
    return "\n".join(lines)


# ── main ───────────────────────────────────────────────────────────────────

def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    seed = int(os.getenv("AI_SEED", "42"))

    dataset_path = Path(
        os.getenv(
            "AI_DATASET_PATH",
            str(repo_root / "ai" / "datasets" / "alerts_dataset.csv"),
        )
    )
    model_out = Path(
        os.getenv(
            "AI_MODEL_PATH",
            str(
                repo_root
                / "ai"
                / "models"
                / "aegiscore-risk-priority-model.keras"
            ),
        )
    )
    metadata_out = Path(
        os.getenv(
            "AI_MODEL_METADATA_PATH",
            str(
                repo_root
                / "ai"
                / "models"
                / "aegiscore-risk-priority-model.metadata.json"
            ),
        )
    )
    eval_out = repo_root / "ai" / "models"
    model_version = os.getenv(
        "AI_MODEL_VERSION",
        datetime.now(timezone.utc).strftime("enterprise_model_%Y%m%d_%H%M%S"),
    )

    if not dataset_path.exists():
        print(f"[ERROR] Dataset not found: {dataset_path}")
        print("Run first:  python ai/datasets/generate_alerts_dataset.py")
        sys.exit(1)

    tf.random.set_seed(seed)
    np.random.seed(seed)

    # ── load and split ─────────────────────────────────────────────────────
    raw = pd.read_csv(dataset_path)
    frame = normalize_dataframe(raw)

    label_to_idx = {lab: i for i, lab in enumerate(CANONICAL_LABELS)}
    idx_to_label = {i: lab for lab, i in label_to_idx.items()}
    y_all = frame[LABEL_COLUMN].map(label_to_idx).to_numpy().astype(np.int32)

    tr_idx, va_idx, te_idx = stratified_split(y_all, seed)
    train_df = frame.iloc[tr_idx].reset_index(drop=True)
    val_df = frame.iloc[va_idx].reset_index(drop=True)
    test_df = frame.iloc[te_idx].reset_index(drop=True)

    x_train, means, stds, feat_cols = build_design_matrix(train_df)
    x_val, _, _, _ = build_design_matrix(val_df, means, stds, feat_cols)
    x_test, _, _, _ = build_design_matrix(test_df, means, stds, feat_cols)

    y_train = (
        train_df[LABEL_COLUMN].map(label_to_idx).to_numpy().astype(np.int32)
    )
    y_val = (
        val_df[LABEL_COLUMN].map(label_to_idx).to_numpy().astype(np.int32)
    )
    y_test = (
        test_df[LABEL_COLUMN].map(label_to_idx).to_numpy().astype(np.int32)
    )

    counts = Counter(y_train.tolist())
    total = sum(counts.values())
    class_weight = {
        idx: total / (len(counts) * cnt) for idx, cnt in counts.items()
    }

    # ── print header ───────────────────────────────────────────────────────
    print("=" * 65)
    print("  AegisCore Enterprise — Alert Priority Model Training")
    print("=" * 65)
    print(f"  Dataset      : {dataset_path.name}  ({len(frame):,} rows)")
    print(
        f"  Split        : {len(train_df):,} train"
        f" / {len(val_df):,} val"
        f" / {len(test_df):,} test"
    )
    print(f"  Features     : {x_train.shape[1]} input dimensions")
    print(
        "  Architecture : Dense(256)+BN+Drop(0.3)"
        " -> Dense(128)+BN+Drop(0.2)"
    )
    print(
        "               : -> Dense(64)+BN+Drop(0.1)"
        " -> Dense(32) -> Dense(4,softmax)"
    )
    print(f"  Classes      : {CANONICAL_LABELS}")
    weights_display = {
        CANONICAL_LABELS[k]: round(v, 2) for k, v in class_weight.items()
    }
    print(f"  Class weights: {weights_display}")
    print("  Max epochs   : 150  (EarlyStopping patience=20)")
    print()

    # ── train ──────────────────────────────────────────────────────────────
    model = build_model(int(x_train.shape[1]), len(CANONICAL_LABELS))

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=20,
            restore_best_weights=True,
            verbose=0,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=10,
            min_lr=1e-6,
            verbose=0,
        ),
    ]

    t0 = time.time()
    history = model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=150,
        batch_size=64,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=0,
    )
    elapsed = time.time() - t0
    epochs_trained = len(history.history["loss"])

    # ── evaluate ───────────────────────────────────────────────────────────
    train_eval = model.evaluate(x_train, y_train, verbose=0)
    val_eval = model.evaluate(x_val, y_val, verbose=0)
    test_eval = model.evaluate(x_test, y_test, verbose=0)

    train_acc = float(train_eval[1])
    val_acc = float(val_eval[1])
    test_acc = float(test_eval[1])

    raw_preds = model.predict(x_test, verbose=0)
    preds = np.argmax(raw_preds, axis=1)
    y_true_lbl = [idx_to_label[int(i)] for i in y_test]
    y_pred_lbl = [idx_to_label[int(i)] for i in preds]

    pc_acc = per_class_accuracy(y_true_lbl, y_pred_lbl, CANONICAL_LABELS)
    conf = confusion_matrix_counts(y_true_lbl, y_pred_lbl, CANONICAL_LABELS)
    report = classification_report_text(
        y_true_lbl, y_pred_lbl, CANONICAL_LABELS
    )

    # ── print results ──────────────────────────────────────────────────────
    print("=" * 65)
    print("  Training Complete")
    print("=" * 65)
    print(f"  Epochs trained  : {epochs_trained} / 150")
    print(f"  Training time   : {elapsed:.0f}s ({elapsed / 60:.1f} min)")
    print(f"  Train accuracy  : {train_acc:.1%}")
    print(f"  Val   accuracy  : {val_acc:.1%}")
    print(f"  Test  accuracy  : {test_acc:.1%}")
    print()
    print("  Per-class test accuracy:")
    for cls in CANONICAL_LABELS:
        acc = pc_acc.get(cls) or 0.0
        bar = "█" * int(acc * 20)
        print(f"    {cls:10s}: {bar:20s}  {acc:.1%}")
    print()
    print("  Confusion matrix (test set):")
    header_row = "".join(f"{lab:>10s}" for lab in CANONICAL_LABELS)
    print(f"    {'true/pred':12s}{header_row}")
    for row_i, true_lab in enumerate(CANONICAL_LABELS):
        row_vals = "".join(
            f"{conf[row_i, col_j]:>10d}"
            for col_j in range(len(CANONICAL_LABELS))
        )
        print(f"    {true_lab:12s}{row_vals}")
    print()
    print("  Classification report (test set):")
    for line in report.splitlines():
        print(f"    {line}")

    # ── save model ─────────────────────────────────────────────────────────
    model_out.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_out)

    class_dist = {
        "train": train_df[LABEL_COLUMN].value_counts().sort_index().to_dict(),
        "validation": val_df[LABEL_COLUMN]
        .value_counts()
        .sort_index()
        .to_dict(),
        "test": test_df[LABEL_COLUMN].value_counts().sort_index().to_dict(),
    }
    conf_dict = {
        CANONICAL_LABELS[row_i]: {
            CANONICAL_LABELS[col_j]: int(conf[row_i, col_j])
            for col_j in range(len(CANONICAL_LABELS))
        }
        for row_i in range(len(CANONICAL_LABELS))
    }
    metadata: dict = {
        "model_name": "aegiscore_enterprise_alert_prioritization_v2",
        "training_schema": TRAINING_SCHEMA,
        "model_version": model_version,
        "model_architecture": "MLP_4layer_BatchNorm_Enterprise",
        "layers": (
            "Dense(256)+BN+Drop(0.3)->Dense(128)+BN+Drop(0.2)"
            "->Dense(64)+BN+Drop(0.1)->Dense(32)->Dense(4,softmax)"
        ),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "framework": "tensorflow",
        "ml_framework": "tensorflow",
        "training_rows": int(len(train_df)),
        "validation_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "epochs_trained": epochs_trained,
        "training_time_seconds": round(elapsed, 1),
        "train_accuracy": round(train_acc, 6),
        "validation_accuracy": round(val_acc, 6),
        "test_accuracy": round(test_acc, 6),
        "per_class_test_accuracy": pc_acc,
        "label_classes": CANONICAL_LABELS,
        "label_to_index": label_to_idx,
        "feature_column_names": feat_cols,
        "numeric_columns": NUMERIC_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "numeric_means": means,
        "numeric_stds": stds,
        "class_distribution": class_dist,
        "confusion_matrix": conf_dict,
    }
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # ── save evaluation artifacts ──────────────────────────────────────────
    eval_out.mkdir(parents=True, exist_ok=True)
    cm_header = ",".join(["true/pred"] + CANONICAL_LABELS)
    cm_lines = [cm_header] + [
        ",".join(
            [CANONICAL_LABELS[row_i]]
            + [
                str(conf[row_i, col_j])
                for col_j in range(len(CANONICAL_LABELS))
            ]
        )
        for row_i in range(len(CANONICAL_LABELS))
    ]
    (eval_out / "alert_prioritization_confusion_matrix.csv").write_text(
        "\n".join(cm_lines) + "\n", encoding="utf-8"
    )
    (eval_out / "alert_prioritization_classification_report.txt").write_text(
        report + "\n", encoding="utf-8"
    )

    print()
    print(f"  Model saved    : {model_out}")
    print(f"  Metadata saved : {metadata_out}")
    print(f"  Eval artifacts : {eval_out}")
    print()


if __name__ == "__main__":
    main()