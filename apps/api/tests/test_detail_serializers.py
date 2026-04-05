from datetime import UTC, datetime
from uuid import uuid4

from app.models.analyst_note import AnalystNote
from app.models.asset import Asset
from app.models.audit_log import AuditLog
from app.models.enums import (
    AlertStatus,
    AssetCriticality,
    DetectionType,
    IncidentPriority,
    IncidentStatus,
    NoteTargetType,
    ResponseMode,
    ResponseStatus,
    RoleName,
)
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.response_action import ResponseAction
from app.models.risk_score import RiskScore
from app.models.role import Role
from app.models.user import User
from app.services.serializers import (
    to_alert_detail_response,
    to_incident_detail_response,
)


def _build_fixture() -> tuple[NormalizedAlert, Incident, list[AuditLog], list[AnalystNote]]:
    role = Role(
        id=uuid4(),
        name=RoleName.ANALYST,
        description="Analyst role",
        created_at=datetime.now(UTC),
    )
    analyst = User(
        id=uuid4(),
        role=role,
        username="analyst",
        password_hash="hashed",
        full_name="AegisCore Analyst",
        is_active=True,
        created_at=datetime.now(UTC),
    )
    asset = Asset(
        id=uuid4(),
        hostname="acct-db-01",
        ip_address="10.20.1.20",
        operating_system="PostgreSQL Appliance",
        criticality=AssetCriticality.CRITICAL,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    raw_alert = RawAlert(
        id=uuid4(),
        asset=asset,
        source="wazuh",
        external_id="wazuh-8421",
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        severity=8,
        raw_payload={
            "rule_id": 60115,
            "signature": "Protected file modified",
            "src_ip": "203.0.113.44",
            "dst_ip": "10.20.1.20",
            "dst_port": "443",
            "username": "backup-runner",
        },
        received_at=datetime.now(UTC),
    )
    alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=raw_alert,
        asset=asset,
        source="wazuh",
        title="Protected configuration file changed",
        description="Observed outside approved maintenance window.",
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        severity=8,
        status=AlertStatus.INVESTIGATING,
        normalized_payload={
            "file_path": "/etc/nginx/nginx.conf",
            "source_ip": "203.0.113.44",
            "destination_port": 443,
            "username": "backup-runner",
        },
        created_at=datetime.now(UTC),
    )
    alert.risk_score = RiskScore(
        id=uuid4(),
        normalized_alert=alert,
        score=0.88,
        confidence=0.89,
        reasoning="Integrity change affected a critical configuration path.",
        calculated_at=datetime.now(UTC),
    )
    incident = Incident(
        id=uuid4(),
        normalized_alert=alert,
        assigned_user=analyst,
        title="Investigate config drift",
        summary="Configuration drift on a critical system is under active investigation.",
        status=IncidentStatus.INVESTIGATING,
        priority=IncidentPriority.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    response_action = ResponseAction(
        id=uuid4(),
        incident=incident,
        requested_by=analyst,
        action_type="collect_configuration_backup",
        status=ResponseStatus.IN_PROGRESS,
        mode=ResponseMode.DRY_RUN,
        details={"path": "/etc/nginx/nginx.conf", "result": "snapshot_requested"},
        created_at=datetime.now(UTC),
        executed_at=None,
    )
    incident.response_actions = [response_action]
    audit_logs = [
        AuditLog(
            id=uuid4(),
            actor=analyst,
            entity_type="incident",
            entity_id=str(incident.id),
            action="incident.assigned",
            details={"assigned_to": analyst.username, "message": "Assigned for review"},
            created_at=datetime.now(UTC),
        )
    ]
    analyst_notes = [
        AnalystNote(
            id=uuid4(),
            target_type=NoteTargetType.ALERT,
            target_id=alert.id,
            author=analyst,
            content="Escalated after validating unexpected configuration drift.",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    ]
    return alert, incident, audit_logs, analyst_notes


def test_alert_detail_response_includes_observables_and_related_workflow() -> None:
    alert, _, audit_logs, analyst_notes = _build_fixture()

    response = to_alert_detail_response(alert, audit_logs, analyst_notes)

    assert response.source_type == "Wazuh"
    assert response.severity.value == "high"
    assert response.status_label == "pending_response"
    assert response.source_ip == "203.0.113.44"
    assert response.destination_port == 443
    assert response.source_rule is not None
    assert response.source_rule.rule_id == "60115"
    assert response.related_responses[0].target == "/etc/nginx/nginx.conf"
    assert response.related_responses[0].mode.value == "dry-run"
    assert response.linked_incident is not None
    assert response.score_explanation is not None
    assert response.analyst_notes[0].content.startswith("Escalated")


def test_incident_detail_response_builds_evidence_timeline_and_capabilities() -> None:
    _, incident, audit_logs, analyst_notes = _build_fixture()

    response = to_incident_detail_response(incident, audit_logs, analyst_notes)

    assert response.state.value == "investigating"
    assert response.assignee is not None
    assert response.assignee.username == "analyst"
    assert len(response.linked_alerts) == 1
    assert response.grouped_evidence.evidence_items
    assert response.response_history[0].action_type == "collect_configuration_backup"
    assert "contain" in response.state_transition_capabilities.available_actions
    assert response.timeline[0].title == "Incident created"
    assert response.analyst_notes[0].content.startswith("Escalated")
