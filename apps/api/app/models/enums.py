import enum


class RoleName(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"


class DetectionType(str, enum.Enum):
    BRUTE_FORCE = "brute_force"
    FILE_INTEGRITY_VIOLATION = "file_integrity_violation"
    PORT_SCAN = "port_scan"
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
    FAILED = "failed"


class ResponseMode(str, enum.Enum):
    DRY_RUN = "dry-run"
    LIVE = "live"


class NoteTargetType(str, enum.Enum):
    ALERT = "alert"
    INCIDENT = "incident"


class ScoreMethod(str, enum.Enum):
    BASELINE_RULES = "baseline_rules"
    SKLEARN_MODEL = "sklearn_model"


def enum_values(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]
