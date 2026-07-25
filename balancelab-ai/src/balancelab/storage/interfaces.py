"""Typed storage interfaces.

Repositories speak in domain models (`Portfolio`, `Snapshot`), never in ORM rows,
so the domain and API layers stay independent of the storage backend. Both the
in-memory and SQLAlchemy implementations satisfy these Protocols, which keeps
tests fast (in-memory) while production uses Postgres.

Writes are idempotent by primary id: saving a record whose id already exists is a
no-op that returns the stored record, so retried requests do not create
duplicates.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from balancelab.domain.models import Portfolio, Snapshot


@runtime_checkable
class PortfolioRepository(Protocol):
    """Persistence for portfolios, keyed by ``Portfolio.id``."""

    def add(self, portfolio: Portfolio) -> Portfolio:
        """Persist ``portfolio``; idempotent by id. Returns the stored record."""
        ...

    def get(self, portfolio_id: str) -> Portfolio | None:
        """Return the portfolio with ``portfolio_id`` or ``None`` if absent."""
        ...


@runtime_checkable
class SnapshotRepository(Protocol):
    """Persistence for snapshots, keyed by ``Snapshot.id``."""

    def add(self, snapshot: Snapshot) -> Snapshot:
        """Persist ``snapshot``; idempotent by id. Returns the stored record."""
        ...

    def get(self, snapshot_id: str) -> Snapshot | None:
        """Return the snapshot with ``snapshot_id`` or ``None`` if absent."""
        ...


@runtime_checkable
class UnitOfWork(Protocol):
    """A transactional boundary exposing both repositories.

    Implementations are context managers: work is committed on clean exit and
    rolled back on exception. In-memory implementations may treat commit/rollback
    as no-ops but must still honor the context-manager contract.

    ``portfolios`` and ``snapshots`` are declared as read-only properties so the
    Protocol is covariant in the repository types: a concrete unit of work may
    expose more specific repository implementations and still satisfy it.
    """

    @property
    def portfolios(self) -> PortfolioRepository: ...

    @property
    def snapshots(self) -> SnapshotRepository: ...

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(self, *exc: object) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
