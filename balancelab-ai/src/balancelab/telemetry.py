"""Structured logging and telemetry hooks.

M0 ships structured JSON logging keyed by correlation ID. The logging setup is
deliberately small and dependency-free; it establishes the contract (one JSON
object per line, correlation ID attached, no secrets) that the OpenTelemetry
integration in a later milestone will extend rather than replace.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from balancelab.correlation import get_correlation_id

_RESERVED_LOGRECORD_KEYS = frozenset(logging.makeLogRecord({}).__dict__.keys()) | {
    "message",
    "asctime",
}

# Field names that must never be emitted verbatim in structured logs.
_REDACT_KEYS = frozenset({"password", "secret", "token", "authorization", "api_key"})
_REDACTED = "***redacted***"


class JsonLogFormatter(logging.Formatter):
    """Render log records as single-line JSON with the correlation ID attached."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        # Promote any structured extras passed via ``logger.info(..., extra=...)``.
        for key, value in record.__dict__.items():
            if key in _RESERVED_LOGRECORD_KEYS:
                continue
            payload[key] = _REDACTED if key.lower() in _REDACT_KEYS else value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, sort_keys=True)


def configure_logging(level: str = "info") -> None:
    """Install the JSON formatter on the root logger.

    Idempotent: repeated calls replace the handler rather than stacking new
    ones, which keeps test runs from emitting duplicate lines.
    """

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonLogFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger for ``name``."""

    return logging.getLogger(name)
