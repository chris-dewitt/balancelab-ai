"""BalanceLab AI: synthetic balance-sheet forecasting and scenario copilot.

The ``balancelab`` package hosts the deterministic domain core and the platform
scaffolding for the milestone M0 vertical slice. Domain logic lives under
:mod:`balancelab.domain`, :mod:`balancelab.synthetic`, and
:mod:`balancelab.calc`, and stays independent of the web framework, provider
SDKs, and deployment infrastructure per ``docs/SHARED_ENGINEERING_STANDARD.md``.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.0.0"
