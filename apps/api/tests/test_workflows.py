from fastapi import HTTPException

from app.models.enums import IncidentStatus
from app.schemas.workflows import IncidentTransitionAction
from app.services.workflows import (
    get_allowed_incident_target_states,
    get_available_incident_actions,
    resolve_incident_transition,
)


def test_incident_transition_rules_allow_expected_progression() -> None:
    assert resolve_incident_transition(
        IncidentStatus.NEW,
        IncidentTransitionAction.TRIAGE,
    ) == IncidentStatus.TRIAGED
    assert resolve_incident_transition(
        IncidentStatus.TRIAGED,
        IncidentTransitionAction.CONTAIN,
    ) == IncidentStatus.CONTAINED
    assert resolve_incident_transition(
        IncidentStatus.CONTAINED,
        IncidentTransitionAction.RESOLVE,
    ) == IncidentStatus.RESOLVED


def test_incident_transition_rules_reject_invalid_transition() -> None:
    try:
        resolve_incident_transition(
            IncidentStatus.NEW,
            IncidentTransitionAction.CONTAIN,
        )
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "contain" in exc.detail
    else:
        raise AssertionError("Expected invalid transition to raise HTTPException")


def test_incident_transition_capabilities_match_workflow_map() -> None:
    assert get_available_incident_actions(IncidentStatus.INVESTIGATING) == [
        "contain",
        "resolve",
        "mark_false_positive",
    ]
    assert get_allowed_incident_target_states(IncidentStatus.TRIAGED) == [
        IncidentStatus.INVESTIGATING,
        IncidentStatus.CONTAINED,
        IncidentStatus.RESOLVED,
        IncidentStatus.FALSE_POSITIVE,
    ]
