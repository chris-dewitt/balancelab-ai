"""Synthetic, labeled data generation for BalanceLab AI.

This package is the *only* sanctioned source of portfolio data in the M0 slice.
Everything it produces is deterministic (seeded), reproducible, and explicitly
labeled with :class:`~balancelab.domain.models.DataOrigin.SYNTHETIC` provenance.
"""

from __future__ import annotations

from balancelab.synthetic.generator import (
    GENERATOR_VERSION,
    ensure_synthetic,
    generate_synthetic_portfolio,
)

__all__ = ["GENERATOR_VERSION", "ensure_synthetic", "generate_synthetic_portfolio"]
