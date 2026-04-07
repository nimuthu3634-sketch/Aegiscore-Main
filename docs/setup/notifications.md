# Notification Subsystem Setup

AegisCore supports SME-friendly critical-incident notifications from backend-owned logic with auditable persistence.

## Supported Channels

- `log` mode: safe development/local mode that records delivery as sent without external email transport
- `smtp` mode: real email delivery suitable for local mail sinks (for example MailHog/Mailpit) or lab SMTP

## Trigger Rules

Notifications are evaluated for:

- high-risk incidents (`risk_threshold`)
- incident state transitions (`incident_state`)
- response execution outcomes (`response_result`)

Rules are controlled through environment configuration.

## Required Configuration

- `NOTIFICATIONS_ENABLED=true`
- `NOTIFICATIONS_MODE=log` or `smtp`
- `NOTIFICATIONS_ADMIN_RECIPIENTS=admin1@example.local,admin2@example.local`
- `NOTIFICATIONS_SENDER=aegiscore@localhost`
- `NOTIFICATIONS_RISK_THRESHOLD=85`
- `NOTIFICATIONS_INCIDENT_STATES=triaged,investigating,contained`
- `NOTIFICATIONS_RESPONSE_STATUSES=warning,failed`

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
   - incident detail API includes notification history
   - audit logs contain `notification.sent` or `notification.failed`

## Audit and Safety Notes

- Every notification attempt/result is persisted in `notification_events`.
- Deduplication keys suppress repeated spam for the same trigger/recipient context.
- Frontend remains source-agnostic; notification history is exposed as incident metadata.
