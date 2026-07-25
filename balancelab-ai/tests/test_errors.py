"""Tests for the structured error taxonomy."""

from __future__ import annotations

from balancelab.errors import (
    HTTP_STATUS_BY_CODE,
    BalanceLabError,
    ConflictError,
    ErrorCode,
    NotFoundError,
    PolicyViolationError,
    ReconciliationError,
    ValidationError,
)


def test_every_code_has_a_status() -> None:
    for code in ErrorCode:
        assert code in HTTP_STATUS_BY_CODE


def test_error_maps_to_body_with_correlation_id() -> None:
    err = ValidationError("bad input", details={"field": "seed"})
    body = err.to_body(correlation_id="abc123")
    assert body.code == ErrorCode.VALIDATION_ERROR
    assert body.message == "bad input"
    assert body.correlation_id == "abc123"
    assert body.details == {"field": "seed"}


def test_http_status_per_subclass() -> None:
    assert ValidationError("x").http_status == 422
    assert NotFoundError("x").http_status == 404
    assert ConflictError("x").http_status == 409
    assert ReconciliationError("x").http_status == 422
    assert PolicyViolationError("x").http_status == 403


def test_base_error_defaults_to_internal() -> None:
    err = BalanceLabError("boom")
    assert err.code == ErrorCode.INTERNAL_ERROR
    assert err.http_status == 500
    assert err.details == {}
