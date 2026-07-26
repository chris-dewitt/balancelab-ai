"""Tests for upload validation."""

from __future__ import annotations

import pytest

from balancelab.config import Settings
from balancelab.ingest import parse_csv_accounts, validate_upload

_SYNTHETIC_ONLY = Settings(synthetic_data_only=True, database_url=None)
_RELAXED = Settings(synthetic_data_only=False, database_url=None)


def _balanced_upload(origin: str = "synthetic") -> dict:
    return {
        "name": "U",
        "currency": "USD",
        "as_of_date": "2025-12-31",
        "origin": origin,
        "accounts": [
            {"name": "Cash", "category": "asset", "currency": "USD", "balance": "100.00"},
            {"name": "Debt", "category": "liability", "currency": "USD", "balance": "40.00"},
            {"name": "Eq", "category": "equity", "currency": "USD", "balance": "60.00"},
        ],
    }


def test_valid_synthetic_upload() -> None:
    report = validate_upload(_balanced_upload(), _SYNTHETIC_ONLY)
    assert report.valid is True
    assert report.portfolio is not None
    assert report.totals is not None
    assert report.totals["residual"] == "0.00"


def test_unbalanced_upload_reports_issue() -> None:
    payload = _balanced_upload()
    payload["accounts"][2]["balance"] = "5.00"
    report = validate_upload(payload, _SYNTHETIC_ONLY)
    assert report.valid is False
    assert any(i.code == "unbalanced" for i in report.issues)


def test_policy_rejects_public_when_synthetic_only() -> None:
    report = validate_upload(_balanced_upload(origin="public"), _SYNTHETIC_ONLY)
    assert report.valid is False
    assert any(i.code == "policy" for i in report.issues)


def test_policy_allows_public_when_relaxed() -> None:
    report = validate_upload(_balanced_upload(origin="public"), _RELAXED)
    assert report.valid is True


def test_uploaded_origin_always_rejected_under_policy() -> None:
    report = validate_upload(_balanced_upload(origin="uploaded"), _SYNTHETIC_ONLY)
    assert report.valid is False
    assert any(i.code == "policy" for i in report.issues)


def test_bad_currency_is_schema_issue() -> None:
    payload = _balanced_upload()
    payload["currency"] = "ZZZ"
    report = validate_upload(payload, _SYNTHETIC_ONLY)
    assert report.valid is False
    assert any(i.code == "schema" for i in report.issues)


def test_non_numeric_balance_is_schema_issue() -> None:
    payload = _balanced_upload()
    payload["accounts"][0]["balance"] = "not-a-number"
    report = validate_upload(payload, _SYNTHETIC_ONLY)
    assert report.valid is False
    assert any(i.code == "schema" for i in report.issues)


def test_accounts_must_be_a_list() -> None:
    report = validate_upload({"accounts": "nope"}, _SYNTHETIC_ONLY)
    assert report.valid is False
    assert report.issues[0].code == "schema"


def test_parse_csv_accounts() -> None:
    text = "name,category,currency,balance\nCash,asset,USD,100.00\nDebt,liability,usd,40\n"
    rows = parse_csv_accounts(text)
    assert rows == [
        {"name": "Cash", "category": "asset", "currency": "USD", "balance": "100.00"},
        {"name": "Debt", "category": "liability", "currency": "USD", "balance": "40"},
    ]


def test_parse_csv_requires_header() -> None:
    with pytest.raises(ValueError):
        parse_csv_accounts("a,b,c\n1,2,3\n")
