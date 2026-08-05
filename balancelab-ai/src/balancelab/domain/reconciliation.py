"""Reconciliation records.

A reconciliation captures whether the balance-sheet identity
(``assets == liabilities + equity``) holds for a snapshot or a forecast, within
the configured absolute tolerance. For forecasts there is one check per period.
Reconciliations are derived deterministically from stored results, so they are
reproducible and safe to recompute.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import Field

from balancelab.domain.base import DomainModel, utc_now
from balancelab.domain.ids import RECONCILIATION, new_id


class ReconciliationSubject(StrEnum):
    SNAPSHOT = "snapshot"
    FORECAST = "forecast"


class ReconciliationCheck(DomainModel):
    """A single identity check (optionally for a forecast period)."""

    period: int | None
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    residual: Decimal
    tolerance: Decimal
    passed: bool


class Reconciliation(DomainModel):
    """The reconciliation result for a snapshot or forecast."""

    id: str = Field(default_factory=lambda: new_id(RECONCILIATION))
    subject_type: ReconciliationSubject
    subject_id: str
    currency: str
    checks: tuple[ReconciliationCheck, ...]
    passed: bool
    created_at: datetime = Field(default_factory=utc_now)
