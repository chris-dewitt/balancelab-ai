"""Tests for typed configuration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from balancelab.config import Settings, get_settings


def test_defaults_are_safe() -> None:
    settings = Settings()
    assert settings.app_name == "balancelab-ai"
    assert settings.environment == "local"
    assert settings.synthetic_data_only is True
    assert settings.reconciliation_abs_tolerance >= 0
    assert settings.is_production is False


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BALANCELAB_ENVIRONMENT", "production")
    monkeypatch.setenv("BALANCELAB_LOG_LEVEL", "error")
    settings = Settings()
    assert settings.environment == "production"
    assert settings.is_production is True
    assert settings.log_level == "error"


def test_invalid_environment_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BALANCELAB_ENVIRONMENT", "not-a-real-env")
    with pytest.raises(ValidationError):
        Settings()


def test_negative_tolerance_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(reconciliation_abs_tolerance=-1.0)


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    assert get_settings() is get_settings()
