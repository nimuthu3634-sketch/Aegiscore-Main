from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import alerts as alerts_route
from app.api.routes import assets as assets_route
from app.api.routes import incidents as incidents_route
from app.api.routes import responses as responses_route
from app.db.session import get_db_session
from app.main import app
from app.models.enums import DetectionType
from app.schemas.common import (
    AlertListResponse,
    AssetListResponse,
    IncidentListResponse,
    ResponseActionListResponse,
)
from app.schemas.listing import (
    AlertListStatusFilter,
    AlertSeverityLabel,
    AssetAgentStatusLabel,
    AssetEnvironmentLabel,
    IncidentListStateFilter,
    ListMetaResponse,
    ResponseExecutionStatusLabel,
    ResponseModeLabel,
    SortDirection,
)


def _override_dependencies() -> None:
    app.dependency_overrides[deps.get_current_user] = lambda: object()
    app.dependency_overrides[get_db_session] = lambda: None


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def _meta(sort_by: str, direction: SortDirection = SortDirection.DESC) -> ListMetaResponse:
    return ListMetaResponse(
        page=1,
        page_size=10,
        total=0,
        total_pages=1,
        sort_by=sort_by,
        sort_direction=direction,
        warnings=[],
    )


def test_alerts_route_parses_query_params(monkeypatch) -> None:
    captured = {}
    _override_dependencies()

    def fake_list_alerts(db, query):
        captured["query"] = query
        return AlertListResponse(items=[], meta=_meta("risk_score"))

    monkeypatch.setattr(alerts_route, "list_alerts", fake_list_alerts)

    try:
        client = TestClient(app)
        response = client.get(
            "/alerts",
            params={
                "search": "svc-shadow",
                "severity": "high",
                "status": "pending_response",
                "detection_type": "unauthorized_user_creation",
                "source_type": "wazuh",
                "asset": "acct-windows-01",
                "date_range": "12h",
                "sort_by": "risk_score",
                "sort_direction": "asc",
                "page": 2,
                "page_size": 5,
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    query = captured["query"]
    assert query.search == "svc-shadow"
    assert query.severity == AlertSeverityLabel.HIGH
    assert query.status == AlertListStatusFilter.PENDING_RESPONSE
    assert query.detection_type == DetectionType.UNAUTHORIZED_USER_CREATION
    assert query.source_type.value == "wazuh"
    assert query.asset == "acct-windows-01"
    assert query.page == 2
    assert query.page_size == 5


def test_incidents_route_parses_query_params(monkeypatch) -> None:
    captured = {}
    _override_dependencies()

    def fake_list_incidents(db, query):
        captured["query"] = query
        return IncidentListResponse(items=[], meta=_meta("priority"))

    monkeypatch.setattr(incidents_route, "list_incidents", fake_list_incidents)

    try:
        client = TestClient(app)
        response = client.get(
            "/incidents",
            params={
                "search": "acct-db-01",
                "priority": "critical",
                "state": "triaged",
                "assignee": "analyst",
                "detection_type": "file_integrity_violation",
                "sort_by": "priority",
                "sort_direction": "asc",
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    query = captured["query"]
    assert query.priority == AlertSeverityLabel.CRITICAL
    assert query.state == IncidentListStateFilter.TRIAGED
    assert query.assignee == "analyst"
    assert query.detection_type == DetectionType.FILE_INTEGRITY_VIOLATION


def test_assets_route_parses_query_params(monkeypatch) -> None:
    captured = {}
    _override_dependencies()

    def fake_list_assets(db, query):
        captured["query"] = query
        return AssetListResponse(items=[], meta=_meta("recent_alerts"))

    monkeypatch.setattr(assets_route, "list_assets", fake_list_assets)

    try:
        client = TestClient(app)
        response = client.get(
            "/assets",
            params={
                "search": "edge",
                "status": "degraded",
                "criticality": "mission_critical",
                "operating_system": "Ubuntu",
                "environment": "remote",
                "sort_by": "recent_alerts",
                "sort_direction": "desc",
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    query = captured["query"]
    assert query.status == AssetAgentStatusLabel.DEGRADED
    assert query.criticality == "mission_critical"
    assert query.operating_system == "Ubuntu"
    assert query.environment == AssetEnvironmentLabel.REMOTE


def test_responses_route_parses_query_params(monkeypatch) -> None:
    captured = {}
    _override_dependencies()

    def fake_list_responses(db, query):
        captured["query"] = query
        return ResponseActionListResponse(items=[], meta=_meta("status"))

    monkeypatch.setattr(responses_route, "list_response_actions", fake_list_responses)

    try:
        client = TestClient(app)
        response = client.get(
            "/responses",
            params={
                "search": "disable_user",
                "mode": "dry-run",
                "execution_status": "warning",
                "action_type": "block_source_ip",
                "sort_by": "status",
                "sort_direction": "asc",
            },
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    query = captured["query"]
    assert query.mode == ResponseModeLabel.DRY_RUN
    assert query.execution_status == ResponseExecutionStatusLabel.WARNING
    assert query.action_type == "block_source_ip"
