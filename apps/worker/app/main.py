from app.core.logging import configure_logging, get_logger
from app.services.heartbeat import run_forever

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    logger.info("Starting AegisCore worker runtime")
    run_forever()


if __name__ == "__main__":
    main()

