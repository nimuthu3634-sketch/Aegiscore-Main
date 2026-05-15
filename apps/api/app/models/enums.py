import enum


# User roles used for access control in the system.
class RoleName(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"


class DetectionType(str, enum.Enum):
    """Academic MVP threat scope.

    These are the main attack types supported by our AegisCore project.
    """

    BRUTE_FORCE = "brute_force"
    PORT_SCAN = "port_scan"
    FILE_INTEGRITY_VIOLATION = "file_integrity_violation"
    UNAUTHORIZED_USER_CREATION = "unauthorized_user_creation"


# Shows how important an asset is for the organisation.
class AssetCriticality(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Status values used to track the alert lifecycle.
class AlertStatus(str, enum.Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


# Status values used to track the incident investigation workflow.
class IncidentStatus(str, enum.Enum):
    NEW = "new"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


# Priority levels assigned to incidents based on their risk.
class IncidentPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Execution status for automated or manual response actions.
class ResponseStatus(str, enum.Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WARNING = "warning"
    FAILED = "failed"


# Response mode decides whether actions are only simulated or actually executed.
class ResponseMode(str, enum.Enum):
    DRY_RUN = "dry-run"
    LIVE = "live"


# Types of response actions supported by the SOC platform.
class ResponseActionType(str, enum.Enum):
    BLOCK_IP = "block_ip"
    DISABLE_USER = "disable_user"
    QUARANTINE_HOST_FLAG = "quarantine_host_flag"
    CREATE_MANUAL_REVIEW = "create_manual_review"
    NOTIFY_ADMIN = "notify_admin"


# Response policies can be applied either to alerts or incidents.
class ResponsePolicyTarget(str, enum.Enum):
    ALERT = "alert"
    INCIDENT = "incident"


# Analyst notes can be attached to either alerts or incidents.
class NoteTargetType(str, enum.Enum):
    ALERT = "alert"
    INCIDENT = "incident"


# Identifies which method was used to calculate the risk score.
class ScoreMethod(str, enum.Enum):
    BASELINE_RULES = "baseline_rules"

    # Kept for old database/API compatibility, but this project does not run scikit-learn inference.
    SKLEARN_MODEL = "sklearn_model"

    TENSORFLOW_MODEL = "tensorflow_model"


def enum_values(enum_class: type[enum.Enum]) -> list[str]:
    # Helps SQLAlchemy store enum values as strings in the database.
    return [member.value for member in enum_class]