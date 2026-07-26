"""Deterministic calculation engine and versioned formulas.

Authoritative arithmetic lives here and only here. Models never perform these
calculations; they may only describe results already computed deterministically.
"""

from __future__ import annotations

from balancelab.calc.engine import compute_snapshot
from balancelab.calc.forecast import FORECAST_FORMULA_VERSION, compute_forecast
from balancelab.calc.formulas import FORMULA_VERSION

__all__ = [
    "FORECAST_FORMULA_VERSION",
    "FORMULA_VERSION",
    "compute_forecast",
    "compute_snapshot",
]
