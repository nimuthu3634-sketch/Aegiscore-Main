from __future__ import annotations

from statistics import mean

from app.models.enums import IncidentPriority
from app.models.incident import Incident
from app.services.scoring.baseline import priority_from_score


def incident_rollup_score(incident: Incident) -> float:
    linked_alerts = list(incident.alerts) or ([incident.primary_alert] if incident.primary_alert else [])
    risk_values = [alert.risk_score.score for alert in linked_alerts if alert and alert.risk_score]

    if risk_values:
        max_score = max(risk_values)
        average_score = mean(risk_values)
        correlation_bonus = min(10, max(0, len(risk_values) - 1) * 4)
        return round(min(100, max_score * 0.7 + average_score * 0.3 + correlation_bonus), 2)

    primary_alert = incident.primary_alert
    if primary_alert is None:
        return 0.0
    return float(primary_alert.severity * 10)


def refresh_incident_priority(incident: Incident) -> IncidentPriority:
    incident.priority = priority_from_score(incident_rollup_score(incident))
    return incident.priority


def build_incident_priority_summary(incident: Incident) -> dict[str, object]:
    linked_alerts = list(incident.alerts) or ([incident.primary_alert] if incident.primary_alert else [])
    risk_values = [alert.risk_score.score for alert in linked_alerts if alert and alert.risk_score]
    rollup_score = incident_rollup_score(incident)
    priority = priority_from_score(rollup_score)
    max_score = max(risk_values) if risk_values else None
    average_score = round(mean(risk_values), 2) if risk_values else None
    scoring_methods = sorted(
        {
            alert.risk_score.scoring_method.value
            for alert in linked_alerts
            if alert.risk_score and alert.risk_score.scoring_method is not None
        }
    )

    factors = [
        f"Linked alert count: {len(linked_alerts)}",
        f"Rollup score: {round(rollup_score)}",
    ]
    if max_score is not None:
        factors.append(f"Highest linked alert score: {round(max_score)}")
    if average_score is not None:
        factors.append(f"Average linked alert score: {round(average_score)}")
    if scoring_methods:
        factors.append(f"Scoring methods in scope: {', '.join(scoring_methods)}")

    return {
        "score": round(rollup_score),
        "priority": priority.value,
        "factors": factors,
        "scoring_methods": scoring_methods,
        "max_alert_score": round(max_score) if max_score is not None else None,
        "average_alert_score": round(average_score) if average_score is not None else None,
    }
