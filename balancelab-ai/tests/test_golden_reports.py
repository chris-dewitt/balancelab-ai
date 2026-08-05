"""Golden-report tests for stable transformations (export bundles).

Export bundles are pinned as golden fixtures after normalizing volatile ids and
timestamps (see ``tests/golden_utils``). A change to a reported value, the bundle
shape, or the lineage structure fails these tests — a report-regression gate.
Regenerate the fixtures deliberately (and note it in the changelog) when the
change is intended.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from balancelab.calc.engine import compute_snapshot
from balancelab.calc.forecast import compute_forecast
from balancelab.domain.models import AccountCategory
from balancelab.domain.scenario import Assumption, Scenario
from balancelab.export import build_forecast_export, build_snapshot_export
from balancelab.synthetic.generator import generate_synthetic_portfolio
from tests.golden_utils import normalize

_GOLDEN = Path(__file__).parent / "golden"


def _load(name: str) -> dict:
    return json.loads((_GOLDEN / name).read_text(encoding="utf-8"))


def test_snapshot_export_matches_golden() -> None:
    portfolio = generate_synthetic_portfolio(seed=7)
    snapshot = compute_snapshot(portfolio)
    got = normalize(build_snapshot_export(portfolio, snapshot).model_dump(mode="json"))
    assert got == _load("snapshot_export_seed7.json")


def test_forecast_export_matches_golden() -> None:
    portfolio = generate_synthetic_portfolio(seed=7)
    scenario = Scenario(
        name="golden-scenario",
        base_portfolio_id=portfolio.id,
        horizon_periods=3,
        assumptions=(
            Assumption(target=AccountCategory.ASSET, value=Decimal("0.05")),
            Assumption(target=AccountCategory.LIABILITY, value=Decimal("0.02")),
        ),
    )
    run = compute_forecast(portfolio, scenario)
    got = normalize(build_forecast_export(portfolio, scenario, run).model_dump(mode="json"))
    assert got == _load("forecast_export_seed7.json")
