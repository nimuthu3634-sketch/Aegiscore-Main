"""Scoring constants: baseline weights, priority thresholds, and feature bundles.

``ALERT_PRIORITY_ANCHORS`` supports the **3-class** TensorFlow alert prioritization model.
``MODEL_*`` / ``RISK_PRIORITY_ANCHORS`` support the **legacy** small fixture schema only
(see :data:`LEGACY_TRAINING_SCHEMA` in ``ml.py``) — not the primary product path.
"""

from app.models.enums import IncidentPriority

MAX_RISK_SCORE = 100
MIN_RISK_SCORE = 0

PRIORITY_THRESHOLDS: tuple[tuple[int, IncidentPriority], ...] = (
    (85, IncidentPriority.CRITICAL),
    (70, IncidentPriority.HIGH),
    (45, IncidentPriority.MEDIUM),
    (0, IncidentPriority.LOW),
)

DETECTION_TYPE_WEIGHTS: dict[str, int] = {
    "unauthorized_user_creation": 28,
    "file_integrity_violation": 24,
    "brute_force": 18,
    "port_scan": 12,
}

SOURCE_TYPE_WEIGHTS: dict[str, int] = {
    "wazuh": 6,
    "suricata": 3,
}

ASSET_CRITICALITY_WEIGHTS: dict[str, int] = {
    "critical": 18,
    "high": 12,
    "medium": 6,
    "low": 0,
    "unknown": 4,
}

SENSITIVE_PORTS = {22, 3389, 3306, 5432, 5985, 5986}
SENSITIVE_FILE_PATTERNS = (
    "/etc/",
    "/root/",
    "/home/",
    "/var/lib/",
    "/opt/",
    ".ssh/",
    "authorized_keys",
    "shadow",
    "passwd",
    "sudoers",
    "nginx.conf",
)
PRIVILEGED_ACCOUNT_MARKERS = (
    "root",
    "admin",
    "administrator",
    "svc",
    "service",
    "backup",
    "sec",
    "ops",
)

RISK_PRIORITY_ANCHORS: dict[str, int] = {
    IncidentPriority.LOW.value: 25,
    IncidentPriority.MEDIUM.value: 55,
    IncidentPriority.HIGH.value: 78,
    IncidentPriority.CRITICAL.value: 93,
}

# 3-class TensorFlow alert prioritization model (no CRITICAL class in softmax).
ALERT_PRIORITY_ANCHORS: dict[str, int] = {
    IncidentPriority.LOW.value: 25,
    IncidentPriority.MEDIUM.value: 55,
    IncidentPriority.HIGH.value: 80,
    IncidentPriority.CRITICAL.value: 95,
}

# LEGACY: `risk_training_fixture.csv` TensorFlow path (MODEL_* schema); tests / optional lab only.
MODEL_CATEGORICAL_FEATURES = [
    "source_type",
    "detection_type",
    "asset_criticality",
]

MODEL_NUMERIC_FEATURES = [
    "source_severity",
    "source_rule_level",
    "repeated_event_count",
    "time_window_density",
    "repeated_source_ip",
    "repeated_failed_logins",
    "recurrence_history",
    "destination_port",
    "has_destination_port",
    "privileged_account_flag",
    "sensitive_file_flag",
]

MODEL_FEATURE_COLUMNS = MODEL_CATEGORICAL_FEATURES + MODEL_NUMERIC_FEATURES

# LEGACY alias bundle (same as MODEL_*); kept for documentation grep-ability.
LEGACY_MODEL_FEATURE_COLUMNS = MODEL_FEATURE_COLUMNS

# Feature extraction for TensorFlow alert prioritization (UTC business hours, simple heuristic).
SCORING_BUSINESS_HOUR_START_UTC = 8
SCORING_BUSINESS_HOUR_END_UTC = 18
SCORING_BLACKLISTED_IP_REPEAT_THRESHOLD = 3

INTEGRITY_CRITICAL_PATH_MARKERS = (
    "shadow",
    "passwd",
    "sudoers",
    "authorized_keys",
    ".ssh/",
)
