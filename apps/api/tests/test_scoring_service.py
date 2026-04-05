from datetime import UTC, datetime
from uuid import uuid4

from app.models.asset import Asset
from app.models.enums import (
    AlertStatus,
    AssetCriticality,
    DetectionType,
    IncidentPriority,
    IncidentStatus,
    ScoreMethod,
)
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.risk_score import RiskScore
from app.services.scoring.service import (
    build_incident_priority_summary,
    persist_and_score_alert,
    refresh_incident_priority,
)


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.flush_count = 0

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        self.flush_count += 1


def test_incident_rollup_uses_real_linked_alert_scores() -> None:
    asset = Asset(
        id=uuid4(),
        hostname="acct-db-01",
        ip_address="10.20.1.20",
        operating_system="PostgreSQL Appliance",
        criticality=AssetCriticality.CRITICAL,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    primary_raw = RawAlert(
        id=uuid4(),
        asset=asset,
        source="wazuh",
        external_id="wazuh-1",
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        severity=8,
        raw_payload={"file_path": "/etc/nginx/nginx.conf"},
        received_at=datetime.now(UTC),
    )
    primary_alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=primary_raw,
        asset=asset,
        source="wazuh",
        title="Critical config changed",
        description="Config drift detected.",
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        severity=8,
        status=AlertStatus.INVESTIGATING,
        normalized_payload={"file_path": "/etc/nginx/nginx.conf"},
        created_at=datetime.now(UTC),
    )
    primary_alert.risk_score = RiskScore(
        id=uuid4(),
        normalized_alert=primary_alert,
        score=88,
        confidence=0.91,
        priority_label=IncidentPriority.CRITICAL,
        scoring_method=ScoreMethod.BASELINE_RULES,
        reasoning="Critical config path changed.",
        explanation={"summary": "Alert scored 88/100."},
        feature_snapshot={"sensitive_file_flag": 1},
        calculated_at=datetime.now(UTC),
    )

    secondary_raw = RawAlert(
        id=uuid4(),
        asset=asset,
        source="suricata",
        external_id="suricata-1",
        detection_type=DetectionType.PORT_SCAN,
        severity=5,
        raw_payload={"src_ip": "198.51.100.22", "dst_port": "443"},
        received_at=datetime.now(UTC),
    )
    secondary_alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=secondary_raw,
        asset=asset,
        source="suricata",
        title="Recon on web edge",
        description="Port scan detected.",
        detection_type=DetectionType.PORT_SCAN,
        severity=5,
        status=AlertStatus.NEW,
        normalized_payload={"destination_port": 443},
        created_at=datetime.now(UTC),
    )
    secondary_alert.risk_score = RiskScore(
        id=uuid4(),
        normalized_alert=secondary_alert,
        score=62,
        confidence=0.76,
        priority_label=IncidentPriority.MEDIUM,
        scoring_method=ScoreMethod.BASELINE_RULES,
        reasoning="Recon detected against internet-facing service.",
        explanation={"summary": "Alert scored 62/100."},
        feature_snapshot={"repeated_source_ip": 3},
        calculated_at=datetime.now(UTC),
    )

    incident = Incident(
        id=uuid4(),
        title="Correlated infrastructure activity",
        summary="Multiple alerts grouped together.",
        status=IncidentStatus.INVESTIGATING,
        priority=IncidentPriority.MEDIUM,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    incident.primary_alert = primary_alert
    incident.alerts = [primary_alert, secondary_alert]
    primary_alert.incident = incident
    secondary_alert.incident = incident

    priority = refresh_incident_priority(incident)
    summary = build_incident_priority_summary(incident)

    assert priority == IncidentPriority.CRITICAL
    assert summary["score"] >= 80
    assert "Linked alert count: 2" in summary["factors"]


def test_persist_and_score_alert_links_raw_and_normalized_records(monkeypatch) -> None:
    session = FakeSession()
    raw_alert = RawAlert(
        id=uuid4(),
        source="wazuh",
        external_id="wazuh-link-test",
        detection_type=DetectionType.BRUTE_FORCE,
        severity=7,
        raw_payload={"src_ip": "203.0.113.8"},
        received_at=datetime.now(UTC),
    )
    normalized_alert = NormalizedAlert(
        id=uuid4(),
        source="wazuh",
        title="Linkage validation alert",
        description="Used to verify raw-to-normalized persistence linkage.",
        detection_type=DetectionType.BRUTE_FORCE,
        severity=7,
        status=AlertStatus.NEW,
        normalized_payload={"source_ip": "203.0.113.8"},
        created_at=datetime.now(UTC),
    )
    captured: dict[str, object] = {}

    def fake_score_alert(score_session, alert):
        captured["session"] = score_session
        captured["alert"] = alert
        return None

    monkeypatch.setattr("app.services.scoring.service.score_alert", fake_score_alert)

    result = persist_and_score_alert(session, raw_alert, normalized_alert)

    assert result is normalized_alert
    assert raw_alert.normalized_alert is normalized_alert
    assert normalized_alert.raw_alert is raw_alert
    assert captured["session"] is session
    assert captured["alert"] is normalized_alert
    assert session.flush_count == 1
