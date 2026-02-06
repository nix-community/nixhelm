import structlog


def configure_logging() -> None:
    # default structlog configuration here is good for now
    structlog.configure()


def get_logger() -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance."""
    return structlog.get_logger()
