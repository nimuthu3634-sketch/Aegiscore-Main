from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import incidents as incidents_route
from app.db.session import get_db_session
from app.main import app
from app.models.enums import (
    AlertStatus,
    AssetCriticality,
    DetectionType,
    IncidentPriority,
    IncidentStatus,
    ResponseStatus,
    RoleName,
)
from app.schemas.alerts import AlertSeverityLabel
from app.schemas.common import (
    ActivityEntryResponse,
    AnalystNoteResponse,
    AssetSummaryResponse,
    ResponseActionDetailResponse,
    RoleResponse,
    UserBriefResponse,
)
from app.schemas.incidents import (
    IncidentDetailResponse,
    IncidentGroupedEvidenceResponse,
    IncidentLinkedAlertResponse,
    IncidentPriorityExplanationResponse,
    IncidentStateTransitionCapabilitiesResponse,
)
from app.schemas.workflows import (
    AnalystNoteCreateResponse,
    IncidentTransitionResponse,
)


def _override_dependencies() -> None:
    app.dependency_overrides[deps.get_current_user] = lambda: object()
    app.dependency_overrides[get_db_session] = lambda: None


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def _sample_incident_detail() -> IncidentDetailResponse:
    role = RoleResponse(id=uuid4(), name=RoleName.ANALYST)
    analyst = UserBriefResponse(
        id=uuid4(),
        username="analyst",
        full_name="AegisCore Analyst",
        role=role,
    )
    primary_asset = AssetSummaryResponse(
        id=uuid4(),
        hostname="acct-db-01",
        ip_address="10.20.1.20",
        operating_system="PostgreSQL Appliance",
        criticality=AssetCriticality.CRITICAL,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    return IncidentDetailResponse(
        id=uuid4(),
        title="File integrity drift on protected configuration",
        summary="Configuration drift on a critical system is under active investigation.",
        priority=IncidentPriority.HIGH,
        state=IncidentStatus.INVESTIGATING,
        assignee=analyst,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        primary_asset=primary_asset,
        affected_assets=[primary_asset],
        linked_alerts=[
            IncidentLinkedAlertResponse(
                id=uuid4(),
                title="Protected configuration file changed",
                detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
                source_type="Wazuh",
                severity=AlertSeverityLabel.HIGH,
                status=AlertStatus.INVESTIGATING,
                risk_score=88,
                timestamp=datetime.now(UTC),
                asset_hostname="acct-db-01",
                source_ip=None,
                destination_ip=None,
                destination_port=None,
                username=None,
            )
        ],
        grouped_evidence=IncidentGroupedEvidenceResponse(
            summary="Correlation is currently grouped around the primary normalized alert and linked workflow evidence.",
            evidence_items=["Primary asset: acct-db-01"],
            correlation_keys={"detection_type": "file_integrity_violation"},
        ),
        response_history=[
            ResponseActionDetailResponse(
                id=uuid4(),
                action_type="collect_configuration_backup",
                status=ResponseStatus.IN_PROGRESS,
                target="/etc/nginx/nginx.conf",
                mode="dry-run",
                result_summary="snapshot_requested",
                details={"path": "/etc/nginx/nginx.conf", "result": "snapshot_requested"},
                created_at=datetime.now(UTC),
                executed_at=None,
                requested_by=analyst,
            )
        ],
        analyst_notes=[
            AnalystNoteResponse(
                id="note-1",
                author=analyst,
                content="Waiting on backup snapshot for diff analysis.",
                created_at=datetime.now(UTC),
            )
        ],
        timeline=[
            ActivityEntryResponse(
                id="timeline-1",
                timestamp=datetime.now(UTC),
                category="incident",
                title="Incident Created",
                description="Incident opened from normalized file integrity alert.",
                actor=analyst,
                details={"state": "investigating"},
            )
        ],
        priority_explanation=IncidentPriorityExplanationResponse(
            label="Incident priority explanation",
            summary="Incident is currently prioritized high based on the primary alert, asset context, and linked workflow evidence.",
            rationale="Configuration drift on a critical system is under active investigation.",
            factors=["Primary asset criticality: critical"],
        ),
        state_transition_capabilities=IncidentStateTransitionCapabilitiesResponse(
            current_state=IncidentStatus.INVESTIGATING,
            available_actions=["contain", "resolve", "mark_false_positive"],
            allowed_target_states=[
                IncidentStatus.CONTAINED,
                IncidentStatus.RESOLVED,
                IncidentStatus.FALSE_POSITIVE,
            ],
        ),
    )


def test_incident_detail_route_returns_rich_payload(monkeypatch) -> None:
    detail = _sample_incident_detail()
    _override_dependencies()
    monkeypatch.setattr(incidents_route, "get_incident", lambda db, incident_id: detail)

    try:
        client = TestClient(app)
        response = client.get(f"/incidents/{detail.id}")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(detail.id)
    assert payload["grouped_evidence"]["correlation_keys"]["detection_type"] == "file_integrity_violation"
    assert payload["response_history"][0]["action_type"] == "collect_configuration_backup"
    assert payload["state_transition_capabilities"]["available_actions"][0] == "contain"


def test_incident_detail_route_returns_not_found(monkeypatch) -> None:
    _override_dependencies()

    def raise_not_found(db, incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")

    monkeypatch.setattr(incidents_route, "get_incident", raise_not_found)

    try:
        client = TestClient(app)
        response = client.get(f"/incidents/{uuid4()}")
    finally:
        _clear_overrides()

    assert response.status_code == 404
    assert response.json() == {"detail": "Incident not found"}


def test_incident_transition_route_returns_summary(monkeypatch) -> None:
    response_payload = IncidentTransitionResponse(
        incident_id=uuid4(),
        previous_state=IncidentStatus.TRIAGED,
        current_state=IncidentStatus.INVESTIGATING,
        message="Incident transitioned to investigating.",
    )
    _override_dependencies()
    monkeypatch.setattr(
        incidents_route,
        "transition_incident",
        lambda db, incident_id, payload, current_user: response_payload,
    )

    try:
        client = TestClient(app)
        response = client.post(
            f"/incidents/{response_payload.incident_id}/transition",
            json={"action": "investigate"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["current_state"] == "investigating"


def test_incident_transition_route_returns_invalid_transition(monkeypatch) -> None:
    _override_dependencies()

    def raise_conflict(db, incident_id, payload, current_user):
        raise HTTPException(
            status_code=409,
            detail="Incident cannot transition via 'contain' from state 'new'.",
        )

    monkeypatch.setattr(incidents_route, "transition_incident", raise_conflict)

    try:
        client = TestClient(app)
        response = client.post(
            f"/incidents/{uuid4()}/transition",
            json={"action": "contain"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 409
    assert "cannot transition" in response.json()["detail"]


def test_incident_note_route_returns_created_note(monkeypatch) -> None:
    role = RoleResponse(id=uuid4(), name=RoleName.ANALYST)
    analyst = UserBriefResponse(
        id=uuid4(),
        username="analyst",
        full_name="AegisCore Analyst",
        role=role,
    )
    response_payload = AnalystNoteCreateResponse(
        note=AnalystNoteResponse(
            id="note-2",
            author=analyst,
            content="Escalated after confirming endpoint owner.",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        message="Incident note saved successfully.",
    )
    _override_dependencies()
    monkeypatch.setattr(
        incidents_route,
        "create_incident_note",
        lambda db, incident_id, content, current_user: response_payload,
    )

    try:
        client = TestClient(app)
        response = client.post(
            f"/incidents/{uuid4()}/notes",
            json={"content": "Escalated after confirming endpoint owner."},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["note"]["content"].startswith("Escalated")
