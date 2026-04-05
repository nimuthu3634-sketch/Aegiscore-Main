from fastapi import HTTPException, status

from app.models.enums import IncidentStatus
from app.schemas.workflows import IncidentTransitionAction

INCIDENT_ACTION_TARGETS: dict[IncidentTransitionAction, IncidentStatus] = {
    IncidentTransitionAction.TRIAGE: IncidentStatus.TRIAGED,
    IncidentTransitionAction.INVESTIGATE: IncidentStatus.INVESTIGATING,
    IncidentTransitionAction.CONTAIN: IncidentStatus.CONTAINED,
    IncidentTransitionAction.RESOLVE: IncidentStatus.RESOLVED,
    IncidentTransitionAction.MARK_FALSE_POSITIVE: IncidentStatus.FALSE_POSITIVE,
}

INCIDENT_TRANSITION_RULES: dict[
    IncidentStatus, tuple[IncidentTransitionAction, ...]
] = {
    IncidentStatus.NEW: (
        IncidentTransitionAction.TRIAGE,
        IncidentTransitionAction.INVESTIGATE,
        IncidentTransitionAction.MARK_FALSE_POSITIVE,
    ),
    IncidentStatus.TRIAGED: (
        IncidentTransitionAction.INVESTIGATE,
        IncidentTransitionAction.CONTAIN,
        IncidentTransitionAction.RESOLVE,
        IncidentTransitionAction.MARK_FALSE_POSITIVE,
    ),
    IncidentStatus.INVESTIGATING: (
        IncidentTransitionAction.CONTAIN,
        IncidentTransitionAction.RESOLVE,
        IncidentTransitionAction.MARK_FALSE_POSITIVE,
    ),
    IncidentStatus.CONTAINED: (
        IncidentTransitionAction.INVESTIGATE,
        IncidentTransitionAction.RESOLVE,
        IncidentTransitionAction.MARK_FALSE_POSITIVE,
    ),
    IncidentStatus.RESOLVED: (),
    IncidentStatus.FALSE_POSITIVE: (),
}


def get_available_incident_actions(
    current_state: IncidentStatus,
) -> list[str]:
    return [action.value for action in INCIDENT_TRANSITION_RULES[current_state]]


def get_allowed_incident_target_states(
    current_state: IncidentStatus,
) -> list[IncidentStatus]:
    return [
        INCIDENT_ACTION_TARGETS[action]
        for action in INCIDENT_TRANSITION_RULES[current_state]
    ]


def resolve_incident_transition(
    current_state: IncidentStatus,
    action: IncidentTransitionAction,
) -> IncidentStatus:
    if action not in INCIDENT_TRANSITION_RULES[current_state]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Incident cannot transition via '{action.value}' from "
                f"state '{current_state.value}'."
            ),
        )

    return INCIDENT_ACTION_TARGETS[action]
