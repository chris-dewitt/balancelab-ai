"""Tests for domain schema validation and invariants."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from balancelab.domain.models import (
    Account,
    AccountCategory,
    DataOrigin,
    Portfolio,
    Provenance,
)


def _synthetic_provenance() -> Provenance:
    return Provenance(origin=DataOrigin.SYNTHETIC, generator="test", seed=1)


def _account(category: AccountCategory, balance: str, currency: str = "USD") -> Account:
    return Account(
        name=f"{category.value} account",
        category=category,
        currency=currency,
        balance=Decimal(balance),
    )


def test_valid_portfolio_constructs() -> None:
    portfolio = Portfolio(
        name="Demo",
        as_of_date=date(2025, 12, 31),
        currency="USD",
        provenance=_synthetic_provenance(),
        accounts=(
            _account(AccountCategory.ASSET, "100.00"),
            _account(AccountCategory.LIABILITY, "40.00"),
            _account(AccountCategory.EQUITY, "60.00"),
        ),
    )
    assert len(portfolio.accounts_by_category(AccountCategory.ASSET)) == 1
    assert portfolio.provenance.is_synthetic is True


def test_unsupported_currency_rejected() -> None:
    with pytest.raises(ValidationError):
        _account(AccountCategory.ASSET, "1.00", currency="ZZZ")


def test_account_currency_must_match_portfolio() -> None:
    with pytest.raises(ValidationError, match="portfolio currency"):
        Portfolio(
            name="Mismatch",
            as_of_date=date(2025, 12, 31),
            currency="USD",
            provenance=_synthetic_provenance(),
            accounts=(_account(AccountCategory.ASSET, "1.00", currency="EUR"),),
        )


def test_portfolio_requires_at_least_one_account() -> None:
    with pytest.raises(ValidationError):
        Portfolio(
            name="Empty",
            as_of_date=date(2025, 12, 31),
            currency="USD",
            provenance=_synthetic_provenance(),
            accounts=(),
        )


def test_unexpected_field_rejected() -> None:
    with pytest.raises(ValidationError):
        Account(
            name="x",
            category=AccountCategory.ASSET,
            currency="USD",
            balance=Decimal("1"),
            surprise="nope",  # type: ignore[call-arg]
        )


def test_models_are_immutable() -> None:
    account = _account(AccountCategory.ASSET, "1.00")
    with pytest.raises(ValidationError):
        account.balance = Decimal("2.00")  # type: ignore[misc]
