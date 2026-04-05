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
        score=0.81,
        confidence=0.88,
        reasoning="High-volume failures on an internet-facing system.",
        calculated_at=datetime.now(UTC),
    )
    normalized_alert.risk_score = risk_score

    response = to_alert_summary_response(normalized_alert)

    assert response.asset is not None
    assert response.risk_score is not None
    assert response.asset.hostname == "acct-web-01"
    assert response.risk_score.score == 0.81


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
    incident = Incident(
        id=uuid4(),
        normalized_alert=normalized_alert,
        assigned_user=assigned_user,
        title="Investigate config drift",
        summary="Critical infrastructure config changed unexpectedly.",
        status=IncidentStatus.INVESTIGATING,
        priority=IncidentPriority.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    response = to_incident_summary_response(incident)

    assert response.assigned_user is not None
    assert response.assigned_user.username == "analyst"
    assert response.alert.title == "Protected config changed"

