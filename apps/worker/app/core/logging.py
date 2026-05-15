import logging


def configure_logging() -> None:
    # Sets a common log format for the worker container.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    # Returns a named logger so logs show which module created the message.
    return logging.getLogger(name)
