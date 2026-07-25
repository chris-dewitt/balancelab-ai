"""initial schema: portfolios and snapshots

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-25

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_portfolios_as_of_date"), "portfolios", ["as_of_date"], unique=False)

    op.create_table(
        "snapshots",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("portfolio_id", sa.String(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("total_assets", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("total_liabilities", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("total_equity", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("balances", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_snapshots_as_of_date"), "snapshots", ["as_of_date"], unique=False)
    op.create_index(op.f("ix_snapshots_portfolio_id"), "snapshots", ["portfolio_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_snapshots_portfolio_id"), table_name="snapshots")
    op.drop_index(op.f("ix_snapshots_as_of_date"), table_name="snapshots")
    op.drop_table("snapshots")
    op.drop_index(op.f("ix_portfolios_as_of_date"), table_name="portfolios")
    op.drop_table("portfolios")
