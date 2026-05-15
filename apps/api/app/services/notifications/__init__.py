# Makes the main notification service functions available from this package.
from app.services.notifications.service import (
    list_incident_notifications,
    notify_for_high_risk_incident,
    notify_for_incident_state,
    notify_for_response_result,
    send_admin_notification,
)

# Defines what can be imported when using from app.services.notifications import *.
__all__ = [
    "notify_for_high_risk_incident",
    "notify_for_incident_state",
    "notify_for_response_result",
    "list_incident_notifications",
    "send_admin_notification",
]
