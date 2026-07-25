"""Versioned deterministic formulas.

These are pure functions over :class:`decimal.Decimal`. They contain no I/O, no
randomness, and no model calls, so their outputs are fully reproducible. The
``FORMULA_VERSION`` string is stamped onto every lineage node the engine
produces; bump it (and add a changelog entry) whenever a formula's numeric
behavior changes, so historical results remain attributable to the code that
made them.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from balancelab.domain.base import quantize_money

FORMULA_VERSION = "balance-formulas@1"


def total(amounts: Iterable[Decimal]) -> Decimal:
    """Return the quantized sum of ``amounts`` (0 for an empty iterable)."""

    return quantize_money(sum(amounts, Decimal(0)))


def balance_residual(
    total_assets: Decimal, total_liabilities: Decimal, total_equity: Decimal
) -> Decimal:
    """Return assets - (liabilities + equity).

    Zero (within tolerance, applied by the caller) means the balance-sheet
    identity holds.
    """

    return quantize_money(total_assets - (total_liabilities + total_equity))


def is_balanced(residual: Decimal, abs_tolerance: Decimal) -> bool:
    """Return whether ``residual`` is within ``abs_tolerance`` of zero."""

    if abs_tolerance < 0:
        raise ValueError("abs_tolerance must be non-negative")
    return abs(residual) <= abs_tolerance
