from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.models.asset import Asset
from app.models.audit_log import AuditLog
from app.models.enums import (
    AlertStatus,
    AssetCriticality,
    DetectionType,
    IncidentPriority,
    IncidentStatus,
    ResponseActionType,
    ResponseMode,
    ResponsePolicyTarget,
    ResponseStatus,
    ScoreMethod,
)
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.response_action import ResponseAction
from app.models.response_policy import ResponsePolicy
from app.models.risk_score import RiskScore
from app.repositories.policies import PoliciesRepository
from app.repositories.responses import ResponsesRepository
from app.services.response_automation import adapters, execution


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        if hasattr(obj, "id") and getattr(obj, "id", None) is None:
            setattr(obj, "id", uuid4())
        self.added.append(obj)

    def flush(self) -> None:
        return None

    def refresh(self, obj: object) -> None:
        if isinstance(obj, NormalizedAlert):
            for candidate in self.added:
                if isinstance(candidate, Incident) and candidate.id == obj.incident_id:
                    obj.incident = candidate
                    if obj not in candidate.alerts:
                        candidate.alerts.append(obj)
                    break
        if isinstance(obj, Incident):
            for candidate in self.added:
                if isinstance(candidate, NormalizedAlert) and candidate.id == obj.primary_alert_id:
                    obj.primary_alert = candidate
                    if obj not in [candidate.incident] and candidate.incident is None:
                        candidate.incident = obj
                    break
            linked_responses = [
                candidate
                for candidate in self.added
                if isinstance(candidate, ResponseAction) and candidate.incident_id == obj.id
            ]
            obj.response_actions = linked_responses

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
        "automated_response_max_retries": 1,
        "response_adapter_block_ip_script": None,
        "response_adapter_disable_user_script": None,
        "response_adapter_quarantine_host_flag_script": None,
        "response_adapter_create_manual_review_script": None,
        "response_adapter_notify_admin_script": None,
        "automated_response_builtin_adapters_enabled": True,
        "automated_response_lab_adapters_enabled": True,
        "automated_response_block_ip_backend": "ledger",
        "automated_response_disable_user_backend": "ledger",
        "automated_response_ledger_path": "/tmp/aegiscore-test-ledger.jsonl",
        "automated_response_host_tag_path": "/tmp/aegiscore-test-host-tags.jsonl",
        "automated_response_enable_host_tag_write": False,
        "notifications_enabled": False,
        "notifications_mode": "log",
        "notifications_risk_threshold": 85,
        "notifications_incident_states": "triaged,investigating,contained",
        "notifications_response_statuses": "warning,failed",
        "notifications_response_action_types": "*",
        "notifications_admin_recipients": "admin@aegiscore.local",
        "notifications_sender": "aegiscore@localhost",
        "smtp_host": "localhost",
        "smtp_port": 1025,
        "smtp_username": None,
        "smtp_password": None,
        "smtp_use_tls": False,
        "smtp_use_starttls": False,
        "smtp_timeout_seconds": 10.0,
    }
    defaults.setdefault("automated_response_ml_brute_force_enabled", True)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _build_alert(
    *,
    detection_type: DetectionType,
    score: float,
    source: str = "wazuh",
    severity: int = 9,
    raw_payload: dict | None = None,
    normalized_payload: dict | None = None,
    scoring_method: ScoreMethod = ScoreMethod.BASELINE_RULES,
    priority_label: IncidentPriority | None = None,
    explanation: dict | None = None,
    feature_snapshot: dict | None = None,
) -> NormalizedAlert:
    now = datetime.now(UTC)
    asset = Asset(
        id=uuid4(),
        hostname="edge-auth-01",
        ip_address="10.10.20.15",
        operating_system="Ubuntu 24.04",
        criticality=AssetCriticality.HIGH,
        created_at=now,
        updated_at=now,
    )
    raw_alert = RawAlert(
        id=uuid4(),
        asset=asset,
        source=source,
        external_id=f"{source}-evt-1",
        detection_type=detection_type,
        severity=severity,
        raw_payload=raw_payload or {},
        received_at=now,
    )
    alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=raw_alert,
        asset=asset,
        source=source,
        title=f"{detection_type.value} detected",
        description="Normalized alert for automated response testing.",
        detection_type=detection_type,
        severity=severity,
        status=AlertStatus.NEW,
        normalized_payload=normalized_payload or {},
        created_at=now,
    )
    pl = priority_label or (
        IncidentPriority.CRITICAL if score >= 85 else IncidentPriority.HIGH
    )
    alert.risk_score = RiskScore(
        id=uuid4(),
        normalized_alert=alert,
        score=score,
        confidence=0.93,
        priority_label=pl,
        scoring_method=scoring_method,
        reasoning="Synthetic scoring fixture for automated response tests.",
        explanation=explanation or {"summary": "Scored for automated response testing."},
        feature_snapshot=feature_snapshot or {"repeated_event_count": 5},
        calculated_at=now,
    )
    return alert


def _build_incident(alert: NormalizedAlert) -> Incident:
    now = datetime.now(UTC)
    incident = Incident(
        id=uuid4(),
        title=f"Incident for {alert.detection_type.value}",
        summary="Incident fixture for automated response tests.",
        status=IncidentStatus.INVESTIGATING,
        priority=IncidentPriority.HIGH,
        created_at=now,
        updated_at=now,
    )
    incident.primary_alert = alert
    incident.alerts = [alert]
    alert.incident = incident
    return incident


def _build_policy(
    *,
    target: ResponsePolicyTarget,
    detection_type: DetectionType,
    action_type: ResponseActionType,
    mode: ResponseMode,
    min_risk_score: int,
) -> ResponsePolicy:
    now = datetime.now(UTC)
    return ResponsePolicy(
        id=uuid4(),
        name=f"{action_type.value}-{target.value}",
        description="Policy fixture",
        enabled=True,
        target=target,
        detection_type=detection_type,
        min_risk_score=min_risk_score,
        action_type=action_type,
        mode=mode,
        config={"source": "test"},
        created_at=now,
        updated_at=now,
    )


def _audit_actions(session: FakeSession) -> list[str]:
    return [obj.action for obj in session.added if isinstance(obj, AuditLog)]


def test_evaluate_alert_policies_executes_dry_run_for_high_risk_alert(monkeypatch) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.BRUTE_FORCE,
        score=95,
        raw_payload={"source_ip": "198.51.100.20", "username": "svc-admin"},
        normalized_payload={"source_ip": "198.51.100.20"},
    )
    policy = _build_policy(
        target=ResponsePolicyTarget.ALERT,
        detection_type=DetectionType.BRUTE_FORCE,
        action_type=ResponseActionType.BLOCK_IP,
        mode=ResponseMode.DRY_RUN,
        min_risk_score=85,
    )

    monkeypatch.setattr(
        execution,
        "get_settings",
        lambda: _settings(automated_response_block_ip_backend="iptables"),
    )
    monkeypatch.setattr(
        PoliciesRepository,
        "find_matching_policies",
        lambda self, **kwargs: [policy],
    )
    monkeypatch.setattr(
        ResponsesRepository,
        "find_existing_policy_action",
        lambda self, **kwargs: None,
    )

    responses = execution.evaluate_alert_policies(session, alert)

    assert len(responses) == 1
    response = responses[0]
    assert response.status == ResponseStatus.COMPLETED
    assert response.mode == ResponseMode.DRY_RUN
    assert response.target_value == "198.51.100.20"
    assert response.attempt_count == 1
    assert response.incident is alert.incident
    assert alert.incident is not None
    assert "Dry-run: would execute block_ip" in (response.result_summary or "")
    assert "Policy block_ip-alert matched" in (response.result_message or "")

    audit_actions = _audit_actions(session)
    assert "incident.created.automated_response" in audit_actions
    assert "response.policy_matched" in audit_actions
    assert "response.execution_completed" in audit_actions


def test_evaluate_alert_policies_blocks_live_destructive_action_by_default(monkeypatch) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.BRUTE_FORCE,
        score=97,
        raw_payload={"source_ip": "203.0.113.8"},
    )
    policy = _build_policy(
        target=ResponsePolicyTarget.ALERT,
        detection_type=DetectionType.BRUTE_FORCE,
        action_type=ResponseActionType.BLOCK_IP,
        mode=ResponseMode.LIVE,
        min_risk_score=90,
    )

    monkeypatch.setattr(
        execution,
        "get_settings",
        lambda: _settings(automated_response_block_ip_backend="iptables"),
    )
    monkeypatch.setattr(
        PoliciesRepository,
        "find_matching_policies",
        lambda self, **kwargs: [policy],
    )
    monkeypatch.setattr(
        ResponsesRepository,
        "find_existing_policy_action",
        lambda self, **kwargs: None,
    )

    response = execution.evaluate_alert_policies(session, alert)[0]

    assert response.status == ResponseStatus.WARNING
    assert response.attempt_count == 1
    assert response.details["blocked_by_safety"] is True
    assert "AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE" in (response.result_message or "")
    assert "response.execution_warning" in _audit_actions(session)


def test_evaluate_incident_policies_uses_stubbed_live_adapter(monkeypatch) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.PORT_SCAN,
        score=82,
        source="suricata",
        severity=7,
        raw_payload={"src_ip": "198.51.100.44", "dst_port": "443"},
    )
    incident = _build_incident(alert)
    policy = _build_policy(
        target=ResponsePolicyTarget.INCIDENT,
        detection_type=DetectionType.PORT_SCAN,
        action_type=ResponseActionType.NOTIFY_ADMIN,
        mode=ResponseMode.LIVE,
        min_risk_score=75,
    )

    monkeypatch.setattr(execution, "get_settings", lambda: _settings(notifications_enabled=True))
    monkeypatch.setattr(
        PoliciesRepository,
        "find_matching_policies",
        lambda self, **kwargs: [policy],
    )
    monkeypatch.setattr(
        ResponsesRepository,
        "find_existing_policy_action",
        lambda self, **kwargs: None,
    )
    monkeypatch.setattr(
        adapters,
        "send_admin_notification",
        lambda session, incident, trigger_value, response_action=None: [
            SimpleNamespace(status="sent", error_message=None),
        ],
    )
    session.add(incident)

    response = execution.evaluate_incident_policies(session, incident)[0]

    assert response.status == ResponseStatus.COMPLETED
    assert response.mode == ResponseMode.LIVE
    assert response.target_value == "AegisCore administrators"
    assert "built-in notification service" in (response.result_summary or "")
    assert "Notification events created for 1 recipients." == response.result_message
    assert response.attempt_count == 1


def test_evaluate_incident_policies_retries_and_logs_failed_execution(monkeypatch) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.PORT_SCAN,
        score=88,
        source="suricata",
        severity=7,
        raw_payload={"src_ip": "198.51.100.77"},
    )
    incident = _build_incident(alert)
    policy = _build_policy(
        target=ResponsePolicyTarget.INCIDENT,
        detection_type=DetectionType.PORT_SCAN,
        action_type=ResponseActionType.NOTIFY_ADMIN,
        mode=ResponseMode.LIVE,
        min_risk_score=75,
    )

    monkeypatch.setattr(
        execution,
        "get_settings",
        lambda: _settings(automated_response_max_retries=2, notifications_enabled=True),
    )
    monkeypatch.setattr(
        PoliciesRepository,
        "find_matching_policies",
        lambda self, **kwargs: [policy],
    )
    monkeypatch.setattr(
        ResponsesRepository,
        "find_existing_policy_action",
        lambda self, **kwargs: None,
    )
    monkeypatch.setattr(
        adapters,
        "send_admin_notification",
        lambda session, incident, trigger_value, response_action=None: [
            SimpleNamespace(status="failed", error_message="adapter unavailable"),
        ],
    )
    session.add(incident)

    response = execution.evaluate_incident_policies(session, incident)[0]

    assert response.status == ResponseStatus.FAILED
    assert response.attempt_count == 2
    assert response.result_message == "adapter unavailable"

    audit_actions = _audit_actions(session)
    assert audit_actions.count("response.execution_attempted") == 2
    assert "response.execution_failed" in audit_actions


def test_evaluate_incident_policies_for_alert_auto_creates_incident_for_port_scan(
    monkeypatch,
) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.PORT_SCAN,
        score=82,
        source="suricata",
        severity=7,
        raw_payload={"src_ip": "198.51.100.44", "dst_port": "443"},
        normalized_payload={
            "source_ip": "198.51.100.44",
            "destination_port": 443,
        },
    )
    session.add(alert)
    policy = _build_policy(
        target=ResponsePolicyTarget.INCIDENT,
        detection_type=DetectionType.PORT_SCAN,
        action_type=ResponseActionType.NOTIFY_ADMIN,
        mode=ResponseMode.DRY_RUN,
        min_risk_score=75,
    )

    monkeypatch.setattr(execution, "get_settings", lambda: _settings())
    monkeypatch.setattr(
        PoliciesRepository,
        "find_matching_policies",
        lambda self, **kwargs: [policy],
    )
    monkeypatch.setattr(
        ResponsesRepository,
        "find_existing_policy_action",
        lambda self, **kwargs: None,
    )

    response = execution.evaluate_incident_policies_for_alert(session, alert)[0]

    assert alert.incident is not None
    assert response.status == ResponseStatus.COMPLETED
    assert response.mode == ResponseMode.DRY_RUN
    assert response.incident is alert.incident
    assert "notify_admin" in (response.result_summary or "")
    assert "incident.created.automated_response" in _audit_actions(session)


def test_evaluate_alert_policies_records_live_manual_review_for_file_integrity(
    monkeypatch,
) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        score=91,
        raw_payload={"path": "D:\\Operations\\Policies\\access-control.xlsx"},
        normalized_payload={
            "file_path": "D:\\Operations\\Policies\\access-control.xlsx"
        },
    )
    policy = _build_policy(
        target=ResponsePolicyTarget.ALERT,
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        action_type=ResponseActionType.CREATE_MANUAL_REVIEW,
        mode=ResponseMode.LIVE,
        min_risk_score=80,
    )

    monkeypatch.setattr(execution, "get_settings", lambda: _settings())
    monkeypatch.setattr(
        PoliciesRepository,
        "find_matching_policies",
        lambda self, **kwargs: [policy],
    )
    monkeypatch.setattr(
        ResponsesRepository,
        "find_existing_policy_action",
        lambda self, **kwargs: None,
    )

    response = execution.evaluate_alert_policies(session, alert)[0]

    assert response.status == ResponseStatus.COMPLETED
    assert response.mode == ResponseMode.LIVE
    assert response.result_summary == "Manual review workflow opened."
    assert response.details["manual_review_recorded"] is True
    assert "response.execution_completed" in _audit_actions(session)


def test_evaluate_alert_policies_records_live_admin_notification_for_user_creation(
    monkeypatch,
) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.UNAUTHORIZED_USER_CREATION,
        score=96,
        raw_payload={"username": "unknown-admin"},
        normalized_payload={
            "username": "unknown-admin",
            "group_name": "Domain Admins",
        },
    )
    policy = _build_policy(
        target=ResponsePolicyTarget.ALERT,
        detection_type=DetectionType.UNAUTHORIZED_USER_CREATION,
        action_type=ResponseActionType.NOTIFY_ADMIN,
        mode=ResponseMode.LIVE,
        min_risk_score=90,
    )

    monkeypatch.setattr(execution, "get_settings", lambda: _settings(notifications_enabled=True))
    monkeypatch.setattr(
        adapters,
        "send_admin_notification",
        lambda session, incident, trigger_value, response_action=None: [
            SimpleNamespace(status="sent", error_message=None),
        ],
    )
    monkeypatch.setattr(
        PoliciesRepository,
        "find_matching_policies",
        lambda self, **kwargs: [policy],
    )
    monkeypatch.setattr(
        ResponsesRepository,
        "find_existing_policy_action",
        lambda self, **kwargs: None,
    )

    response = execution.evaluate_alert_policies(session, alert)[0]

    assert response.status == ResponseStatus.COMPLETED
    assert response.mode == ResponseMode.LIVE
    assert response.target_value == "AegisCore administrators"
    assert "built-in notification service" in (response.result_summary or "")
    assert response.details["delivered"] == 1
    assert "response.execution_completed" in _audit_actions(session)


def test_ml_brute_force_auto_block_executes_when_all_gates_met(monkeypatch) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.BRUTE_FORCE,
        score=80,
        raw_payload={"source_ip": "198.51.100.50"},
        normalized_payload={"source_ip": "198.51.100.50"},
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        priority_label=IncidentPriority.HIGH,
        explanation={"model_priority_tier": "high", "summary": "TF"},
        feature_snapshot={
            "source_ip": "198.51.100.50",
            "failed_logins_5m": 12,
            "detection_type": "brute_force",
        },
    )
    monkeypatch.setattr(
        execution,
        "get_settings",
        lambda: _settings(automated_response_block_ip_backend="ledger"),
    )
    monkeypatch.setattr(
        PoliciesRepository,
        "find_matching_policies",
        lambda self, **kwargs: [],
    )
    monkeypatch.setattr(
        ResponsesRepository,
        "find_existing_automation_action",
        lambda self, **kwargs: None,
    )
    monkeypatch.setattr(
        ResponsesRepository,
        "find_existing_policy_action",
        lambda self, **kwargs: None,
    )

    responses = execution.evaluate_alert_policies(session, alert)

    assert len(responses) == 1
    r = responses[0]
    assert r.policy_id is None
    assert r.action_type == ResponseActionType.BLOCK_IP.value
    assert r.target_value == "198.51.100.50"
    assert (r.details or {}).get("automation_rule") == "ml_brute_force_auto_block_v1"
    ev = (r.details or {}).get("ml_brute_force_evaluation") or {}
    assert ev.get("thresholds", {}).get("required_failed_logins_5m") == 10
    assert ev.get("checks", {}).get("failed_logins_5m_meets_threshold") is True
    assert "response.builtin_automation_matched" in _audit_actions(session)


def test_ml_brute_force_auto_block_skipped_when_failed_logins_below_threshold(monkeypatch) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.BRUTE_FORCE,
        score=80,
        raw_payload={"source_ip": "198.51.100.50"},
        normalized_payload={"source_ip": "198.51.100.50"},
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        priority_label=IncidentPriority.HIGH,
        explanation={"model_priority_tier": "high"},
        feature_snapshot={"source_ip": "198.51.100.50", "failed_logins_5m": 5},
    )
    monkeypatch.setattr(execution, "get_settings", lambda: _settings())
    monkeypatch.setattr(PoliciesRepository, "find_matching_policies", lambda self, **kwargs: [])

    assert execution.evaluate_alert_policies(session, alert) == []


def test_ml_brute_force_auto_block_skipped_for_non_brute_high_risk(monkeypatch) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.PORT_SCAN,
        score=80,
        raw_payload={"source_ip": "198.51.100.51"},
        normalized_payload={"source_ip": "198.51.100.51"},
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        priority_label=IncidentPriority.HIGH,
        explanation={"model_priority_tier": "high"},
        feature_snapshot={"source_ip": "198.51.100.51", "failed_logins_5m": 25},
    )
    monkeypatch.setattr(execution, "get_settings", lambda: _settings())
    monkeypatch.setattr(PoliciesRepository, "find_matching_policies", lambda self, **kwargs: [])

    assert execution.evaluate_alert_policies(session, alert) == []


def test_ml_brute_force_auto_block_skipped_for_file_integrity_high_even_with_failed_logins(
    monkeypatch,
) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        score=80,
        raw_payload={"source_ip": "198.51.100.60"},
        normalized_payload={"source_ip": "198.51.100.60"},
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        priority_label=IncidentPriority.HIGH,
        explanation={"model_priority_tier": "high"},
        feature_snapshot={
            "source_ip": "198.51.100.60",
            "failed_logins_5m": 15,
            "detection_type": "file_integrity_violation",
        },
    )
    monkeypatch.setattr(execution, "get_settings", lambda: _settings())
    monkeypatch.setattr(PoliciesRepository, "find_matching_policies", lambda self, **kwargs: [])

    assert execution.evaluate_alert_policies(session, alert) == []


def test_ml_brute_force_auto_block_skipped_for_unauthorized_user_creation_high(
    monkeypatch,
) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.UNAUTHORIZED_USER_CREATION,
        score=80,
        raw_payload={"source_ip": "198.51.100.61"},
        normalized_payload={"source_ip": "198.51.100.61"},
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        priority_label=IncidentPriority.HIGH,
        explanation={"model_priority_tier": "high"},
        feature_snapshot={
            "source_ip": "198.51.100.61",
            "failed_logins_5m": 12,
            "detection_type": "unauthorized_user_creation",
        },
    )
    monkeypatch.setattr(execution, "get_settings", lambda: _settings())
    monkeypatch.setattr(PoliciesRepository, "find_matching_policies", lambda self, **kwargs: [])

    assert execution.evaluate_alert_policies(session, alert) == []


def test_ml_brute_force_auto_block_skipped_when_source_ip_missing(monkeypatch) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.BRUTE_FORCE,
        score=80,
        raw_payload={},
        normalized_payload={},
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        priority_label=IncidentPriority.HIGH,
        explanation={"model_priority_tier": "high"},
        feature_snapshot={"failed_logins_5m": 15},
    )
    monkeypatch.setattr(execution, "get_settings", lambda: _settings())
    monkeypatch.setattr(PoliciesRepository, "find_matching_policies", lambda self, **kwargs: [])

    assert execution.evaluate_alert_policies(session, alert) == []


def test_ml_brute_force_not_duplicated_when_policy_already_blocks_ip(monkeypatch) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.BRUTE_FORCE,
        score=95,
        raw_payload={"source_ip": "198.51.100.50"},
        normalized_payload={"source_ip": "198.51.100.50"},
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        priority_label=IncidentPriority.HIGH,
        explanation={"model_priority_tier": "high"},
        feature_snapshot={"source_ip": "198.51.100.50", "failed_logins_5m": 12},
    )
    policy = _build_policy(
        target=ResponsePolicyTarget.ALERT,
        detection_type=DetectionType.BRUTE_FORCE,
        action_type=ResponseActionType.BLOCK_IP,
        mode=ResponseMode.DRY_RUN,
        min_risk_score=70,
    )
    monkeypatch.setattr(
        execution,
        "get_settings",
        lambda: _settings(automated_response_block_ip_backend="ledger"),
    )
    monkeypatch.setattr(
        PoliciesRepository,
        "find_matching_policies",
        lambda self, **kwargs: [policy],
    )
    monkeypatch.setattr(
        ResponsesRepository,
        "find_existing_policy_action",
        lambda self, **kwargs: None,
    )

    responses = execution.evaluate_alert_policies(session, alert)
    assert len(responses) == 1
    assert (responses[0].details or {}).get("automation_rule") is None
    assert (responses[0].details or {}).get("policy_snapshot") is not None


def test_ml_brute_force_auto_block_skipped_when_disabled(monkeypatch) -> None:
    session = FakeSession()
    alert = _build_alert(
        detection_type=DetectionType.BRUTE_FORCE,
        score=80,
        raw_payload={"source_ip": "198.51.100.50"},
        normalized_payload={"source_ip": "198.51.100.50"},
        scoring_method=ScoreMethod.TENSORFLOW_MODEL,
        priority_label=IncidentPriority.HIGH,
        explanation={"model_priority_tier": "high"},
        feature_snapshot={"source_ip": "198.51.100.50", "failed_logins_5m": 12},
    )
    monkeypatch.setattr(
        execution,
        "get_settings",
        lambda: _settings(automated_response_ml_brute_force_enabled=False),
    )
    monkeypatch.setattr(PoliciesRepository, "find_matching_policies", lambda self, **kwargs: [])

    assert execution.evaluate_alert_policies(session, alert) == []
