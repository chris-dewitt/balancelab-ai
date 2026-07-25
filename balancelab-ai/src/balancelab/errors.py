"""Structured error taxonomy.

Domain and platform code raise :class:`BalanceLabError` subclasses. The API
layer maps these to HTTP responses with a stable structured body containing a
machine-readable ``code``, a human-readable ``message``, the request
``correlation_id``, and ``details`` that must never leak secrets or internal
state.

Keeping the taxonomy in the platform layer (not the API layer) lets the domain
raise meaningful, typed failures without importing the web framework.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    """Stable, machine-readable error codes.

    Values are part of the API contract; rename with care and a changelog entry.
    """

    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RECONCILIATION_FAILED = "reconciliation_failed"
    POLICY_VIOLATION = "policy_violation"
    UNPROCESSABLE = "unprocessable"
    INTERNAL_ERROR = "internal_error"


# Default HTTP status per error code. The API layer owns the actual response,
# but co-locating the mapping keeps it consistent and testable without FastAPI.
HTTP_STATUS_BY_CODE: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.RECONCILIATION_FAILED: 422,
    ErrorCode.POLICY_VIOLATION: 403,
    ErrorCode.UNPROCESSABLE: 422,
    ErrorCode.INTERNAL_ERROR: 500,
}


class ErrorBody(BaseModel):
    """Serializable error payload returned to clients."""

    code: ErrorCode
    message: str
    correlation_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class BalanceLabError(Exception):
    """Base class for all application errors.

    ``details`` must contain only safe, non-sensitive context suitable for
    returning to a client and recording in telemetry.
    """

    code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = details or {}

    @property
    def http_status(self) -> int:
        return HTTP_STATUS_BY_CODE[self.code]

    def to_body(self, correlation_id: str | None = None) -> ErrorBody:
        return ErrorBody(
            code=self.code,
            message=self.message,
            correlation_id=correlation_id,
            details=self.details,
        )


class ValidationError(BalanceLabError):
    """Input failed schema or domain validation."""

    code = ErrorCode.VALIDATION_ERROR


class NotFoundError(BalanceLabError):
    """A requested resource does not exist."""

    code = ErrorCode.NOT_FOUND


class ConflictError(BalanceLabError):
    """The request conflicts with existing state (e.g. duplicate id)."""

    code = ErrorCode.CONFLICT


class ReconciliationError(BalanceLabError):
    """A deterministic result failed a reconciliation invariant."""

    code = ErrorCode.RECONCILIATION_FAILED


class PolicyViolationError(BalanceLabError):
    """A guarded policy (e.g. synthetic-data-only) was violated."""

    code = ErrorCode.POLICY_VIOLATION
