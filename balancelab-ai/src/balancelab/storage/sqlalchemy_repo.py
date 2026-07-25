"""SQLAlchemy-backed repositories and unit of work.

Domain models are serialized to JSONB for storage and reconstructed through
Pydantic validation on read. Writes are idempotent by primary id: if a row with
the same id exists, the stored record is returned unchanged.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from balancelab.domain.models import Portfolio, Snapshot
from balancelab.storage.orm import PortfolioRow, SnapshotRow


class SqlAlchemyPortfolioRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, portfolio: Portfolio) -> Portfolio:
        existing = self._session.get(PortfolioRow, portfolio.id)
        if existing is not None:
            return Portfolio.model_validate(existing.data)
        self._session.add(
            PortfolioRow(
                id=portfolio.id,
                name=portfolio.name,
                as_of_date=portfolio.as_of_date,
                currency=portfolio.currency,
                created_at=portfolio.created_at,
                data=portfolio.model_dump(mode="json"),
            )
        )
        self._session.flush()
        return portfolio

    def get(self, portfolio_id: str) -> Portfolio | None:
        row = self._session.get(PortfolioRow, portfolio_id)
        return Portfolio.model_validate(row.data) if row is not None else None


class SqlAlchemySnapshotRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, snapshot: Snapshot) -> Snapshot:
        existing = self._session.get(SnapshotRow, snapshot.id)
        if existing is not None:
            return Snapshot.model_validate(existing.data)
        self._session.add(
            SnapshotRow(
                id=snapshot.id,
                portfolio_id=snapshot.portfolio_id,
                as_of_date=snapshot.as_of_date,
                currency=snapshot.currency,
                total_assets=snapshot.total_assets,
                total_liabilities=snapshot.total_liabilities,
                total_equity=snapshot.total_equity,
                balances=snapshot.balances,
                created_at=snapshot.created_at,
                data=snapshot.model_dump(mode="json"),
            )
        )
        self._session.flush()
        return snapshot

    def get(self, snapshot_id: str) -> Snapshot | None:
        row = self._session.get(SnapshotRow, snapshot_id)
        return Snapshot.model_validate(row.data) if row is not None else None


class SqlAlchemyUnitOfWork:
    """A transactional unit of work over a single SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self.portfolios = SqlAlchemyPortfolioRepository(session)
        self.snapshots = SqlAlchemySnapshotRepository(session)

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        return self

    def __exit__(self, *exc: object) -> None:
        # Roll back on any error, then always close the session.
        try:
            if exc and exc[0] is not None:
                self.rollback()
        finally:
            self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
