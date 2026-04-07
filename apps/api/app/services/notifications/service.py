from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import EmailMessage
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.audit_log import AuditLog
from app.models.incident import Incident
from app.models.notification_event import NotificationEvent
from app.models.response_action import ResponseAction
from app.repositories.audit_logs import AuditLogsRepository

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class NotificationDecision:
    should_notify: bool
    reason: str


def _csv_set(value: str) -> set[str]:
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def _recipient_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _notification_subject(incident: Incident, trigger_type: str) -> str:
    return f"[AegisCore] Incident {incident.priority.value} - {incident.title} ({trigger_type})"


def _notification_body(
    incident: Incident,
    *,
    trigger_type: str,
    trigger_value: str,
    response_action: ResponseAction | None,
) -> str:
    lines = [
        "AegisCore incident notification",
        "",
        f"Incident ID: {incident.id}",
        f"Title: {incident.title}",
        f"Priority: {incident.priority.value}",
        f"State: {incident.status.value}",
        f"Trigger type: {trigger_type}",
        f"Trigger value: {trigger_value}",
    ]
    if response_action is not None:
        lines.extend(
            [
                f"Response action ID: {response_action.id}",
                f"Response action type: {response_action.action_type}",
                f"Response status: {response_action.status.value}",
            ]
        )
    if incident.summary:
        lines.extend(["", "Summary:", incident.summary])
    return "\n".join(lines)


def _send_via_smtp(*, recipient: str, subject: str, body: str) -> None:
    settings = get_settings()
    message = EmailMessage()
    message["From"] = settings.notifications_sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    timeout = max(1.0, settings.smtp_timeout_seconds)
    if settings.smtp_use_tls:
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=timeout,
        ) as smtp:
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=timeout) as smtp:
        if settings.smtp_use_starttls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


def _record_audit(session: Session, *, event: NotificationEvent) -> None:
    action = (
        "notification.sent"
        if event.status == "sent"
        else "notification.failed"
        if event.status == "failed"
        else "notification.skipped"
    )
    details = {
        "channel": event.channel,
        "delivery_mode": event.delivery_mode,
        "trigger_type": event.trigger_type,
        "trigger_value": event.trigger_value,
        "recipient": event.recipient,
        "status": event.status,
        "error_message": event.error_message,
        "summary": f"Notification {event.status} for incident {event.incident_id}.",
    }
    AuditLogsRepository(session).create(
        AuditLog(
            actor=None,
            entity_type="notification",
            entity_id=str(event.id),
            action=action,
            details=details,
        )
    )
    AuditLogsRepository(session).create(
        AuditLog(
            actor=None,
            entity_type="incident",
            entity_id=str(event.incident_id),
            action=action,
            details=details,
        )
    )


def _existing_event_by_dedupe(session: Session, dedupe_key: str) -> NotificationEvent | None:
    return session.scalar(
        select(NotificationEvent).where(NotificationEvent.dedupe_key == dedupe_key)
    )


def _create_event(
    session: Session,
    *,
    incident: Incident,
    response_action: ResponseAction | None,
    recipient: str,
    subject: str,
    body: str,
    trigger_type: str,
    trigger_value: str,
    dedupe_key: str,
) -> NotificationEvent:
    event = NotificationEvent(
        incident=incident,
        response_action=response_action,
        channel="email",
        delivery_mode=get_settings().notifications_mode,
        trigger_type=trigger_type,
        trigger_value=trigger_value,
        recipient=recipient,
        subject=subject,
        body=body,
        status="queued",
        details={},
        dedupe_key=dedupe_key,
    )
    session.add(event)
    session.flush()
    return event


def _deliver_event(session: Session, event: NotificationEvent) -> NotificationEvent:
    settings = get_settings()
    mode = settings.notifications_mode.lower()
    if mode == "log":
        logger.info(
            "AegisCore notification (log mode) recipient=%s subject=%s",
            event.recipient,
            event.subject,
        )
        event.status = "sent"
        event.sent_at = datetime.now(UTC)
        event.details = {"mode": "log"}
        _record_audit(session, event=event)
        return event

    if mode != "smtp":
        event.status = "failed"
        event.error_message = f"Unsupported notifications mode: {settings.notifications_mode}"
        _record_audit(session, event=event)
        return event

    try:
        _send_via_smtp(recipient=event.recipient, subject=event.subject, body=event.body)
        event.status = "sent"
        event.sent_at = datetime.now(UTC)
        event.details = {"mode": "smtp"}
    except Exception as exc:  # pragma: no cover - runtime network branch
        event.status = "failed"
        event.error_message = str(exc)
    _record_audit(session, event=event)
    return event


def _decide_for_risk(*, risk_score: float, incident_state: str) -> NotificationDecision:
    settings = get_settings()
    if not settings.notifications_enabled:
        return NotificationDecision(False, "notifications_disabled")
    if risk_score < settings.notifications_risk_threshold:
        return NotificationDecision(False, "risk_below_threshold")
    if incident_state.lower() not in _csv_set(settings.notifications_incident_states):
        return NotificationDecision(False, "incident_state_not_notifiable")
    return NotificationDecision(True, "risk_threshold_matched")


def _decide_for_incident_state(*, incident_state: str) -> NotificationDecision:
    settings = get_settings()
    if not settings.notifications_enabled:
        return NotificationDecision(False, "notifications_disabled")
    if incident_state.lower() not in _csv_set(settings.notifications_incident_states):
        return NotificationDecision(False, "incident_state_not_notifiable")
    return NotificationDecision(True, "incident_state_matched")


def _decide_for_response_result(*, response_status: str) -> NotificationDecision:
    settings = get_settings()
    if not settings.notifications_enabled:
        return NotificationDecision(False, "notifications_disabled")
    if response_status.lower() not in _csv_set(settings.notifications_response_statuses):
        return NotificationDecision(False, "response_status_not_notifiable")
    return NotificationDecision(True, "response_status_matched")


def _notify_many(
    session: Session,
    *,
    incident: Incident,
    response_action: ResponseAction | None,
    trigger_type: str,
    trigger_value: str,
    dedupe_suffix: str,
) -> list[NotificationEvent]:
    recipients = _recipient_list(get_settings().notifications_admin_recipients)
    if not recipients:
        return []

    events: list[NotificationEvent] = []
    for recipient in recipients:
        dedupe_key = f"{incident.id}:{trigger_type}:{dedupe_suffix}:{recipient}"
        existing = _existing_event_by_dedupe(session, dedupe_key)
        if existing is not None:
            continue
        event = _create_event(
            session,
            incident=incident,
            response_action=response_action,
            recipient=recipient,
            subject=_notification_subject(incident, trigger_type),
            body=_notification_body(
                incident,
                trigger_type=trigger_type,
                trigger_value=trigger_value,
                response_action=response_action,
            ),
            trigger_type=trigger_type,
            trigger_value=trigger_value,
            dedupe_key=dedupe_key,
        )
        events.append(_deliver_event(session, event))
    return events


def notify_for_high_risk_incident(
    session: Session,
    *,
    incident: Incident,
    risk_score: float,
) -> list[NotificationEvent]:
    decision = _decide_for_risk(
        risk_score=risk_score,
        incident_state=incident.status.value,
    )
    if not decision.should_notify:
        return []
    bucket = int(risk_score)
    return _notify_many(
        session,
        incident=incident,
        response_action=None,
        trigger_type="risk_threshold",
        trigger_value=f"score={bucket}",
        dedupe_suffix=f"risk-{bucket}",
    )


def notify_for_incident_state(
    session: Session,
    *,
    incident: Incident,
    previous_state: str | None,
) -> list[NotificationEvent]:
    decision = _decide_for_incident_state(incident_state=incident.status.value)
    if not decision.should_notify:
        return []
    return _notify_many(
        session,
        incident=incident,
        response_action=None,
        trigger_type="incident_state",
        trigger_value=f"{previous_state or 'unknown'}->{incident.status.value}",
        dedupe_suffix=f"state-{incident.status.value}",
    )


def notify_for_response_result(
    session: Session,
    *,
    incident: Incident,
    response_action: ResponseAction,
) -> list[NotificationEvent]:
    decision = _decide_for_response_result(response_status=response_action.status.value)
    if not decision.should_notify:
        return []
    return _notify_many(
        session,
        incident=incident,
        response_action=response_action,
        trigger_type="response_result",
        trigger_value=f"{response_action.action_type}:{response_action.status.value}",
        dedupe_suffix=f"response-{response_action.id}-{response_action.status.value}",
    )


def send_admin_notification(
    session: Session,
    *,
    incident: Incident,
    trigger_value: str,
    response_action: ResponseAction | None = None,
) -> list[NotificationEvent]:
    settings = get_settings()
    if not settings.notifications_enabled:
        return []
    return _notify_many(
        session,
        incident=incident,
        response_action=response_action,
        trigger_type="notify_admin",
        trigger_value=trigger_value,
        dedupe_suffix=f"notify-admin-{trigger_value}",
    )


def list_incident_notifications(
    incident: Incident,
) -> list[NotificationEvent]:
    return sorted(incident.notification_events, key=lambda item: item.created_at, reverse=True)
