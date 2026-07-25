"""Database engine and session factory.

The engine is created lazily from the configured ``database_url`` and cached, so
importing this module has no side effects and the service can run without a
database when persistence is not configured.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from balancelab.config import get_settings
from balancelab.errors import BalanceLabError


class DatabaseNotConfiguredError(BalanceLabError):
    """Raised when a database operation is attempted without a configured URL."""


@lru_cache(maxsize=1)
def get_engine(database_url: str | None = None) -> Engine:
    """Return a cached SQLAlchemy engine.

    ``database_url`` defaults to the configured value. ``pool_pre_ping`` guards
    against stale connections. Raises :class:`DatabaseNotConfiguredError` if no
    URL is available.
    """

    url = database_url or get_settings().database_url
    if not url:
        raise DatabaseNotConfiguredError("no database_url configured")
    return create_engine(url, pool_pre_ping=True, future=True)


@lru_cache(maxsize=1)
def get_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    """Return a cached session factory bound to the engine."""

    return sessionmaker(bind=get_engine(database_url), expire_on_commit=False)


def ping(database_url: str | None = None) -> bool:
    """Return whether a trivial query against the database succeeds.

    Used by the readiness probe. Never raises: connection problems return
    ``False`` so readiness reports "not ready" rather than erroring.
    """

    from sqlalchemy import text

    try:
        with get_engine(database_url).connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - readiness must not raise
        return False


def reset_engine_cache() -> None:
    """Dispose and clear cached engines/sessions (useful in tests)."""

    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
