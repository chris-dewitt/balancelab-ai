"""Shared domain primitives: base model, timestamps, and money handling.

Monetary amounts use :class:`decimal.Decimal` throughout the deterministic core.
Binary floating point is unsuitable for authoritative financial arithmetic, so
amounts are parsed and carried as decimals and only the reconciliation step
allows a documented absolute tolerance.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

# Currencies supported by the M0 synthetic slice. Kept small and explicit;
# widening this is a deliberate, tested change rather than free-form input.
SUPPORTED_CURRENCIES: frozenset[str] = frozenset({"USD", "EUR", "GBP"})

# Amounts are quantized to two minor units (cents) for reporting stability.
MONEY_QUANTUM: Decimal = Decimal("0.01")


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""

    return datetime.now(tz=UTC)


def quantize_money(amount: Decimal) -> Decimal:
    """Quantize ``amount`` to the reporting quantum (2 decimal places)."""

    return amount.quantize(MONEY_QUANTUM)


class DomainModel(BaseModel):
    """Base for all domain models.

    Domain records are immutable (``frozen=True``): corrections create new
    versions rather than mutating existing ones, matching the spec's versioning
    rule. ``extra="forbid"`` rejects unexpected fields so malformed or
    injection-style payloads fail loudly at the boundary.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)
