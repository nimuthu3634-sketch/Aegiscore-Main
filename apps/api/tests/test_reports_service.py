from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from app.models.asset import Asset
from app.models.audit_log import AuditLog
from app.models.enums import (
    AlertStatus,
    AssetCriticality,
    DetectionType,
    IncidentPriority,
    IncidentStatus,
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
from app.schemas.reports import (
    AlertReportExportQuery,
    IncidentReportExportQuery,
    ReportExportFormat,
    ReportSummaryQuery,
    ResponseReportExportQuery,
)
from app.services import reports


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def commit(self) -> None:
        self.commits += 1


def _sample_actor() -> User:
    return User(
        id=uuid4(),
        role=Role(id=uuid4(), name=RoleName.ADMIN),
        username="admin",
        password_hash="hashed",
        full_name="AegisCore Admin",
        is_active=True,
    )


def _sample_alert_fixture() -> tuple[NormalizedAlert, NormalizedAlert]:
    # Keep fixture timestamps deterministic and within report query windows.
    now = datetime(2026, 4, 5, 12, 0, tzinfo=UTC)
    asset = Asset(
        id=uuid4(),
        hostname="acct-db-01",
        ip_address="10.20.1.20",
        operating_system="Ubuntu 24.04",
        criticality=AssetCriticality.CRITICAL,
        created_at=now,
        updated_at=now,
    )

    raw_one = RawAlert(
        id=uuid4(),
        asset=asset,
        source="wazuh",
        external_id="wazuh-report-1",
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        severity=9,
        raw_payload={"file_path": "/etc/shadow", "source_ip": "203.0.113.10"},
        received_at=now,
    )
    alert_one = NormalizedAlert(
        id=uuid4(),
        raw_alert=raw_one,
        asset=asset,
        source="wazuh",
        title="Critical file changed",
        description="Sensitive file integrity drift detected.",
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        severity=9,
        status=AlertStatus.INVESTIGATING,
        normalized_payload={"file_path": "/etc/shadow", "source_ip": "203.0.113.10"},
        created_at=now,
    )
    alert_one.risk_score = RiskScore(
        id=uuid4(),
        normalized_alert=alert_one,
        score=91,
        confidence=0.95,
        priority_label=IncidentPriority.CRITICAL,
        scoring_method=ScoreMethod.BASELINE_RULES,
        baseline_version="baseline-v1",
        model_version=None,
        reasoning="Critical asset + sensitive file.",
        explanation={"drivers": ["Sensitive file touched", "Critical asset"]},
        feature_snapshot={"sensitive_file_flag": True},
        calculated_at=now,
    )

    raw_two = RawAlert(
        id=uuid4(),
        asset=asset,
        source="suricata",
        external_id="suricata-report-1",
        detection_type=DetectionType.PORT_SCAN,
        severity=6,
        raw_payload={"src_ip": "198.51.100.20", "dst_port": "443"},
        received_at=now,
    )
    alert_two = NormalizedAlert(
        id=uuid4(),
        raw_alert=raw_two,
        asset=asset,
        source="suricata",
        title="Port scan detected",
        description="Recon against internet-facing service.",
        detection_type=DetectionType.PORT_SCAN,
        severity=6,
        status=AlertStatus.NEW,
        normalized_payload={"source_ip": "198.51.100.20", "destination_port": 443},
        created_at=now,
    )
    alert_two.risk_score = RiskScore(
        id=uuid4(),
        normalized_alert=alert_two,
        score=68,
        confidence=0.8,
        priority_label=IncidentPriority.HIGH,
        scoring_method=ScoreMethod.BASELINE_RULES,
        baseline_version="baseline-v1",
        model_version=None,
        reasoning="Repeated reconnaissance activity.",
        explanation={"drivers": ["Repeated source IP"]},
        feature_snapshot={"repeated_source_ip": 4},
        calculated_at=now,
    )

    incident = Incident(
        id=uuid4(),
        title="Correlated perimeter activity",
        summary="Wazuh and Suricata signals grouped together.",
        status=IncidentStatus.TRIAGED,
        priority=IncidentPriority.CRITICAL,
        created_at=now,
        updated_at=now,
    )
    incident.primary_alert = alert_one
    incident.alerts = [alert_one, alert_two]
    alert_one.incident = incident
    alert_two.incident = incident

    response_action = ResponseAction(
        id=uuid4(),
        incident=incident,
        normalized_alert=alert_one,
        action_type="notify_admin",
        status=ResponseStatus.COMPLETED,
        mode=ResponseMode.DRY_RUN,
        target_value="AegisCore administrators",
        result_summary="Administrator notification delivered.",
        result_message="notification sent",
        attempt_count=1,
        details={"summary": "notification sent"},
        created_at=now,
        executed_at=now,
    )
    incident.response_actions = [response_action]
    alert_one.response_actions = [response_action]
    alert_two.response_actions = []

    return alert_one, alert_two


def test_get_daily_summary_compiles_operational_metrics(monkeypatch) -> None:
    alert_one, alert_two = _sample_alert_fixture()
    session = FakeSession()

    monkeypatch.setattr(
        reports.ReportsRepository,
        "list_alerts_for_summary",
        lambda self, query, window_start, window_end: [alert_one, alert_two],
    )

    summary = reports.get_daily_summary(
        session,
        ReportSummaryQuery(
            date_from=date(2026, 4, 4),
            date_to=date(2026, 4, 5),
        ),
    )

    assert summary.report_type == "daily"
    assert summary.total_alerts == 2
    assert summary.high_risk_alerts == 1
    assert summary.open_incidents == 1
    assert summary.response_actions == 1
    assert summary.active_assets == 1
    assert any(item.label == "file_integrity_violation" for item in summary.alerts_by_detection)
    assert any(item.label == "critical" for item in summary.severity_distribution)


def test_export_alert_report_returns_json_and_audits(monkeypatch) -> None:
    alert_one, alert_two = _sample_alert_fixture()
    session = FakeSession()
    actor = _sample_actor()

    monkeypatch.setattr(
        reports.ReportsRepository,
        "list_alerts_for_export",
        lambda self, query, window_start, window_end: [alert_one, alert_two],
    )

    response = reports.export_alert_report(
        session,
        AlertReportExportQuery(format=ReportExportFormat.JSON),
        actor,
    )

    assert response.media_type == "application/json"
    assert "content-disposition" in response.headers
    assert session.commits == 1
    assert any(isinstance(item, AuditLog) for item in session.added)


def test_export_responses_report_returns_csv(monkeypatch) -> None:
    alert_one, _ = _sample_alert_fixture()
    session = FakeSession()
    actor = _sample_actor()
    response_action = alert_one.response_actions[0]

    monkeypatch.setattr(
        reports.ReportsRepository,
        "list_responses_for_export",
        lambda self, query, window_start, window_end: [response_action],
    )

    response = reports.export_response_report(
        session,
        ResponseReportExportQuery(format=ReportExportFormat.CSV),
        actor,
    )

    assert response.media_type == "text/csv"
    assert "response_id" in response.body.decode()
    assert "notify_admin" in response.body.decode()
    assert session.commits == 1


def test_export_incidents_report_returns_csv(monkeypatch) -> None:
    alert_one, _ = _sample_alert_fixture()
    incident = alert_one.incident
    assert incident is not None
    session = FakeSession()
    actor = _sample_actor()

    monkeypatch.setattr(
        reports.ReportsRepository,
        "list_incidents_for_export",
        lambda self, query, window_start, window_end: [incident],
    )

    response = reports.export_incident_report(
        session,
        IncidentReportExportQuery(format=ReportExportFormat.CSV),
        actor,
    )

    assert response.media_type == "text/csv"
    payload = response.body.decode()
    assert "incident_id" in payload
    assert "Correlated perimeter activity" in payload
    assert session.commits == 1
