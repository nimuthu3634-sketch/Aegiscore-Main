import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import engine

logger = get_logger(__name__)


def get_database_status() -> str:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "up"
    except SQLAlchemyError:
        return "down"


def run_forever() -> None:
    settings = get_settings()

    while True:
        logger.info("Worker heartbeat | database=%s", get_database_status())
        time.sleep(settings.worker_poll_interval_seconds)

