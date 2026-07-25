"""Typed application configuration.

Configuration is loaded from environment variables (optionally an ``.env`` file
during local development) and validated with Pydantic. Secrets are never
committed; only their environment-variable names appear here.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "ci", "staging", "production"]
LogLevel = Literal["debug", "info", "warning", "error"]


class Settings(BaseSettings):
    """Runtime settings for the BalanceLab service.

    All fields carry safe, non-secret defaults so the M0 slice runs without any
    external configuration. Fields intended to hold secrets (for later
    milestones) must be sourced from the environment and never persisted.
    """

    model_config = SettingsConfigDict(
        env_prefix="BALANCELAB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    app_name: str = "balancelab-ai"
    environment: Environment = "local"
    log_level: LogLevel = "info"

    # API surface.
    api_version: str = "v1"

    # Persistence. When unset, the service uses an in-memory store (no durability)
    # so it runs without a database; when set, the SQLAlchemy/Postgres backend is
    # used. This is a connection URL, not a secret to embed — provide it via the
    # environment (e.g. postgresql+psycopg://user:pass@host/db).
    database_url: str | None = None

    # Deterministic-core guardrails. These are policy switches, not secrets.
    # The reconciliation tolerance bounds acceptable floating-point drift when
    # checking the balance-sheet identity; it is a currency-minor-unit amount.
    reconciliation_abs_tolerance: float = Field(default=0.01, ge=0.0)

    # Hard boundary: synthetic data only. Flipping this off is intentionally
    # unsupported in M0 and guarded by the synthetic data module.
    synthetic_data_only: bool = True

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    Cached so configuration is parsed once. Tests that need alternate settings
    should call :func:`get_settings.cache_clear` or construct ``Settings``
    directly with overrides.
    """

    return Settings()
