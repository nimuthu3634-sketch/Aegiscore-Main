import enum
from uuid import UUID

from pydantic import Field, model_validator

from app.models.enums import IncidentPriority, IncidentStatus
from app.schemas.base import APIModel
from app.schemas.common import AnalystNoteResponse


# Actions supported for changing an incident's workflow state.
class IncidentTransitionAction(str, enum.Enum):
    TRIAGE = "triage"
    INVESTIGATE = "investigate"
    CONTAIN = "contain"
    RESOLVE = "resolve"
    MARK_FALSE_POSITIVE = "mark_false_positive"


# Request body used when an analyst adds a note.
class AnalystNoteCreateRequest(APIModel):
    content: str = Field(min_length=1, max_length=4000)


# Request body used when linking an alert to an existing or new incident.
class AlertLinkIncidentRequest(APIModel):
    incident_id: UUID | None = None
    create_new: bool = False
    title: str | None = Field(default=None, min_length=1, max_length=255)
    summary: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_link_mode(self) -> "AlertLinkIncidentRequest":
        # Makes sure the user chooses only one linking method.
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


# Response returned after an alert is linked to an incident.
class AlertLinkIncidentResponse(APIModel):
    incident_id: UUID
    title: str
    state: IncidentStatus
    priority: IncidentPriority
    linked_alerts_count: int
    message: str


# Response returned after an alert status is changed.
class AlertLifecycleResponse(APIModel):
    alert_id: UUID
    previous_status: str
    current_status: str
    linked_incident_id: UUID | None = None
    message: str


# Request body used when changing an incident state.
class IncidentTransitionRequest(APIModel):
    action: IncidentTransitionAction


# Response returned after an incident state change is completed.
class IncidentTransitionResponse(APIModel):
    incident_id: UUID
    previous_state: IncidentStatus
    current_state: IncidentStatus
    message: str


# Response returned after a note is created successfully.
class AnalystNoteCreateResponse(APIModel):
    note: AnalystNoteResponse
    message: str