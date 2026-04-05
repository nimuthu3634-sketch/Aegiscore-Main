import enum
from uuid import UUID

from pydantic import Field

from app.models.enums import IncidentPriority, IncidentStatus
from app.schemas.base import APIModel
from app.schemas.common import AnalystNoteResponse


class IncidentTransitionAction(str, enum.Enum):
    TRIAGE = "triage"
    INVESTIGATE = "investigate"
    CONTAIN = "contain"
    RESOLVE = "resolve"
    MARK_FALSE_POSITIVE = "mark_false_positive"


class AnalystNoteCreateRequest(APIModel):
    content: str = Field(min_length=1, max_length=4000)


class AlertLinkIncidentResponse(APIModel):
    incident_id: UUID
    title: str
    state: IncidentStatus
    priority: IncidentPriority
    message: str


class AlertLifecycleResponse(APIModel):
    alert_id: UUID
    previous_status: str
    current_status: str
    linked_incident_id: UUID | None = None
    message: str


class IncidentTransitionRequest(APIModel):
    action: IncidentTransitionAction


class IncidentTransitionResponse(APIModel):
    incident_id: UUID
    previous_state: IncidentStatus
    current_state: IncidentStatus
    message: str


class AnalystNoteCreateResponse(APIModel):
    note: AnalystNoteResponse
    message: str
