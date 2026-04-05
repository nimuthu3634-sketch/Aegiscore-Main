from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import alerts as alerts_route
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
from app.schemas.alerts import (
    AlertDetailResponse,
    AlertLinkedIncidentResponse,
    AlertScoreExplanationResponse,
    AlertSeverityLabel,
    AlertSourceRuleResponse,
)
from app.schemas.common import (
    ActivityEntryResponse,
    AnalystNoteResponse,
    AssetSummaryResponse,
    ResponseActionDetailResponse,
    RoleResponse,
    UserBriefResponse,
)
from app.schemas.workflows import (
    AlertLifecycleResponse,
    AlertLinkIncidentResponse,
    AnalystNoteCreateResponse,
)


def _override_dependencies() -> None:
    app.dependency_overrides[deps.get_current_user] = lambda: object()
    app.dependency_overrides[get_db_session] = lambda: None


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def _sample_alert_detail() -> AlertDetailResponse:
    role = RoleResponse(id=uuid4(), name=RoleName.ANALYST)
    analyst = UserBriefResponse(
        id=uuid4(),
        username="analyst",
        full_name="AegisCore Analyst",
        role=role,
    )
    return AlertDetailResponse(
        id=uuid4(),
        title="Unauthorized user creation detected",
        description="A privileged local account was created outside approved windows.",
        detection_type=DetectionType.UNAUTHORIZED_USER_CREATION,
        source_type="Wazuh",
        severity=AlertSeverityLabel.CRITICAL,
        severity_score=9,
        status=AlertStatus.INVESTIGATING,
        status_label="investigating",
        risk_score=96,
        risk_confidence=0.92,
        priority_label=AlertSeverityLabel.CRITICAL,
        linked_incident=AlertLinkedIncidentResponse(
            id=uuid4(),
            title="Unauthorized directory account creation",
            status=IncidentStatus.INVESTIGATING,
            priority=IncidentPriority.CRITICAL,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            assigned_user=analyst,
        ),
        asset=AssetSummaryResponse(
            id=uuid4(),
            hostname="acct-windows-01",
            ip_address="10.20.1.35",
            operating_system="Windows Server 2022",
            criticality=AssetCriticality.MEDIUM,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        source_ip="10.20.1.35",
        destination_ip=None,
        destination_port=389,
        username="svc-shadow",
        timestamp=datetime.now(UTC),
        source_rule=AlertSourceRuleResponse(
            rule_id="60115",
            name="Unauthorized local user created",
            provider="Wazuh",
            metadata={"agent": "acct-windows-01"},
        ),
        normalized_details={"username": "svc-shadow", "asset_hostname": "acct-windows-01"},
        raw_payload={"rule_id": 60115, "new_user": "svc-shadow"},
        score_explanation=AlertScoreExplanationResponse(
            label="Alert risk explanation",
            summary="Alert is currently scored critical based on normalized telemetry and asset context.",
            rationale="High-confidence admin account creation on a monitored server.",
            factors=["Detection type: unauthorized_user_creation"],
            confidence=0.92,
        ),
        related_responses=[
            ResponseActionDetailResponse(
                id=uuid4(),
                action_type="disable_user_account",
                status=ResponseStatus.COMPLETED,
                target="svc-shadow",
                mode="live",
                result_summary="disabled",
                details={"username": "svc-shadow", "result": "disabled"},
                created_at=datetime.now(UTC),
                executed_at=datetime.now(UTC),
                requested_by=analyst,
            )
        ],
        analyst_notes=[
            AnalystNoteResponse(
                id="note-1",
                author=analyst,
                content="Escalated to identity review.",
                created_at=datetime.now(UTC),
            )
        ],
        audit_history=[
            ActivityEntryResponse(
                id="audit-1",
                timestamp=datetime.now(UTC),
                category="incident",
                title="Incident Created",
                description="Initial incident created from alert correlation.",
                actor=analyst,
                details={"priority": "critical"},
            )
        ],
    )


def test_alert_detail_route_returns_rich_payload(monkeypatch) -> None:
    detail = _sample_alert_detail()
    _override_dependencies()
    monkeypatch.setattr(alerts_route, "get_alert_detail", lambda db, alert_id: detail)

    try:
        client = TestClient(app)
        response = client.get(f"/alerts/{detail.id}")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(detail.id)
    assert payload["linked_incident"]["priority"] == "critical"
    assert payload["related_responses"][0]["action_type"] == "disable_user_account"
    assert payload["source_rule"]["rule_id"] == "60115"


def test_alert_detail_route_returns_not_found(monkeypatch) -> None:
    _override_dependencies()

    def raise_not_found(db, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")

    monkeypatch.setattr(alerts_route, "get_alert_detail", raise_not_found)

    try:
        client = TestClient(app)
        response = client.get(f"/alerts/{uuid4()}")
    finally:
        _clear_overrides()

    assert response.status_code == 404
    assert response.json() == {"detail": "Alert not found"}


def test_alert_acknowledge_route_returns_lifecycle_response(monkeypatch) -> None:
    response_payload = AlertLifecycleResponse(
        alert_id=uuid4(),
        previous_status="new",
        current_status="investigating",
        linked_incident_id=None,
        message="Alert acknowledged and moved into investigation.",
    )
    _override_dependencies()
    monkeypatch.setattr(
        alerts_route,
        "acknowledge_alert",
        lambda db, alert_id, current_user: response_payload,
    )

    try:
        client = TestClient(app)
        response = client.post(f"/alerts/{response_payload.alert_id}/acknowledge")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["current_status"] == "investigating"


def test_alert_link_incident_route_returns_summary(monkeypatch) -> None:
    response_payload = AlertLinkIncidentResponse(
        incident_id=uuid4(),
        title="Unauthorized directory account creation",
        state=IncidentStatus.TRIAGED,
        priority=IncidentPriority.CRITICAL,
        message="Alert linked into a new incident.",
    )
    _override_dependencies()
    monkeypatch.setattr(
        alerts_route,
        "link_alert_incident",
        lambda db, alert_id, current_user: response_payload,
    )

    try:
        client = TestClient(app)
        response = client.post(f"/alerts/{uuid4()}/link-incident")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["state"] == "triaged"


def test_alert_note_route_returns_created_note(monkeypatch) -> None:
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
            content="Validated alert context before escalation.",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        message="Alert note saved successfully.",
    )
    _override_dependencies()
    monkeypatch.setattr(
        alerts_route,
        "create_alert_note",
        lambda db, alert_id, content, current_user: response_payload,
    )

    try:
        client = TestClient(app)
        response = client.post(
            f"/alerts/{uuid4()}/notes",
            json={"content": "Validated alert context before escalation."},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["note"]["content"].startswith("Validated")
