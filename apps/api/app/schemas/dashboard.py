from app.schemas.base import APIModel


# Summary data shown on the main SOC dashboard.
class DashboardSummaryResponse(APIModel):
    asset_count: int
    raw_alert_count: int
    alert_count: int
    open_incident_count: int
    pending_response_count: int
    average_risk_score: float
    alerts_by_detection: list[tuple[str, int]]