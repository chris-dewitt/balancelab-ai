"""In-memory storage implementation.

Used for tests and for running the service without a database. It satisfies the
same Protocols as the SQLAlchemy backend, so behavior is exercised identically;
only durability differs. Stored models are immutable (frozen Pydantic), so the
dicts hold safe references.

The store (:class:`InMemoryDatabase`) is separate from the per-call unit of work
so data written by one request is visible to the next, mirroring how a real
database persists across transactions.
"""

from __future__ import annotations

from balancelab.domain.models import Portfolio, Snapshot


class InMemoryPortfolioRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, Portfolio] = {}

    def add(self, portfolio: Portfolio) -> Portfolio:
        # Idempotent by id: first write wins, later identical writes are no-ops.
        return self._by_id.setdefault(portfolio.id, portfolio)

    def get(self, portfolio_id: str) -> Portfolio | None:
        return self._by_id.get(portfolio_id)


class InMemorySnapshotRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, Snapshot] = {}

    def add(self, snapshot: Snapshot) -> Snapshot:
        return self._by_id.setdefault(snapshot.id, snapshot)

    def get(self, snapshot_id: str) -> Snapshot | None:
        return self._by_id.get(snapshot_id)


class InMemoryDatabase:
    """Process-lifetime store shared across units of work."""

    def __init__(self) -> None:
        self.portfolios = InMemoryPortfolioRepository()
        self.snapshots = InMemorySnapshotRepository()


class InMemoryUnitOfWork:
    """A unit of work over a shared :class:`InMemoryDatabase`.

    Commit/rollback are no-ops: the in-memory store has no transaction log.
    """

    def __init__(self, db: InMemoryDatabase) -> None:
        self.portfolios = db.portfolios
        self.snapshots = db.snapshots

    def __enter__(self) -> InMemoryUnitOfWork:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None
