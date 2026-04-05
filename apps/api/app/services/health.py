from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine
from app.schemas.health import HealthResponse


def get_database_status() -> str:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "up"
    except SQLAlchemyError:
        return "down"


def get_health_payload() -> HealthResponse:
    database_status = get_database_status()
    application_status = "ok" if database_status == "up" else "degraded"

    return HealthResponse(
        status=application_status,
        service="aegiscore-api",
        database=database_status,
    )

