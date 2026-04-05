from __future__ import annotations

import numpy as np
import pandas as pd

ALLOWED_DETECTIONS = {
    "brute_force": 0.75,
    "file_integrity_violation": 0.85,
    "port_scan": 0.45,
    "unauthorized_user_creation": 0.95,
}


def score_alerts(alerts: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(alerts)
    if frame.empty:
        return pd.DataFrame(columns=["detection_type", "severity", "risk_score"])

    frame["detection_type"] = frame["detection_type"].astype(str)
    invalid_detections = set(frame["detection_type"]) - set(ALLOWED_DETECTIONS)
    if invalid_detections:
        raise ValueError(
            f"Unsupported detections requested: {', '.join(sorted(invalid_detections))}"
        )

    frame["severity"] = pd.to_numeric(frame["severity"], errors="coerce").fillna(0)
    frame["detection_weight"] = frame["detection_type"].map(ALLOWED_DETECTIONS)
    frame["risk_score"] = np.clip(
        (frame["severity"] / 10.0) * 0.4 + frame["detection_weight"] * 0.6,
        0,
        1,
    )

    return frame[["detection_type", "severity", "risk_score"]]
