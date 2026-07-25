"""Correlation-ID propagation.

Every request or job carries a correlation ID so logs, traces, and error
responses can be tied together. The ID is stored in a :class:`ContextVar` so it
is available to any code in the same execution context without threading it
through every function signature.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar, Token

_CORRELATION_ID: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def new_correlation_id() -> str:
    """Return a fresh, opaque correlation ID."""

    return uuid.uuid4().hex


def set_correlation_id(correlation_id: str) -> Token[str | None]:
    """Bind ``correlation_id`` to the current context.

    Returns the reset token so callers (e.g. middleware) can restore the prior
    value with :func:`reset_correlation_id`.
    """

    return _CORRELATION_ID.set(correlation_id)


def reset_correlation_id(token: Token[str | None]) -> None:
    """Restore the correlation ID to its value before ``token`` was issued."""

    _CORRELATION_ID.reset(token)


def get_correlation_id() -> str | None:
    """Return the correlation ID bound to the current context, if any."""

    return _CORRELATION_ID.get()
