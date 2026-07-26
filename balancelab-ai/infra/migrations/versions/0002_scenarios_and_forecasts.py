"""scenarios and forecast_runs tables

Revision ID: 0002_scenarios_forecasts
Revises: 0001_initial
Create Date: 2026-07-26

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_scenarios_forecasts"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("base_portfolio_id", sa.String(), nullable=False),
        sa.Column("horizon_periods", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_scenarios_base_portfolio_id"),
        "scenarios",
        ["base_portfolio_id"],
        unique=False,
    )

    op.create_table(
        "forecast_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("scenario_id", sa.String(), nullable=False),
        sa.Column("base_portfolio_id", sa.String(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("horizon_periods", sa.Integer(), nullable=False),
        sa.Column("formula_version", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_forecast_runs_scenario_id"),
        "forecast_runs",
        ["scenario_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_forecast_runs_base_portfolio_id"),
        "forecast_runs",
        ["base_portfolio_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_forecast_runs_base_portfolio_id"), table_name="forecast_runs")
    op.drop_index(op.f("ix_forecast_runs_scenario_id"), table_name="forecast_runs")
    op.drop_table("forecast_runs")
    op.drop_index(op.f("ix_scenarios_base_portfolio_id"), table_name="scenarios")
    op.drop_table("scenarios")
