"""Export bundle builders.

Pure assembly of :class:`~balancelab.domain.export.SnapshotExport` and
:class:`~balancelab.domain.export.ForecastExport` from already-loaded domain
objects. Reconciliation and the lineage graph are computed here so a bundle is
self-contained and independently verifiable.
"""

from __future__ import annotations

from balancelab.config import Settings
from balancelab.domain.export import ForecastExport, SnapshotExport
from balancelab.domain.forecast import ForecastRun
from balancelab.domain.lineage import build_lineage_graph
from balancelab.domain.models import Portfolio, Snapshot
from balancelab.domain.scenario import Scenario
from balancelab.reconcile import reconcile_forecast, reconcile_snapshot


def build_snapshot_export(
    portfolio: Portfolio, snapshot: Snapshot, settings: Settings | None = None
) -> SnapshotExport:
    return SnapshotExport(
        portfolio=portfolio,
        snapshot=snapshot,
        reconciliation=reconcile_snapshot(snapshot, settings),
        lineage=build_lineage_graph(snapshot.lineage),
    )


def build_forecast_export(
    portfolio: Portfolio,
    scenario: Scenario,
    forecast: ForecastRun,
    settings: Settings | None = None,
) -> ForecastExport:
    return ForecastExport(
        portfolio=portfolio,
        scenario=scenario,
        forecast=forecast,
        reconciliation=reconcile_forecast(forecast, settings),
        lineage=build_lineage_graph(forecast.lineage),
    )
