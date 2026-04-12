from datetime import UTC, datetime
from uuid import uuid4

from app.models.asset import Asset
from app.models.enums import (
    AlertStatus,
    AssetCriticality,
    DetectionType,
    IncidentPriority,
    IncidentStatus,
    RoleName,
    ScoreMethod,
)
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.risk_score import RiskScore
from app.models.role import Role
from app.models.user import User
from app.services.serializers import (
    to_alert_summary_response,
    to_incident_summary_response,
)


def test_alert_summary_response_includes_nested_entities() -> None:
    asset = Asset(
        id=uuid4(),
        hostname="acct-web-01",
        ip_address="10.0.0.10",
        operating_system="Ubuntu",
        criticality=AssetCriticality.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    raw_alert = RawAlert(
        id=uuid4(),
        asset=asset,
        source="wazuh",
        external_id="wazuh-1",
        detection_type=DetectionType.BRUTE_FORCE,
        severity=7,
        raw_payload={"source_ip": "203.0.113.10"},
        received_at=datetime.now(UTC),
    )
    normalized_alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=raw_alert,
        asset=asset,
        source="wazuh",
        title="Brute force against SSH",
        description="Repeated authentication failures exceeded threshold.",
        detection_type=DetectionType.BRUTE_FORCE,
        severity=7,
        status=AlertStatus.NEW,
        normalized_payload={"failed_attempts": 22},
        created_at=datetime.now(UTC),
    )
    risk_score = RiskScore(
        id=uuid4(),
        normalized_alert=normalized_alert,
        score=81,
        confidence=0.88,
        priority_label=IncidentPriority.HIGH,
        scoring_method=ScoreMethod.BASELINE_RULES,
        baseline_version="baseline_v1",
        reasoning="High-volume failures on an internet-facing system.",
        explanation={"summary": "Alert scored 81/100."},
        feature_snapshot={"repeated_failed_logins": 22},
        calculated_at=datetime.now(UTC),
    )
    normalized_alert.risk_score = risk_score

    response = to_alert_summary_response(normalized_alert)

    assert response.asset is not None
    assert response.risk_score is not None
    assert response.asset.hostname == "acct-web-01"
    assert response.risk_score.score == 81
    assert response.risk_score.scoring_method == ScoreMethod.BASELINE_RULES
    assert response.risk_score.baseline_version == "baseline_v1"
    assert response.risk_score_value == 81


def test_incident_summary_response_includes_assigned_user_and_alert() -> None:
    role = Role(
        id=uuid4(),
        name=RoleName.ANALYST,
        description="Analyst role",
        created_at=datetime.now(UTC),
    )
    assigned_user = User(
        id=uuid4(),
        role=role,
        username="analyst",
        password_hash="hashed",
        full_name="Analyst User",
        is_active=True,
        created_at=datetime.now(UTC),
    )
    asset = Asset(
        id=uuid4(),
        hostname="acct-db-01",
        ip_address="10.0.0.20",
        operating_system="PostgreSQL",
        criticality=AssetCriticality.CRITICAL,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    raw_alert = RawAlert(
        id=uuid4(),
        asset=asset,
        source="wazuh",
        external_id="wazuh-2",
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        severity=8,
        raw_payload={"file_path": "/etc/nginx/nginx.conf"},
        received_at=datetime.now(UTC),
    )
    normalized_alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=raw_alert,
        asset=asset,
        source="wazuh",
        title="Protected config changed",
        description="Observed outside approved maintenance window.",
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        severity=8,
        status=AlertStatus.INVESTIGATING,
        normalized_payload={"file_path": "/etc/nginx/nginx.conf"},
        created_at=datetime.now(UTC),
    )
    secondary_raw_alert = RawAlert(
        id=uuid4(),
        asset=asset,
        source="suricata",
        external_id="suricata-3",
        detection_type=DetectionType.PORT_SCAN,
        severity=6,
        raw_payload={"src_ip": "198.51.100.22", "dst_port": "22"},
        received_at=datetime.now(UTC),
    )
    secondary_alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=secondary_raw_alert,
        asset=asset,
        source="suricata",
        title="Port scan on web edge",
        description="Sequential connection attempts observed.",
        detection_type=DetectionType.PORT_SCAN,
        severity=6,
        status=AlertStatus.NEW,
        normalized_payload={"destination_port": 22},
        created_at=datetime.now(UTC),
    )
    incident = Incident(
        id=uuid4(),
        assigned_user=assigned_user,
        title="Investigate config drift",
        summary="Critical infrastructure config changed unexpectedly.",
        status=IncidentStatus.INVESTIGATING,
        priority=IncidentPriority.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    incident.primary_alert = normalized_alert
    incident.alerts = [normalized_alert, secondary_alert]
    normalized_alert.incident = incident
    secondary_alert.incident = incident

    response = to_incident_summary_response(incident)

    assert response.assigned_user is not None
    assert response.assigned_user.username == "analyst"
    assert response.alert.title == "Protected config changed"
    assert response.linked_alerts_count == 2


def test_alert_summary_tensorflow_risk_score_serializes_explanation_payload() -> None:
    """Nested ``risk_score.explanation`` keeps ML fields for API clients."""
    now = datetime.now(UTC)
    asset = Asset(
        id=uuid4(),
        hostname="auth-01",
        ip_address="10.0.0.5",
        operating_system="Linux",
        criticality=AssetCriticality.HIGH,
        created_at=now,
        updated_at=now,
    )
    raw_alert = RawAlert(
        id=uuid4(),
        asset=asset,
        source="wazuh",
        external_id="wazuh-tf-1",
        detection_type=DetectionType.BRUTE_FORCE,
        severity=9,
        raw_payload={"source_ip": "198.51.100.10"},
        received_at=now,
    )
    normalized_alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=raw_alert,
        asset=asset,
        source="wazuh",
        title="Brute force (TF scored)",
        description="Model-assigned tier.",
        detection_type=DetectionType.BRUTE_FORCE,
        severity=9,
        status=AlertStatus.NEW,
        normalized_payload={"source_ip": "198.51.100.10"},
        created_at=now,
    )
    explanation = {
        "label": "Trainable alert prioritization model",
        "summary": "Model version v1 predicted high priority at 72.5/100 (3-class TensorFlow output: high).",
        "rationale": "TensorFlow (Keras) MLP on normalized telemetry (alert_prioritization_v1).",
        "factors": ["Model probability for high class: 61.0%"],
        "class_probabilities": {"low": 0.12, "medium": 0.27, "high": 0.61},
        "model_priority_tier": "high",
        "predicted_class": "high",
        "scoring_method": ScoreMethod.TENSORFLOW_MODEL.value,
        "model_version": "alert_prioritization_v1",
    }
    normalized_alert.risk_score = RiskScore(
        id=uuid4(),
        normalized_alert=normalized_alert,
        score=72.5,
        confidence=0.61,
        priority_label=IncidentPriority.HIGH,
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        model_version="alert_prioritization_v1",
        reasoning="TensorFlow 3-class tier: high with 61% confidence.",
        explanation=explanation,
        feature_snapshot={"failed_logins_5m": 14, "detection_type": "brute_force"},
        calculated_at=now,
    )
    normalized_alert.response_actions = []

    response = to_alert_summary_response(normalized_alert)
    dumped = response.model_dump(mode="json")

    assert dumped["risk_score"]["scoring_method"] == ScoreMethod.TENSORFLOW_MODEL.value
    assert dumped["risk_score"]["explanation"]["scoring_method"] == ScoreMethod.TENSORFLOW_MODEL.value
    assert dumped["risk_score"]["explanation"]["class_probabilities"]["high"] == 0.61
    assert dumped["risk_score"]["explanation"]["model_priority_tier"] == "high"
    assert dumped["risk_score"]["model_version"] == "alert_prioritization_v1"
