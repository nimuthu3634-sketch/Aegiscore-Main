from fastapi import HTTPException
from pydantic import ValidationError

from app.models.enums import IncidentStatus
from app.schemas.workflows import AlertLinkIncidentRequest, IncidentTransitionAction
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


def test_alert_link_incident_request_requires_explicit_mode() -> None:
    try:
        AlertLinkIncidentRequest()
    except ValidationError as exc:
        assert "incident_id" in str(exc) or "create_new" in str(exc)
    else:
        raise AssertionError("Expected invalid alert link request to fail validation")


def test_alert_link_incident_request_rejects_mixed_modes() -> None:
    try:
        AlertLinkIncidentRequest(
            incident_id="2ef3a70c-2bf8-4c92-bd71-e6e37f0cbb0c",
            create_new=True,
        )
    except ValidationError as exc:
        assert "not both" in str(exc)
    else:
        raise AssertionError("Expected mixed incident link modes to fail validation")


def test_alert_link_incident_request_accepts_existing_or_new_modes() -> None:
    existing = AlertLinkIncidentRequest(
        incident_id="2ef3a70c-2bf8-4c92-bd71-e6e37f0cbb0c",
    )
    creating = AlertLinkIncidentRequest(
        create_new=True,
        title="External reconnaissance incident",
    )

    assert existing.incident_id is not None
    assert existing.create_new is False
    assert creating.create_new is True
