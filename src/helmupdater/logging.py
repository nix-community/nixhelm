import logging
import os

import structlog


def configure_logging(level: int | None = None) -> None:
    if level is None:
        level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
        level = logging.getLevelNamesMapping().get(level_name, logging.INFO)

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
    )


def get_logger() -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance."""
    return structlog.get_logger()
