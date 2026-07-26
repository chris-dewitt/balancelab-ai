"""Stable, prefixed identifiers for domain entities.

Every entity carries a human-scannable, collision-resistant id of the form
``<prefix>_<hex>`` (e.g. ``acct_9f2c...``). Prefixes make ids self-describing in
logs and lineage without a lookup.
"""

from __future__ import annotations

import uuid
from typing import Final

PORTFOLIO: Final = "port"
ACCOUNT: Final = "acct"
INSTRUMENT: Final = "inst"
CASHFLOW: Final = "cf"
SNAPSHOT: Final = "snap"
CALC_NODE: Final = "calc"
SCENARIO: Final = "scen"
ASSUMPTION: Final = "asmp"
FORECAST_RUN: Final = "frun"


def new_id(prefix: str) -> str:
    """Return a new prefixed identifier.

    ``prefix`` should be one of the module-level constants; any short, stable
    token works. The random component is a uuid4 hex string.
    """

    if not prefix or not prefix.isidentifier():
        raise ValueError(f"invalid id prefix: {prefix!r}")
    return f"{prefix}_{uuid.uuid4().hex}"
