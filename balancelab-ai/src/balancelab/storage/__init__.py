"""Storage layer: typed repository interfaces and interchangeable backends.

The rest of the application depends only on :class:`UnitOfWork` and a
``UnitOfWorkFactory`` callable, never on a concrete backend. Two backends are
provided: an in-memory store (tests, DB-less runs) and a SQLAlchemy/Postgres
store (production). Select one with :func:`create_unit_of_work_factory`.
"""

from __future__ import annotations

from collections.abc import Callable

from balancelab.config import Settings, get_settings
from balancelab.storage.interfaces import (
    ForecastRepository,
    PortfolioRepository,
    ScenarioRepository,
    SnapshotRepository,
    UnitOfWork,
)
from balancelab.storage.memory import InMemoryDatabase, InMemoryUnitOfWork

UnitOfWorkFactory = Callable[[], UnitOfWork]

__all__ = [
    "ForecastRepository",
    "InMemoryDatabase",
    "InMemoryUnitOfWork",
    "PortfolioRepository",
    "ScenarioRepository",
    "SnapshotRepository",
    "UnitOfWork",
    "UnitOfWorkFactory",
    "create_unit_of_work_factory",
]


def create_unit_of_work_factory(settings: Settings | None = None) -> UnitOfWorkFactory:
    """Return a factory that produces a fresh :class:`UnitOfWork` per call.

    Uses the SQLAlchemy backend when ``database_url`` is configured, otherwise a
    shared in-memory backend. The choice is made once, at wiring time, so request
    handlers stay backend-agnostic.
    """

    cfg = settings or get_settings()

    if cfg.database_url:
        # Import here so SQLAlchemy engine creation is not triggered in DB-less runs.
        from balancelab.storage.session import get_session_factory
        from balancelab.storage.sqlalchemy_repo import SqlAlchemyUnitOfWork

        session_factory = get_session_factory(cfg.database_url)

        def _sqlalchemy_factory() -> UnitOfWork:
            return SqlAlchemyUnitOfWork(session_factory())

        return _sqlalchemy_factory

    db = InMemoryDatabase()

    def _memory_factory() -> UnitOfWork:
        return InMemoryUnitOfWork(db)

    return _memory_factory
