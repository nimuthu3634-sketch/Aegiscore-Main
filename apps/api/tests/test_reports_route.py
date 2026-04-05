from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import reports as reports_route
from app.db.session import get_db_session
from app.main import app
from app.models.enums import DetectionType
from app.schemas.reports import ReportSummaryResponse


def _override_dependencies() -> None:
    app.dependency_overrides[deps.get_current_user] = lambda: object()
    app.dependency_overrides[get_db_session] = lambda: None


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def _sample_summary(report_type: str) -> ReportSummaryResponse:
    now = datetime.now(UTC)
    return ReportSummaryResponse(
        report_type=report_type,
        generated_at=now,
        window_start=now,
        window_end=now,
        total_alerts=4,
        high_risk_alerts=2,
        open_incidents=1,
        response_actions=2,
        active_assets=3,
        average_risk_score=81.5,
        alert_volume=[],
        alerts_by_detection=[],
        severity_distribution=[],
        incident_state_distribution=[],
        response_status_distribution=[],
        top_assets=[],
    )


def test_daily_summary_route_parses_query_params(monkeypatch) -> None:
    captured = {}
    _override_dependencies()

    def fake_get_daily_summary(db, query):
        captured["query"] = query
        return _sample_summary("daily")

    monkeypatch.setattr(reports_route, "get_daily_summary", fake_get_daily_summary)

    try:
        client = TestClient(app)
        response = client.get(
            "/reports/daily-summary",
            params={
                "date_from": "2026-04-01",
                "date_to": "2026-04-05",
                "detection_type": "port_scan",
                "source_type": "suricata",
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    query = captured["query"]
    assert query.date_from.isoformat() == "2026-04-01"
    assert query.date_to.isoformat() == "2026-04-05"
    assert query.detection_type == DetectionType.PORT_SCAN
    assert query.source_type.value == "suricata"


def test_alert_export_route_parses_query_params(monkeypatch) -> None:
    captured = {}
    _override_dependencies()

    def fake_export_alert_report(db, query, actor):
        captured["query"] = query
        return reports_route.Response(
            content="alert_id\n",
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="alerts.csv"'},
        )

    monkeypatch.setattr(reports_route, "export_alert_report", fake_export_alert_report)

    try:
        client = TestClient(app)
        response = client.get(
            "/reports/alerts/export",
            params={
                "date_from": "2026-04-01",
                "date_to": "2026-04-05",
                "severity": "high",
                "status": "pending_response",
                "asset": "edge-auth-01",
                "format": "csv",
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="alerts.csv"'
    query = captured["query"]
    assert query.severity.value == "high"
    assert query.status.value == "pending_response"
    assert query.asset == "edge-auth-01"
    assert query.format.value == "csv"


def test_incident_export_route_parses_query_params(monkeypatch) -> None:
    captured = {}
    _override_dependencies()

    def fake_export_incident_report(db, query, actor):
        captured["query"] = query
        return reports_route.Response(
            content="incident_id\n",
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="incidents.json"'},
        )

    monkeypatch.setattr(reports_route, "export_incident_report", fake_export_incident_report)

    try:
        client = TestClient(app)
        response = client.get(
            "/reports/incidents/export",
            params={
                "date_from": "2026-04-01",
                "date_to": "2026-04-05",
                "priority": "critical",
                "state": "triaged",
                "assignee": "analyst",
                "detection_type": "file_integrity_violation",
                "format": "json",
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    query = captured["query"]
    assert query.priority.value == "critical"
    assert query.state.value == "triaged"
    assert query.assignee == "analyst"
    assert query.detection_type == DetectionType.FILE_INTEGRITY_VIOLATION
    assert query.format.value == "json"


def test_response_export_route_parses_query_params(monkeypatch) -> None:
    captured = {}
    _override_dependencies()

    def fake_export_response_report(db, query, actor):
        captured["query"] = query
        return reports_route.Response(
            content="response_id\n",
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="responses.csv"'},
        )

    monkeypatch.setattr(reports_route, "export_response_report", fake_export_response_report)

    try:
        client = TestClient(app)
        response = client.get(
            "/reports/responses/export",
            params={
                "date_from": "2026-04-01",
                "date_to": "2026-04-05",
                "mode": "dry-run",
                "execution_status": "warning",
                "action_type": "notify_admin",
                "format": "csv",
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    query = captured["query"]
    assert query.mode.value == "dry-run"
    assert query.execution_status.value == "warning"
    assert query.action_type == "notify_admin"
