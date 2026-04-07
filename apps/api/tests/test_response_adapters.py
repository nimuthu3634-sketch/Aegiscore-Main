from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.models.containment_flag import ContainmentFlag
from app.models.enums import IncidentPriority, IncidentStatus, ResponseActionType, ResponseMode, ResponseStatus
from app.models.incident import Incident
from app.services.response_automation.adapters import AdapterContext, execute_adapter
from app.services.response_automation import adapters


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def scalar(self, statement):  # noqa: ANN001
        return None

    def get(self, model, obj_id):  # noqa: ANN001
        for candidate in self.added:
            if isinstance(candidate, model) and getattr(candidate, "id", None) == obj_id:
                return candidate
        return None


def _settings(**overrides: object) -> SimpleNamespace:
    defaults = {
        "automated_response_allow_destructive": False,
        "automated_response_builtin_adapters_enabled": True,
        "automated_response_lab_adapters_enabled": True,
        "automated_response_block_ip_backend": "ledger",
        "automated_response_disable_user_backend": "ledger",
        "automated_response_ledger_path": "/tmp/aegiscore-test-ledger.jsonl",
        "automated_response_host_tag_path": "/tmp/aegiscore-test-host-tags.jsonl",
        "automated_response_enable_host_tag_write": False,
        "response_adapter_block_ip_script": None,
        "response_adapter_disable_user_script": None,
        "notifications_enabled": True,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _context(
    session: FakeSession,
    *,
    action: ResponseActionType,
    mode: ResponseMode = ResponseMode.LIVE,
    target: str | None = None,
) -> AdapterContext:
    incident = Incident(
        id=uuid4(),
        title="Adapter test incident",
        summary="Test summary",
        status=IncidentStatus.INVESTIGATING,
        priority=IncidentPriority.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(incident)
    return AdapterContext(
        session=session,
        action_type=action,
        mode=mode,
        target_value=target,
        policy_name="test-policy",
        payload={
            "incident": {
                "id": str(incident.id),
                "title": incident.title,
                "status": incident.status.value,
                "priority": incident.priority.value,
            }
        },
    )


def test_block_ip_dry_run_remains_non_destructive() -> None:
    session = FakeSession()
    result = execute_adapter(
        _context(
            session,
            action=ResponseActionType.BLOCK_IP,
            mode=ResponseMode.DRY_RUN,
            target="203.0.113.10",
        ),
        settings=_settings(),
    )
    assert result.status == ResponseStatus.COMPLETED
    assert "Dry-run: would execute block_ip" in result.summary


def test_block_ip_live_ledger_completes(monkeypatch) -> None:
    session = FakeSession()
    monkeypatch.setattr(adapters, "_append_json_line", lambda path, payload: None)
    result = execute_adapter(
        _context(session, action=ResponseActionType.BLOCK_IP, target="203.0.113.10"),
        settings=_settings(),
    )
    assert result.status == ResponseStatus.COMPLETED
    assert result.details["backend"] == "ledger"
    assert result.details["adapter_contract"]["action"] == "block_ip"


def test_disable_user_live_rejects_unsafe_username() -> None:
    session = FakeSession()
    result = execute_adapter(
        _context(session, action=ResponseActionType.DISABLE_USER, target="bad user"),
        settings=_settings(),
    )
    assert result.status == ResponseStatus.WARNING
    assert "safe Linux username" in result.message


def test_block_ip_live_ledger_write_failure_marks_failed(monkeypatch) -> None:
    session = FakeSession()

    def _raise_ledger_error(path, payload):  # noqa: ANN001
        raise OSError("ledger unavailable")

    monkeypatch.setattr(adapters, "_append_json_line", _raise_ledger_error)
    result = execute_adapter(
        _context(session, action=ResponseActionType.BLOCK_IP, target="203.0.113.10"),
        settings=_settings(),
    )
    assert result.status == ResponseStatus.FAILED
    assert "ledger unavailable" in result.message
    assert result.details["backend"] == "ledger"


def test_quarantine_host_flag_persists_containment_state(monkeypatch) -> None:
    session = FakeSession()
    monkeypatch.setattr(adapters, "_append_json_line", lambda path, payload: None)
    result = execute_adapter(
        _context(session, action=ResponseActionType.QUARANTINE_HOST_FLAG, target="edge-auth-01"),
        settings=_settings(automated_response_enable_host_tag_write=True),
    )
    assert result.status == ResponseStatus.COMPLETED
    assert any(isinstance(item, ContainmentFlag) for item in session.added)


def test_manual_review_ledger_failure_returns_warning_with_audit(monkeypatch) -> None:
    session = FakeSession()

    def _raise_ledger_error(path, payload):  # noqa: ANN001
        raise OSError("manual review ledger blocked")

    monkeypatch.setattr(adapters, "_append_json_line", _raise_ledger_error)
    result = execute_adapter(
        _context(session, action=ResponseActionType.CREATE_MANUAL_REVIEW, target="manual-review"),
        settings=_settings(),
    )
    assert result.status == ResponseStatus.WARNING
    assert "ledger blocked" in result.message
    assert result.details["manual_review_recorded"] is True
    assert result.details["manual_review_ledger_written"] is False


def test_notify_admin_live_reports_failure_from_notification_channel(monkeypatch) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        adapters,
        "send_admin_notification",
        lambda session, incident, trigger_value, response_action=None: [
            SimpleNamespace(status="failed", error_message="smtp down"),
        ],
    )
    result = execute_adapter(
        _context(session, action=ResponseActionType.NOTIFY_ADMIN, target="AegisCore administrators"),
        settings=_settings(),
    )
    assert result.status == ResponseStatus.FAILED
    assert "smtp down" in result.message


def test_notify_admin_live_partial_delivery_returns_warning(monkeypatch) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        adapters,
        "send_admin_notification",
        lambda session, incident, trigger_value, response_action=None: [
            SimpleNamespace(status="sent", error_message=None),
            SimpleNamespace(status="failed", error_message="smtp down"),
        ],
    )
    result = execute_adapter(
        _context(session, action=ResponseActionType.NOTIFY_ADMIN, target="AegisCore administrators"),
        settings=_settings(),
    )
    assert result.status == ResponseStatus.WARNING
    assert result.details["attempted"] == 2
    assert result.details["delivered"] == 1
    assert result.details["failed"] == 1
