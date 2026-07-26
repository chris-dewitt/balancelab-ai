"""Deterministic forecast engine with lineage.

Projects a base portfolio forward over a scenario's horizon by applying
per-category growth rates. Assets and liabilities grow according to their
assumptions; equity is carried as a residual (assets − liabilities) each period,
so the balance-sheet identity holds by construction in every period.

Like the snapshot engine, this is a pure transform: no I/O, no randomness, no
model calls. Given the same portfolio and scenario, the output is identical, and
every projected figure is backed by a :class:`CalculationNode`.
"""

from __future__ import annotations

from decimal import Decimal

from balancelab.calc import formulas
from balancelab.domain.base import quantize_money
from balancelab.domain.forecast import ForecastRun, ForecastValue
from balancelab.domain.models import AccountCategory, CalculationNode, Portfolio
from balancelab.domain.scenario import Scenario
from balancelab.errors import ValidationError

FORECAST_FORMULA_VERSION = "forecast-formulas@1"

_GROWABLE = (AccountCategory.ASSET, AccountCategory.LIABILITY)


def _growth_formula(rate: Decimal) -> str:
    return f"previous_balance * (1 + {rate})"


def compute_forecast(portfolio: Portfolio, scenario: Scenario) -> ForecastRun:
    """Project ``portfolio`` over ``scenario``'s horizon deterministically.

    Raises :class:`ValidationError` if the scenario does not reference this
    portfolio.
    """

    if scenario.base_portfolio_id != portfolio.id:
        raise ValidationError(
            "scenario base_portfolio_id does not match the provided portfolio",
            details={
                "scenario_base_portfolio_id": scenario.base_portfolio_id,
                "portfolio_id": portfolio.id,
            },
        )

    currency = portfolio.currency
    horizon = scenario.horizon_periods
    rates = {category: scenario.growth_rate(category) for category in _GROWABLE}

    values: list[ForecastValue] = []
    lineage: list[CalculationNode] = []

    # Per-account running state: current value and the id of the node that
    # produced it, so each period's node can cite the previous period's node.
    growable_accounts = [a for a in portfolio.accounts if a.category in _GROWABLE]
    current_value: dict[str, Decimal] = {}
    prev_node_id: dict[str, str] = {}

    for period in range(horizon + 1):
        period_asset_nodes: list[CalculationNode] = []
        period_liability_nodes: list[CalculationNode] = []

        for account in growable_accounts:
            if period == 0:
                value = account.balance
                node = CalculationNode(
                    label=f"{account.category.value}:{account.name}@t0",
                    formula="base_balance",
                    formula_version=FORECAST_FORMULA_VERSION,
                    inputs=(account.id,),
                    value=value,
                    unit=currency,
                )
            else:
                rate = rates[account.category]
                value = quantize_money(current_value[account.id] * (Decimal(1) + rate))
                node = CalculationNode(
                    label=f"{account.category.value}:{account.name}@t{period}",
                    formula=_growth_formula(rate),
                    formula_version=FORECAST_FORMULA_VERSION,
                    inputs=(prev_node_id[account.id],),
                    value=value,
                    unit=currency,
                )

            current_value[account.id] = value
            prev_node_id[account.id] = node.id
            lineage.append(node)
            values.append(
                ForecastValue(
                    period=period,
                    account_id=account.id,
                    label=account.name,
                    category=account.category,
                    value=value,
                    unit=currency,
                )
            )
            if account.category == AccountCategory.ASSET:
                period_asset_nodes.append(node)
            else:
                period_liability_nodes.append(node)

        # Per-period category totals and the equity residual.
        assets_node = _total_node("total_asset", period, period_asset_nodes, currency)
        liabilities_node = _total_node("total_liability", period, period_liability_nodes, currency)
        equity_value = formulas.balance_residual(
            assets_node.value, liabilities_node.value, Decimal(0)
        )
        equity_node = CalculationNode(
            label=f"total_equity@t{period}",
            formula="total_asset - total_liability",
            formula_version=FORECAST_FORMULA_VERSION,
            inputs=(assets_node.id, liabilities_node.id),
            value=equity_value,
            unit=currency,
        )
        lineage.extend((assets_node, liabilities_node, equity_node))
        values.extend(
            (
                _total_value(
                    period, AccountCategory.ASSET, "total_asset", assets_node.value, currency
                ),
                _total_value(
                    period,
                    AccountCategory.LIABILITY,
                    "total_liability",
                    liabilities_node.value,
                    currency,
                ),
                _total_value(
                    period, AccountCategory.EQUITY, "total_equity", equity_value, currency
                ),
            )
        )

    return ForecastRun(
        scenario_id=scenario.id,
        base_portfolio_id=portfolio.id,
        currency=currency,
        horizon_periods=horizon,
        formula_version=FORECAST_FORMULA_VERSION,
        values=tuple(values),
        lineage=tuple(lineage),
    )


def _total_node(
    label: str, period: int, nodes: list[CalculationNode], currency: str
) -> CalculationNode:
    return CalculationNode(
        label=f"{label}@t{period}",
        formula="sum(account values in category for period)",
        formula_version=FORECAST_FORMULA_VERSION,
        inputs=tuple(n.id for n in nodes),
        value=formulas.total(n.value for n in nodes),
        unit=currency,
    )


def _total_value(
    period: int, category: AccountCategory, label: str, value: Decimal, currency: str
) -> ForecastValue:
    return ForecastValue(
        period=period,
        account_id=None,
        label=label,
        category=category,
        value=value,
        unit=currency,
    )
