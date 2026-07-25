"""Tests for the synthetic generator and the synthetic-only boundary."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from balancelab.config import Settings
from balancelab.domain.models import (
    Account,
    AccountCategory,
    DataOrigin,
    Portfolio,
    Provenance,
)
from balancelab.errors import PolicyViolationError
from balancelab.synthetic.generator import (
    ensure_synthetic,
    generate_synthetic_portfolio,
)


def test_generation_is_deterministic() -> None:
    a = generate_synthetic_portfolio(seed=42)
    b = generate_synthetic_portfolio(seed=42)
    assert [ac.balance for ac in a.accounts] == [ac.balance for ac in b.accounts]


def test_different_seeds_differ() -> None:
    a = generate_synthetic_portfolio(seed=1)
    b = generate_synthetic_portfolio(seed=2)
    assert [ac.balance for ac in a.accounts] != [ac.balance for ac in b.accounts]


def test_generated_portfolio_balances_by_construction() -> None:
    p = generate_synthetic_portfolio(seed=7, n_asset_accounts=3, n_liability_accounts=2)
    assets = sum((a.balance for a in p.accounts_by_category(AccountCategory.ASSET)), Decimal(0))
    liabilities = sum(
        (a.balance for a in p.accounts_by_category(AccountCategory.LIABILITY)), Decimal(0)
    )
    equity = sum((a.balance for a in p.accounts_by_category(AccountCategory.EQUITY)), Decimal(0))
    assert assets == liabilities + equity


def test_generated_portfolio_is_labeled_synthetic() -> None:
    p = generate_synthetic_portfolio(seed=7)
    assert p.provenance.origin == DataOrigin.SYNTHETIC
    assert p.provenance.is_synthetic is True
    assert p.provenance.seed == 7


def test_account_counts_are_bounded() -> None:
    with pytest.raises(ValueError):
        generate_synthetic_portfolio(seed=1, n_asset_accounts=99)


def test_ensure_synthetic_passes_synthetic_data() -> None:
    p = generate_synthetic_portfolio(seed=3)
    assert ensure_synthetic(p, Settings(synthetic_data_only=True)) is p


def test_ensure_synthetic_rejects_non_synthetic_when_policy_on() -> None:
    uploaded = Portfolio(
        name="Real",
        as_of_date=date(2025, 12, 31),
        currency="USD",
        provenance=Provenance(
            origin=DataOrigin.UPLOADED,
            source_uri="file://x.csv",
            retrieved_at=datetime.now(tz=UTC),
        ),
        accounts=(
            Account(
                name="Cash",
                category=AccountCategory.ASSET,
                currency="USD",
                balance=Decimal("1.00"),
            ),
        ),
    )
    with pytest.raises(PolicyViolationError):
        ensure_synthetic(uploaded, Settings(synthetic_data_only=True))


def test_ensure_synthetic_allows_non_synthetic_when_policy_off() -> None:
    uploaded = Portfolio(
        name="Real",
        as_of_date=date(2025, 12, 31),
        currency="USD",
        provenance=Provenance(origin=DataOrigin.PUBLIC, source_uri="https://example.org"),
        accounts=(
            Account(
                name="Cash",
                category=AccountCategory.ASSET,
                currency="USD",
                balance=Decimal("1.00"),
            ),
        ),
    )
    assert ensure_synthetic(uploaded, Settings(synthetic_data_only=False)) is uploaded
