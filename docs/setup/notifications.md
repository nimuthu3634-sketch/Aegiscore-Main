# Notification Subsystem Setup

AegisCore supports SME-friendly critical-incident notifications from backend-owned logic with auditable persistence.

## Supported Channels

- `log` mode: safe development/local mode that records delivery as sent without external email transport
- `smtp` mode: real email delivery suitable for local mail sinks (for example MailHog/Mailpit) or lab SMTP

## Trigger Rules

Notifications are evaluated for:

- high-risk incidents (`risk_threshold`) after alert policy evaluation when score and incident state match configured filters
- incident state transitions (`incident_state`) when the new state is in the configured list
- response execution outcomes (`response_result`) when the final response status is in the configured list (for example `warning`, `failed`)
- explicit `notify_admin` automated-response actions (trigger type `notify_admin`), which bypass the response-status filter but still require `NOTIFICATIONS_ENABLED=true`

Optional narrowing for `response_result` triggers:

- `NOTIFICATIONS_RESPONSE_ACTION_TYPES`: comma-separated action types (for example `block_ip,notify_admin`) or `*` for all types (default).

Rules are controlled through environment configuration.

## Required Configuration

- `NOTIFICATIONS_ENABLED=true`
- `NOTIFICATIONS_MODE=log` or `smtp`
- `NOTIFICATIONS_ADMIN_RECIPIENTS=admin1@example.local,admin2@example.local`
- `NOTIFICATIONS_SENDER=aegiscore@localhost`
- `NOTIFICATIONS_RISK_THRESHOLD=85`
- `NOTIFICATIONS_INCIDENT_STATES=triaged,investigating,contained`
- `NOTIFICATIONS_RESPONSE_STATUSES=warning,failed`
- `NOTIFICATIONS_RESPONSE_ACTION_TYPES=*` (or a comma-separated subset of response `action_type` values)

For SMTP mode additionally set:

- `SMTP_HOST`
- `SMTP_PORT`
- optional auth (`SMTP_USERNAME`, `SMTP_PASSWORD`)
- optional transport flags (`SMTP_USE_TLS`, `SMTP_USE_STARTTLS`)

## Validation in Local/Lab

1. Enable notifications and start stack.
2. Generate an incident with risk >= threshold or transition an incident to a configured state.
3. Trigger a response action that results in `warning` or `failed`.
4. Verify:
   - entries exist in `notification_events`
   - incident detail API includes notification history (`notifications`)
   - alert detail API includes the same incident-scoped list (`notifications`) when the alert is linked to an incident
   - response list/detail payloads include `related_notifications` when a response action generated deliveries
   - audit logs contain `notification.sent` or `notification.failed`

## Audit and Safety Notes

- Every notification attempt/result is persisted in `notification_events`.
- Deduplication keys suppress repeated spam for the same trigger/recipient context.
- Frontend remains source-agnostic; notification history is exposed on incident detail, alert detail (linked incident), response rows (summary + per-action related deliveries), and audit logs.
