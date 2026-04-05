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
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


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


def enum_values(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]
