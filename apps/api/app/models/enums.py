import enum


class DetectionType(str, enum.Enum):
    BRUTE_FORCE = "brute_force"
    FILE_INTEGRITY_VIOLATION = "file_integrity_violation"
    PORT_SCAN = "port_scan"
    UNAUTHORIZED_USER_CREATION = "unauthorized_user_creation"


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class ResponseStatus(str, enum.Enum):
    QUEUED = "queued"
    COMPLETED = "completed"
    FAILED = "failed"

