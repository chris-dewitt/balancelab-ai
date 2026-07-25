"""HTTP middleware: correlation-ID propagation.

Each request is assigned a correlation ID (honoring an inbound
``X-Correlation-ID`` header when present) that is bound to the context for the
duration of the request and echoed back on the response. Downstream logs, error
bodies, and traces reuse it.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from balancelab.correlation import (
    new_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)

CORRELATION_HEADER = "X-Correlation-ID"

# Bound the length of a client-supplied correlation id so it cannot be abused as
# an unbounded log-injection vector.
_MAX_INBOUND_ID_LEN = 128


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Bind a correlation ID for the lifetime of each request."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        inbound = request.headers.get(CORRELATION_HEADER)
        correlation_id = (
            inbound.strip()
            if inbound and 0 < len(inbound.strip()) <= _MAX_INBOUND_ID_LEN
            else new_correlation_id()
        )
        token = set_correlation_id(correlation_id)
        try:
            response = await call_next(request)
        finally:
            reset_correlation_id(token)
        response.headers[CORRELATION_HEADER] = correlation_id
        return response
