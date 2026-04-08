from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.models.enums import IncidentPriority, IncidentStatus, ResponseMode, ResponseStatus
from app.models.incident import Incident
from app.models.response_action import ResponseAction
from app.services.notifications import service as notifications


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.flushed = 0

    def add(self, obj: object) -> None:
        if hasattr(obj, "id") and getattr(obj, "id", None) is None:
            setattr(obj, "id", uuid4())
        self.added.append(obj)

    def flush(self) -> None:
        self.flushed += 1

    def scalar(self, statement):  # noqa: ANN001
        return None


def _settings(**overrides: object) -> SimpleNamespace:
    defaults = {
        "notifications_enabled": True,
        "notifications_mode": "log",
        "notifications_risk_threshold": 85,
        "notifications_incident_states": "triaged,investigating,contained",
        "notifications_response_statuses": "warning,failed",
        "notifications_response_action_types": "*",
        "notifications_admin_recipients": "admin1@aegiscore.local,admin2@aegiscore.local",
        "notifications_sender": "aegiscore@localhost",
        "smtp_host": "localhost",
        "smtp_port": 1025,
        "smtp_username": None,
        "smtp_password": None,
        "smtp_use_tls": False,
        "smtp_use_starttls": False,
        "smtp_timeout_seconds": 10.0,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _build_incident() -> Incident:
    now = datetime.now(UTC)
    return Incident(
        id=uuid4(),
        title="Critical file integrity drift",
        summary="Potential tampering on a protected endpoint.",
        status=IncidentStatus.INVESTIGATING,
        priority=IncidentPriority.HIGH,
        created_at=now,
        updated_at=now,
    )


def _build_response_action(incident: Incident, status: ResponseStatus) -> ResponseAction:
    return ResponseAction(
        id=uuid4(),
        incident=incident,
        action_type="notify_admin",
        status=status,
        mode=ResponseMode.LIVE,
        target_value="AegisCore administrators",
        details={},
        created_at=datetime.now(UTC),
        executed_at=datetime.now(UTC),
    )


def test_notify_for_high_risk_incident_records_log_mode_events(monkeypatch) -> None:
    session = FakeSession()
    incident = _build_incident()

    monkeypatch.setattr(notifications, "get_settings", lambda: _settings())
    monkeypatch.setattr(notifications, "_existing_event_by_dedupe", lambda session, dedupe_key: None)

    events = notifications.notify_for_high_risk_incident(
        session,
        incident=incident,
        risk_score=91,
    )

    assert len(events) == 2
    assert all(event.status == "sent" for event in events)
    assert all(event.trigger_type == "risk_threshold" for event in events)


def test_notify_for_response_result_records_failure_when_smtp_fails(monkeypatch) -> None:
    session = FakeSession()
    incident = _build_incident()
    response_action = _build_response_action(incident, ResponseStatus.FAILED)

    monkeypatch.setattr(
        notifications,
        "get_settings",
        lambda: _settings(notifications_mode="smtp", notifications_admin_recipients="soc@aegiscore.local"),
    )
    monkeypatch.setattr(notifications, "_existing_event_by_dedupe", lambda session, dedupe_key: None)
    monkeypatch.setattr(
        notifications,
        "_send_via_smtp",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("SMTP unavailable")),
    )

    events = notifications.notify_for_response_result(
        session,
        incident=incident,
        response_action=response_action,
    )

    assert len(events) == 1
    assert events[0].status == "failed"
    assert "SMTP unavailable" in (events[0].error_message or "")


def test_notify_for_response_result_smtp_success(monkeypatch) -> None:
    session = FakeSession()
    incident = _build_incident()
    response_action = _build_response_action(incident, ResponseStatus.WARNING)
    sent: dict[str, object] = {}

    monkeypatch.setattr(
        notifications,
        "get_settings",
        lambda: _settings(notifications_mode="smtp", notifications_admin_recipients="soc@aegiscore.local"),
    )
    monkeypatch.setattr(notifications, "_existing_event_by_dedupe", lambda session, dedupe_key: None)
    monkeypatch.setattr(
        notifications,
        "_send_via_smtp",
        lambda **kwargs: sent.update(kwargs),
    )

    events = notifications.notify_for_response_result(
        session,
        incident=incident,
        response_action=response_action,
    )

    assert len(events) == 1
    assert events[0].status == "sent"
    assert events[0].details.get("mode") == "smtp"
    assert sent.get("recipient") == "soc@aegiscore.local"
    assert "AegisCore" in str(sent.get("subject", ""))


def test_notify_for_response_result_skips_disallowed_action_types(monkeypatch) -> None:
    session = FakeSession()
    incident = _build_incident()
    response_action = _build_response_action(incident, ResponseStatus.FAILED)
    response_action.action_type = "block_ip"

    monkeypatch.setattr(
        notifications,
        "get_settings",
        lambda: _settings(
            notifications_response_action_types="notify_admin,quarantine_host_flag",
        ),
    )

    events = notifications.notify_for_response_result(
        session,
        incident=incident,
        response_action=response_action,
    )

    assert events == []


def test_log_mode_delivery_writes_audit_entries(monkeypatch) -> None:
    session = FakeSession()
    incident = _build_incident()
    audit_creates: list[object] = []

    class FakeAuditRepo:
        def __init__(self, _session):  # noqa: ANN001
            pass

        def create(self, log):  # noqa: ANN001
            audit_creates.append(log)
            return log

    monkeypatch.setattr(notifications, "get_settings", lambda: _settings())
    monkeypatch.setattr(notifications, "_existing_event_by_dedupe", lambda session, dedupe_key: None)
    monkeypatch.setattr(notifications, "AuditLogsRepository", FakeAuditRepo)

    notifications.notify_for_high_risk_incident(
        session,
        incident=incident,
        risk_score=91,
    )

    assert len(audit_creates) >= 2
    assert any(getattr(log, "entity_type", None) == "notification" for log in audit_creates)
    assert any(getattr(log, "entity_type", None) == "incident" for log in audit_creates)


def test_notify_for_incident_state_respects_state_filter(monkeypatch) -> None:
    session = FakeSession()
    incident = _build_incident()
    incident.status = IncidentStatus.RESOLVED

    monkeypatch.setattr(notifications, "get_settings", lambda: _settings())

    events = notifications.notify_for_incident_state(
        session,
        incident=incident,
        previous_state="investigating",
    )

    assert events == []
