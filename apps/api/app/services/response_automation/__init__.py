# Re-exports the main response automation functions for easier imports.

from app.services.response_automation.execution import (
    evaluate_alert_policies,
    evaluate_incident_policies,
)

# Controls which functions are exposed when importing this package.
__all__ = [
    "evaluate_alert_policies",
    "evaluate_incident_policies",
]
