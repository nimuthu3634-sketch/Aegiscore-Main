import enum


class RoleName(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"


class DetectionType(str, enum.Enum):
    """Academic MVP threat scope (canonical iteration order matches public documentation).

    The current academic MVP validates four core threat categories: brute-force attacks,
    port scans, file integrity violations, and unauthorized user account creation.
    Additional detection families are roadmap-only beyond this implementation.
    """

    BRUTE_FORCE = "brute_force"
    PORT_SCAN = "port_scan"
    FILE_INTEGRITY_VIOLATION = "file_integrity_violation"
    UNAUTHORIZED_USER_CREATION = "unauthorized_user_creation"


class AssetCriticality(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class IncidentStatus(str, enum.Enum):
    NEW = "new"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class IncidentPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseStatus(str, enum.Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WARNING = "warning"
    FAILED = "failed"


class ResponseMode(str, enum.Enum):
    DRY_RUN = "dry-run"
    LIVE = "live"


class ResponseActionType(str, enum.Enum):
    BLOCK_IP = "block_ip"
    DISABLE_USER = "disable_user"
    QUARANTINE_HOST_FLAG = "quarantine_host_flag"
    CREATE_MANUAL_REVIEW = "create_manual_review"
    NOTIFY_ADMIN = "notify_admin"


class ResponsePolicyTarget(str, enum.Enum):
    ALERT = "alert"
    INCIDENT = "incident"


class NoteTargetType(str, enum.Enum):
    ALERT = "alert"
    INCIDENT = "incident"


class ScoreMethod(str, enum.Enum):
    BASELINE_RULES = "baseline_rules"
    # Historical DB/API string only — no scikit-learn inference in this codebase.
    SKLEARN_MODEL = "sklearn_model"
    TENSORFLOW_MODEL = "tensorflow_model"


def enum_values(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]
