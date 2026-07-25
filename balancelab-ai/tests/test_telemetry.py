"""Tests for structured logging and redaction."""

from __future__ import annotations

import json
import logging

from balancelab.correlation import reset_correlation_id, set_correlation_id
from balancelab.telemetry import JsonLogFormatter


def _format(record: logging.LogRecord) -> dict[str, object]:
    return json.loads(JsonLogFormatter().format(record))


def test_output_is_json_with_expected_fields() -> None:
    record = logging.makeLogRecord(
        {"name": "test.logger", "levelno": logging.INFO, "levelname": "INFO", "msg": "hello"}
    )
    payload = _format(record)
    assert payload["level"] == "info"
    assert payload["logger"] == "test.logger"
    assert payload["message"] == "hello"
    assert "correlation_id" in payload


def test_correlation_id_is_attached() -> None:
    token = set_correlation_id("cid-xyz")
    try:
        record = logging.makeLogRecord({"msg": "hi", "levelname": "INFO"})
        assert _format(record)["correlation_id"] == "cid-xyz"
    finally:
        reset_correlation_id(token)


def test_sensitive_extras_are_redacted() -> None:
    record = logging.makeLogRecord(
        {"msg": "auth", "levelname": "INFO", "password": "hunter2", "user": "alice"}
    )
    payload = _format(record)
    assert payload["password"] == "***redacted***"
    assert payload["user"] == "alice"
