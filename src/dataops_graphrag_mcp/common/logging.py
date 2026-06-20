import json
import logging
import uuid
from contextvars import ContextVar

from dataops_graphrag_mcp.common.settings import settings

# Per-request correlation ID stored in a context variable so it propagates
# automatically across sync and async callstacks within the same request.
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def new_correlation_id() -> str:
    """Generate and activate a fresh correlation ID for the current context."""
    cid = uuid.uuid4().hex
    _correlation_id.set(cid)
    return cid


def get_correlation_id() -> str:
    return _correlation_id.get() or "no-correlation-id"


class _StructuredFormatter(logging.Formatter):
    """Emit JSON log lines with correlation_id injected into every record."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_StructuredFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    return logger
