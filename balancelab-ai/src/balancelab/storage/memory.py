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

from balancelab.domain.forecast import ForecastRun
from balancelab.domain.models import Portfolio, Snapshot
from balancelab.domain.scenario import Scenario


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


class InMemoryScenarioRepository:
    def __init__(self) -> None:
        # Insertion order preserved; list() returns newest first.
        self._by_id: dict[str, Scenario] = {}

    def add(self, scenario: Scenario) -> Scenario:
        return self._by_id.setdefault(scenario.id, scenario)

    def get(self, scenario_id: str) -> Scenario | None:
        return self._by_id.get(scenario_id)

    def list(self, limit: int = 50, offset: int = 0) -> tuple[Scenario, ...]:
        newest_first = list(reversed(self._by_id.values()))
        return tuple(newest_first[offset : offset + limit])

    def delete(self, scenario_id: str) -> bool:
        return self._by_id.pop(scenario_id, None) is not None


class InMemoryForecastRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, ForecastRun] = {}

    def add(self, run: ForecastRun) -> ForecastRun:
        return self._by_id.setdefault(run.id, run)

    def get(self, run_id: str) -> ForecastRun | None:
        return self._by_id.get(run_id)


class InMemoryDatabase:
    """Process-lifetime store shared across units of work."""

    def __init__(self) -> None:
        self.portfolios = InMemoryPortfolioRepository()
        self.snapshots = InMemorySnapshotRepository()
        self.scenarios = InMemoryScenarioRepository()
        self.forecasts = InMemoryForecastRepository()


class InMemoryUnitOfWork:
    """A unit of work over a shared :class:`InMemoryDatabase`.

    Commit/rollback are no-ops: the in-memory store has no transaction log.
    """

    def __init__(self, db: InMemoryDatabase) -> None:
        self.portfolios = db.portfolios
        self.snapshots = db.snapshots
        self.scenarios = db.scenarios
        self.forecasts = db.forecasts

    def __enter__(self) -> InMemoryUnitOfWork:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None
