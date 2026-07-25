"""HTTP API layer for BalanceLab AI.

This package is the only place the web framework appears. It adapts typed
requests to the framework-independent domain and calculation core and back.
"""

from __future__ import annotations

from balancelab.api.app import create_app

__all__ = ["create_app"]
