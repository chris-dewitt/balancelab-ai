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

from balancelab.domain.forecast import ForecastRun
from balancelab.domain.models import Portfolio, Snapshot
from balancelab.domain.scenario import Scenario


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
class ScenarioRepository(Protocol):
    """Persistence for scenarios, keyed by ``Scenario.id``."""

    def add(self, scenario: Scenario) -> Scenario:
        """Persist ``scenario``; idempotent by id. Returns the stored record."""
        ...

    def get(self, scenario_id: str) -> Scenario | None:
        """Return the scenario with ``scenario_id`` or ``None`` if absent."""
        ...

    def list(self, limit: int = 50, offset: int = 0) -> tuple[Scenario, ...]:
        """Return stored scenarios, newest first, paginated."""
        ...

    def delete(self, scenario_id: str) -> bool:
        """Delete a scenario; return ``True`` if it existed."""
        ...


@runtime_checkable
class ForecastRepository(Protocol):
    """Persistence for forecast runs, keyed by ``ForecastRun.id``."""

    def add(self, run: ForecastRun) -> ForecastRun:
        """Persist ``run``; idempotent by id. Returns the stored record."""
        ...

    def get(self, run_id: str) -> ForecastRun | None:
        """Return the forecast run with ``run_id`` or ``None`` if absent."""
        ...


@runtime_checkable
class UnitOfWork(Protocol):
    """A transactional boundary exposing the repositories.

    Implementations are context managers: work is committed on clean exit and
    rolled back on exception. In-memory implementations may treat commit/rollback
    as no-ops but must still honor the context-manager contract.

    The repositories are declared as read-only properties so the Protocol is
    covariant in the repository types: a concrete unit of work may expose more
    specific repository implementations and still satisfy it.
    """

    @property
    def portfolios(self) -> PortfolioRepository: ...

    @property
    def snapshots(self) -> SnapshotRepository: ...

    @property
    def scenarios(self) -> ScenarioRepository: ...

    @property
    def forecasts(self) -> ForecastRepository: ...

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(self, *exc: object) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
