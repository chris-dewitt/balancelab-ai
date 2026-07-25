"""SQLAlchemy ORM models.

ORM rows are a storage detail, kept separate from the domain models. Each table
stores the full domain object as JSONB (the authoritative source for
reconstruction) plus a few typed scalar columns used for indexing and querying.
Reconstruction always goes through Pydantic validation, so a row that does not
round-trip to a valid domain model fails loudly rather than yielding a malformed
object.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class PortfolioRow(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class SnapshotRow(Base):
    __tablename__ = "snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    total_assets: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    total_equity: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    balances: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
