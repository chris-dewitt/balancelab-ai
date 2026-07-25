"""Alembic migration environment.

Resolves the database URL from application settings (so migrations and the app
agree on configuration) and targets the ORM metadata for autogenerate support.
Supports both offline (SQL emitting, no DB) and online (live DB) modes.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

from balancelab.config import get_settings
from balancelab.storage.orm import Base

config = context.config

# Target metadata for 'autogenerate' and 'alembic check'.
target_metadata = Base.metadata

# In offline mode we still need a URL/dialect; default to the postgresql dialect
# so generated SQL matches the production backend even without a live database.
_settings = get_settings()
_url = _settings.database_url or "postgresql+psycopg://localhost/balancelab"
config.set_main_option("sqlalchemy.url", _url)


def run_migrations_offline() -> None:
    """Emit SQL without a live database connection."""

    context.configure(
        url=_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""

    section = config.get_section(config.config_ini_section, {})
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
