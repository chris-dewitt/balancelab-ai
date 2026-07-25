"""Tests for correlation-ID context handling."""

from __future__ import annotations

from balancelab.correlation import (
    get_correlation_id,
    new_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)


def test_ids_are_unique() -> None:
    assert new_correlation_id() != new_correlation_id()


def test_set_get_reset_roundtrip() -> None:
    assert get_correlation_id() is None
    token = set_correlation_id("cid-1")
    try:
        assert get_correlation_id() == "cid-1"
        nested = set_correlation_id("cid-2")
        assert get_correlation_id() == "cid-2"
        reset_correlation_id(nested)
        assert get_correlation_id() == "cid-1"
    finally:
        reset_correlation_id(token)
    assert get_correlation_id() is None
