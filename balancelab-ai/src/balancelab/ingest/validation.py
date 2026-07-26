"""Balance-sheet upload validation.

Given a loosely-typed candidate payload (parsed JSON or CSV rows), attempt to
build a typed :class:`~balancelab.domain.models.Portfolio` and check it against
three gates:

1. **Schema** — Pydantic validation (types, required fields, currency allow-list,
   currency consistency, at least one account).
2. **Policy** — the declared data origin must be permitted under the current
   ``synthetic_data_only`` policy (synthetic always; public only when the policy
   is relaxed; ``uploaded``/unknown never).
3. **Reconciliation** — the balance-sheet identity (assets == liabilities +
   equity) within the configured tolerance.

The result is a structured report; nothing is persisted. All issues are
collected (not raised) so a caller sees every problem at once.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import Field, ValidationError

from balancelab.calc import formulas
from balancelab.config import Settings, get_settings
from balancelab.domain.base import DomainModel
from balancelab.domain.models import AccountCategory, DataOrigin, Portfolio

# Maximum accounts accepted in a single upload; bounds payload size.
MAX_UPLOAD_ACCOUNTS = 1000


class ValidationIssue(DomainModel):
    """A single problem found while validating an upload."""

    code: str
    message: str
    location: str | None = None


class ValidationReport(DomainModel):
    """The outcome of validating an upload.

    When ``valid`` is true, ``portfolio`` is the normalized, typed portfolio and
    ``totals`` holds the reconciled category totals. When false, ``issues``
    explains why and ``portfolio``/``totals`` may be ``None``.
    """

    valid: bool
    issues: tuple[ValidationIssue, ...] = ()
    portfolio: Portfolio | None = None
    totals: dict[str, str] | None = Field(default=None)


def _permitted_origins(settings: Settings) -> set[DataOrigin]:
    if settings.synthetic_data_only:
        return {DataOrigin.SYNTHETIC}
    return {DataOrigin.SYNTHETIC, DataOrigin.PUBLIC}


def parse_csv_accounts(text: str) -> list[dict[str, Any]]:
    """Parse CSV text into account row dicts.

    Expected header: ``name,category,currency,balance``. Raises ``ValueError``
    for a missing/invalid header so the caller can surface a structured error.
    """

    reader = csv.DictReader(io.StringIO(text))
    required = {"name", "category", "currency", "balance"}
    if reader.fieldnames is None or not required.issubset(
        {(f or "").strip() for f in reader.fieldnames}
    ):
        raise ValueError(f"CSV must have a header with columns: {sorted(required)}")
    rows: list[dict[str, Any]] = []
    for row in reader:
        rows.append(
            {
                "name": (row.get("name") or "").strip(),
                "category": (row.get("category") or "").strip().lower(),
                "currency": (row.get("currency") or "").strip().upper(),
                "balance": (row.get("balance") or "").strip(),
            }
        )
    return rows


def _coerce_accounts(
    raw_accounts: Sequence[Any],
) -> tuple[list[dict[str, Any]], list[ValidationIssue]]:
    """Coerce raw account rows to typed dicts, collecting per-row issues."""

    issues: list[ValidationIssue] = []
    coerced: list[dict[str, Any]] = []
    for idx, row in enumerate(raw_accounts):
        if not isinstance(row, Mapping):
            issues.append(
                ValidationIssue(
                    code="schema",
                    message="account row must be an object",
                    location=f"accounts[{idx}]",
                )
            )
            continue
        balance_raw = row.get("balance")
        try:
            balance = Decimal(str(balance_raw))
        except (InvalidOperation, TypeError, ValueError):
            issues.append(
                ValidationIssue(
                    code="schema",
                    message=f"balance is not a valid number: {balance_raw!r}",
                    location=f"accounts[{idx}].balance",
                )
            )
            continue
        coerced.append(
            {
                "name": row.get("name"),
                "category": row.get("category"),
                "currency": row.get("currency"),
                "balance": balance,
            }
        )
    return coerced, issues


def validate_upload(raw: Mapping[str, Any], settings: Settings | None = None) -> ValidationReport:
    """Validate a candidate portfolio payload and return a structured report."""

    cfg = settings or get_settings()
    issues: list[ValidationIssue] = []

    raw_accounts = raw.get("accounts")
    if not isinstance(raw_accounts, Sequence) or isinstance(raw_accounts, str | bytes):
        return ValidationReport(
            valid=False,
            issues=(
                ValidationIssue(
                    code="schema", message="'accounts' must be a list", location="accounts"
                ),
            ),
        )
    if len(raw_accounts) > MAX_UPLOAD_ACCOUNTS:
        return ValidationReport(
            valid=False,
            issues=(
                ValidationIssue(
                    code="too_large",
                    message=f"too many accounts (>{MAX_UPLOAD_ACCOUNTS})",
                    location="accounts",
                ),
            ),
        )

    coerced_accounts, coercion_issues = _coerce_accounts(raw_accounts)
    issues.extend(coercion_issues)

    # Declared provenance/origin.
    origin_raw = str(raw.get("origin", "")).strip().lower()
    try:
        origin = DataOrigin(origin_raw)
    except ValueError:
        origin = None
        issues.append(
            ValidationIssue(
                code="schema",
                message=f"unknown data origin: {origin_raw!r}; "
                f"expected one of {[o.value for o in DataOrigin]}",
                location="origin",
            )
        )

    provenance = {
        "origin": origin.value if origin else DataOrigin.UPLOADED.value,
        "source_uri": raw.get("source_uri"),
        "license_notes": raw.get("license_notes"),
    }

    portfolio: Portfolio | None = None
    if not coercion_issues:
        try:
            # Loosely-typed inputs are validated/coerced by Pydantic here; type
            # ignores acknowledge the untyped upload payload crossing the boundary.
            portfolio = Portfolio(
                name=raw.get("name", ""),
                as_of_date=raw.get("as_of_date"),  # type: ignore[arg-type]
                currency=raw.get("currency", ""),
                provenance=provenance,  # type: ignore[arg-type]
                accounts=coerced_accounts,  # type: ignore[arg-type]
            )
        except ValidationError as exc:
            for err in exc.errors():
                loc = ".".join(str(p) for p in err.get("loc", ()))
                issues.append(
                    ValidationIssue(
                        code="schema", message=err.get("msg", "invalid"), location=loc or None
                    )
                )

    # Policy gate (only meaningful once we know the origin).
    if origin is not None and origin not in _permitted_origins(cfg):
        issues.append(
            ValidationIssue(
                code="policy",
                message=f"data origin {origin.value!r} is not permitted under the "
                "current policy (synthetic-only)"
                if cfg.synthetic_data_only
                else f"data origin {origin.value!r} is not permitted",
                location="origin",
            )
        )

    totals: dict[str, str] | None = None
    if portfolio is not None:
        total_assets = formulas.total(
            a.balance for a in portfolio.accounts_by_category(AccountCategory.ASSET)
        )
        total_liabilities = formulas.total(
            a.balance for a in portfolio.accounts_by_category(AccountCategory.LIABILITY)
        )
        total_equity = formulas.total(
            a.balance for a in portfolio.accounts_by_category(AccountCategory.EQUITY)
        )
        residual = formulas.balance_residual(total_assets, total_liabilities, total_equity)
        tolerance = Decimal(str(cfg.reconciliation_abs_tolerance))
        balanced = formulas.is_balanced(residual, tolerance)
        totals = {
            "total_assets": str(total_assets),
            "total_liabilities": str(total_liabilities),
            "total_equity": str(total_equity),
            "residual": str(residual),
        }
        if not balanced:
            issues.append(
                ValidationIssue(
                    code="unbalanced",
                    message=f"assets != liabilities + equity (residual {residual})",
                )
            )

    valid = not issues and portfolio is not None
    return ValidationReport(
        valid=valid,
        issues=tuple(issues),
        portfolio=portfolio if valid else None,
        totals=totals,
    )
