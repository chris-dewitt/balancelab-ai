"""Exception handlers mapping errors to structured API responses.

All error responses share the :class:`~balancelab.errors.ErrorBody` shape:
``code``, ``message``, ``correlation_id``, and safe ``details``. Unexpected
exceptions are never leaked verbatim; they are logged with the correlation ID and
returned as a generic internal error.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from balancelab.correlation import get_correlation_id
from balancelab.errors import BalanceLabError, ErrorBody, ErrorCode
from balancelab.telemetry import get_logger

_logger = get_logger("balancelab.api.errors")


def sanitize_validation_errors(errors: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Reduce Pydantic/FastAPI error dicts to JSON-safe primitives.

    Pydantic error entries can carry a ``ctx`` holding the original exception
    object, which is not JSON-serializable. Keeping only ``loc``/``msg``/``type``
    yields a safe, stable error payload.
    """

    return [
        {
            "loc": [str(part) for part in err.get("loc", ())],
            "msg": str(err.get("msg", "")),
            "type": str(err.get("type", "")),
        }
        for err in errors
    ]


def _json(body: ErrorBody, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


async def _handle_balancelab_error(_: Request, exc: BalanceLabError) -> JSONResponse:
    correlation_id = get_correlation_id()
    _logger.warning(
        "handled application error",
        extra={"error_code": exc.code.value, "detail_keys": sorted(exc.details)},
    )
    return _json(exc.to_body(correlation_id), exc.http_status)


async def _handle_request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
    correlation_id = get_correlation_id()
    body = ErrorBody(
        code=ErrorCode.VALIDATION_ERROR,
        message="request validation failed",
        correlation_id=correlation_id,
        details={"errors": sanitize_validation_errors(exc.errors())},
    )
    return _json(body, 422)


async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
    correlation_id = get_correlation_id()
    # Log the real exception; return a generic body so internals never leak.
    _logger.error("unhandled exception", exc_info=exc)
    body = ErrorBody(
        code=ErrorCode.INTERNAL_ERROR,
        message="an internal error occurred",
        correlation_id=correlation_id,
    )
    return _json(body, 500)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to ``app``."""

    app.add_exception_handler(BalanceLabError, _handle_balancelab_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_request_validation)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unexpected)
