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
    ScoreMethod,
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
        score=88,
        confidence=0.89,
        priority_label=IncidentPriority.CRITICAL,
        scoring_method=ScoreMethod.BASELINE_RULES,
        baseline_version="baseline_v1",
        reasoning="Integrity change affected a critical configuration path.",
        explanation={
            "label": "Deterministic baseline score",
            "summary": "Alert scored 88/100 and was classified as critical priority.",
            "rationale": "Baseline factors elevated the alert.",
            "factors": ["Sensitive file or configuration path was involved."],
            "drivers": [{"feature": "sensitive_file_flag", "contribution": 10}],
        },
        feature_snapshot={"sensitive_file_flag": 1},
        calculated_at=datetime.now(UTC),
    )
    secondary_asset = Asset(
        id=uuid4(),
        hostname="acct-web-01",
        ip_address="10.20.1.15",
        operating_system="Ubuntu 22.04 LTS",
        criticality=AssetCriticality.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    secondary_raw_alert = RawAlert(
        id=uuid4(),
        asset=secondary_asset,
        source="suricata",
        external_id="suricata-2048",
        detection_type=DetectionType.PORT_SCAN,
        severity=6,
        raw_payload={
            "signature": "ET SCAN Potential SSH Scan",
            "src_ip": "198.51.100.22",
            "dest_ip": "10.20.1.15",
            "dst_port": "22",
        },
        received_at=datetime.now(UTC),
    )
    secondary_alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=secondary_raw_alert,
        asset=secondary_asset,
        source="suricata",
        title="External port scan observed",
        description="Repeated TCP connection attempts targeted the web tier.",
        detection_type=DetectionType.PORT_SCAN,
        severity=6,
        status=AlertStatus.NEW,
        normalized_payload={
            "scanner_ip": "198.51.100.22",
            "destination_port": 22,
        },
        created_at=datetime.now(UTC),
    )
    secondary_alert.risk_score = RiskScore(
        id=uuid4(),
        normalized_alert=secondary_alert,
        score=54,
        confidence=0.73,
        priority_label=IncidentPriority.MEDIUM,
        scoring_method=ScoreMethod.BASELINE_RULES,
        baseline_version="baseline_v1",
        reasoning="External reconnaissance detected against an internet-facing asset.",
        explanation={"summary": "Alert scored 54/100."},
        feature_snapshot={"repeated_source_ip": 2},
        calculated_at=datetime.now(UTC),
    )
    incident = Incident(
        id=uuid4(),
        assigned_user=analyst,
        title="Investigate config drift",
        summary="Configuration drift on a critical system is under active investigation.",
        status=IncidentStatus.INVESTIGATING,
        priority=IncidentPriority.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    incident.primary_alert = alert
    incident.alerts = [alert, secondary_alert]
    alert.incident = incident
    secondary_alert.incident = incident
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


def test_alert_detail_tensorflow_score_explanation_includes_scoring_method() -> None:
    now = datetime.now(UTC)
    asset = Asset(
        id=uuid4(),
        hostname="edge-ssh",
        ip_address="10.5.0.1",
        operating_system="Linux",
        criticality=AssetCriticality.HIGH,
        created_at=now,
        updated_at=now,
    )
    raw = RawAlert(
        id=uuid4(),
        asset=asset,
        source="wazuh",
        external_id="wazuh-tf-detail",
        detection_type=DetectionType.BRUTE_FORCE,
        severity=10,
        raw_payload={"source_ip": "203.0.113.9"},
        received_at=now,
    )
    alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=raw,
        asset=asset,
        source="wazuh",
        title="SSH brute force",
        description="Repeated failures.",
        detection_type=DetectionType.BRUTE_FORCE,
        severity=10,
        status=AlertStatus.NEW,
        normalized_payload={"source_ip": "203.0.113.9", "failed_attempts": 40},
        created_at=now,
    )
    alert.risk_score = RiskScore(
        id=uuid4(),
        normalized_alert=alert,
        score=68.0,
        confidence=0.55,
        priority_label=IncidentPriority.MEDIUM,
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        model_version="tf_unit",
        reasoning="TensorFlow 3-class tier: medium with 55% confidence.",
        explanation={
            "label": "Trainable alert prioritization model",
            "summary": "Model predicted medium priority at 68.0/100 (3-class TensorFlow output: medium).",
            "rationale": "TensorFlow (Keras) MLP on normalized telemetry (alert_prioritization_v1).",
            "factors": [
                "Model probability for medium class: 55.0%",
                "Model probability for high class: 30.0%",
            ],
            "class_probabilities": {"low": 0.15, "medium": 0.55, "high": 0.30},
            "model_priority_tier": "medium",
            "scoring_method": ScoreMethod.TENSORFLOW_MODEL.value,
        },
        feature_snapshot={"failed_logins_5m": 11},
        calculated_at=now,
    )
    alert.response_actions = []

    response = to_alert_detail_response(alert, [], [])

    assert response.score_explanation is not None
    assert response.score_explanation.scoring_method == ScoreMethod.TENSORFLOW_MODEL
    assert response.score_explanation.model_version == "tf_unit"
    assert response.score_explanation.confidence == 0.55
    assert "TensorFlow" in response.score_explanation.rationale
    assert response.score_explanation.factors
    assert response.score_explanation.model_priority_tier == "medium"
    assert response.score_explanation.class_probabilities == {"low": 0.15, "medium": 0.55, "high": 0.30}
    assert response.score_explanation.reasoning == "TensorFlow 3-class tier: medium with 55% confidence."
    dumped = response.model_dump(mode="json")
    assert dumped["score_explanation"]["scoring_method"] == ScoreMethod.TENSORFLOW_MODEL.value
    assert dumped["score_explanation"]["model_priority_tier"] == "medium"
    assert dumped["score_explanation"]["class_probabilities"]["high"] == 0.30


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
    assert response.risk_score == 88
    assert response.score_explanation.scoring_method == ScoreMethod.BASELINE_RULES
    assert response.score_explanation.feature_snapshot == {"sensitive_file_flag": 1}
    assert response.analyst_notes[0].content.startswith("Escalated")
    assert response.notifications == []


def test_incident_detail_response_builds_evidence_timeline_and_capabilities() -> None:
    _, incident, audit_logs, analyst_notes = _build_fixture()

    response = to_incident_detail_response(incident, audit_logs, analyst_notes)

    assert response.state.value == "investigating"
    assert response.assignee is not None
    assert response.assignee.username == "analyst"
    assert len(response.linked_alerts) == 2
    assert len(response.affected_assets) == 2
    assert response.grouped_evidence.evidence_items
    assert response.response_history[0].action_type == "collect_configuration_backup"
    assert "contain" in response.state_transition_capabilities.available_actions
    assert response.timeline[0].title == "Incident created"
    assert response.priority_explanation.rollup_score is not None
    assert response.priority_explanation.linked_alerts_count == 2
    assert response.analyst_notes[0].content.startswith("Escalated")
