"""Core domain schemas for the M0 slice.

These Pydantic models are the typed contract for balance-sheet data. They are
independent of FastAPI, provider SDKs, and storage. The set implemented here is
the subset the M0 milestone requires (synthetic data boundary, schemas,
formulas): ``Portfolio``, ``Account``, ``Instrument``, ``CashFlow``,
``Snapshot``, and the lineage ``CalculationNode``. Scenario, forecast, and
evidence entities are deferred to later milestones (see docs/adr).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from balancelab.domain.base import SUPPORTED_CURRENCIES, DomainModel, utc_now
from balancelab.domain.ids import (
    ACCOUNT,
    CALC_NODE,
    CASHFLOW,
    INSTRUMENT,
    PORTFOLIO,
    SNAPSHOT,
    new_id,
)


class AccountCategory(StrEnum):
    """Top-level balance-sheet classification for an account."""

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"


class DataOrigin(StrEnum):
    """Where a record's data came from.

    ``SYNTHETIC`` and ``PUBLIC`` are the only origins permitted in the MVP;
    ``UPLOADED`` exists for the future upload-validation path but is not accepted
    while ``synthetic_data_only`` policy is in force.
    """

    SYNTHETIC = "synthetic"
    PUBLIC = "public"
    UPLOADED = "uploaded"


def _validate_currency(value: str) -> str:
    code = value.upper()
    if code not in SUPPORTED_CURRENCIES:
        raise ValueError(
            f"unsupported currency {value!r}; supported: {sorted(SUPPORTED_CURRENCIES)}"
        )
    return code


class Provenance(DomainModel):
    """Origin and reproducibility metadata carried by every portfolio.

    For synthetic data, ``generator`` and ``seed`` make a portfolio
    reproducible. For source-derived data (later milestones) the source URI,
    retrieval time, checksum, and license notes are retained per the spec.
    """

    origin: DataOrigin
    generator: str | None = None
    seed: int | None = None
    source_uri: str | None = None
    retrieved_at: datetime | None = None
    content_checksum: str | None = None
    license_notes: str | None = None

    @property
    def is_synthetic(self) -> bool:
        return self.origin == DataOrigin.SYNTHETIC


class Instrument(DomainModel):
    """A financial instrument held within an account.

    Minimal in M0: an identifier, a display name, and an optional external
    symbol. Richer instrument modeling (rates, maturities) arrives with the
    scenario/forecast milestones.
    """

    id: str = Field(default_factory=lambda: new_id(INSTRUMENT))
    name: str = Field(min_length=1, max_length=200)
    symbol: str | None = Field(default=None, max_length=64)


class CashFlow(DomainModel):
    """A dated cash movement associated with an account."""

    id: str = Field(default_factory=lambda: new_id(CASHFLOW))
    account_id: str
    amount: Decimal
    currency: str
    flow_date: date
    memo: str | None = Field(default=None, max_length=500)

    _check_currency = field_validator("currency")(_validate_currency)


class Account(DomainModel):
    """A single balance-sheet account with a point-in-time balance."""

    id: str = Field(default_factory=lambda: new_id(ACCOUNT))
    name: str = Field(min_length=1, max_length=200)
    category: AccountCategory
    currency: str
    balance: Decimal
    instruments: tuple[Instrument, ...] = ()

    _check_currency = field_validator("currency")(_validate_currency)


class Portfolio(DomainModel):
    """A named collection of accounts observed as of a single date.

    All accounts must share the portfolio currency in M0 (multi-currency
    consolidation is deferred). ``provenance`` records how the data was produced
    and, for synthetic data, how to reproduce it.
    """

    id: str = Field(default_factory=lambda: new_id(PORTFOLIO))
    name: str = Field(min_length=1, max_length=200)
    as_of_date: date
    currency: str
    provenance: Provenance
    accounts: tuple[Account, ...] = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)

    _check_currency = field_validator("currency")(_validate_currency)

    @model_validator(mode="after")
    def _accounts_match_portfolio_currency(self) -> Portfolio:
        mismatched = [a.id for a in self.accounts if a.currency != self.currency]
        if mismatched:
            raise ValueError(
                "all accounts must use the portfolio currency "
                f"{self.currency!r}; mismatched account ids: {mismatched}"
            )
        return self

    def accounts_by_category(self, category: AccountCategory) -> tuple[Account, ...]:
        return tuple(a for a in self.accounts if a.category == category)


class CalculationNode(DomainModel):
    """A single node in a calculation-lineage graph.

    Every authoritative number the system reports resolves to one of these:
    the ``formula`` applied, the ``inputs`` (ids of upstream nodes or source
    accounts) that fed it, the resulting ``value`` and ``unit``, and the
    ``formula_version`` of the code that produced it. Leaf nodes reference source
    account ids in ``inputs`` and carry an empty ``formula`` sentinel.
    """

    id: str = Field(default_factory=lambda: new_id(CALC_NODE))
    label: str = Field(min_length=1, max_length=200)
    formula: str
    formula_version: str
    inputs: tuple[str, ...] = ()
    value: Decimal
    unit: str


class Snapshot(DomainModel):
    """A deterministic point-in-time summary of a portfolio.

    Totals are authoritative outputs of the calculation engine. ``lineage`` is
    the full set of calculation nodes that produced them, so any displayed number
    can be traced end to end.
    """

    id: str = Field(default_factory=lambda: new_id(SNAPSHOT))
    portfolio_id: str
    as_of_date: date
    currency: str
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    balances: bool = Field(description="True when assets == liabilities + equity within tolerance.")
    lineage: tuple[CalculationNode, ...]
    created_at: datetime = Field(default_factory=utc_now)

    _check_currency = field_validator("currency")(_validate_currency)
