"""
Structured JSON logging configuration for ForgeSight AI.

No print() statements are used anywhere in this codebase — all runtime
diagnostics flow through the logger configured here. As of Phase 11, log
records emitted while an OpenTelemetry span is active automatically carry
trace_id/span_id fields (see TraceContextFilter), so logs and traces are
correlatable without a separate scheme.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from forgesight.config.settings import settings

_LOGGER_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        reserved = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())
        for key, value in record.__dict__.items():
            if key not in reserved and key not in payload:
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure the root logger for the application. Idempotent."""
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    # Imported lazily to avoid a circular import (observability imports
    # settings; settings has no dependency on observability).
    from forgesight.observability.logging_bridge import TraceContextFilter

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(TraceContextFilter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    for noisy_logger in ("sqlalchemy.engine", "uvicorn.access"):
        logging.getLogger(noisy_logger).setLevel(logging.INFO if settings.debug else logging.WARNING)

    _LOGGER_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name."""
    configure_logging()
    return logging.getLogger(name)