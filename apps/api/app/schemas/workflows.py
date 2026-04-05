import enum
from uuid import UUID

from pydantic import Field, model_validator

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


class AlertLinkIncidentRequest(APIModel):
    incident_id: UUID | None = None
    create_new: bool = False
    title: str | None = Field(default=None, min_length=1, max_length=255)
    summary: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_link_mode(self) -> "AlertLinkIncidentRequest":
        if self.incident_id and self.create_new:
            raise ValueError(
                "Provide either incident_id or create_new, but not both."
            )

        if not self.incident_id and not self.create_new:
            raise ValueError(
                "Provide incident_id to link an existing incident or set create_new=true."
            )

        if not self.create_new and (self.title is not None or self.summary is not None):
            raise ValueError(
                "New incident title or summary can only be provided when create_new=true."
            )

        return self


class AlertLinkIncidentResponse(APIModel):
    incident_id: UUID
    title: str
    state: IncidentStatus
    priority: IncidentPriority
    linked_alerts_count: int
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
