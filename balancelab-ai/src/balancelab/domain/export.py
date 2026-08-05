"""Export bundle schemas.

An export bundle packages everything needed to independently verify a result:
the inputs, the deterministic result, its reconciliation, and its full
calculation-lineage graph. Bundles are self-describing (schema version) and
serialize to JSON. They are the M2 precursor to the signature-demo audit export.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from balancelab.domain.base import DomainModel, utc_now
from balancelab.domain.forecast import ForecastRun
from balancelab.domain.lineage import LineageGraph
from balancelab.domain.models import Portfolio, Snapshot
from balancelab.domain.reconciliation import Reconciliation
from balancelab.domain.scenario import Scenario

EXPORT_SCHEMA_VERSION = "balancelab-export@1"


class SnapshotExport(DomainModel):
    """A verifiable bundle for a single snapshot."""

    schema_version: str = EXPORT_SCHEMA_VERSION
    exported_at: datetime = Field(default_factory=utc_now)
    portfolio: Portfolio
    snapshot: Snapshot
    reconciliation: Reconciliation
    lineage: LineageGraph


class ForecastExport(DomainModel):
    """A verifiable bundle for a single forecast run."""

    schema_version: str = EXPORT_SCHEMA_VERSION
    exported_at: datetime = Field(default_factory=utc_now)
    portfolio: Portfolio
    scenario: Scenario
    forecast: ForecastRun
    reconciliation: Reconciliation
    lineage: LineageGraph
