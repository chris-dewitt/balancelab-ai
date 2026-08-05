"""Helpers for golden-report tests.

Export bundles and lineage graphs contain volatile fields — random entity ids and
timestamps — that would make byte-for-byte golden comparison impossible. The
normalizer replaces those with stable placeholders while preserving referential
structure (each distinct id maps to a stable ordinal per prefix, so cross
references still line up), so the *shape and values* of a report can be pinned.
"""

from __future__ import annotations

import re
from typing import Any

_ID_RE = re.compile(r"^(port|acct|inst|cf|snap|calc|scen|asmp|frun|recon)_[0-9a-f]{32}$")
_TIMESTAMP_KEYS = frozenset({"created_at", "exported_at", "retrieved_at"})


def _map_id(value: str, mapping: dict[str, str]) -> str:
    if value not in mapping:
        prefix = value.split("_", 1)[0]
        count = sum(1 for v in mapping.values() if v.startswith(f"<{prefix}:"))
        mapping[value] = f"<{prefix}:{count}>"
    return mapping[value]


def normalize(obj: Any, mapping: dict[str, str] | None = None) -> Any:
    """Return ``obj`` with random ids and timestamps replaced by placeholders."""

    if mapping is None:
        mapping = {}
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if key in _TIMESTAMP_KEYS and value is not None:
                out[key] = "<ts>"
            else:
                out[key] = normalize(value, mapping)
        return out
    if isinstance(obj, list):
        return [normalize(item, mapping) for item in obj]
    if isinstance(obj, str) and _ID_RE.match(obj):
        return _map_id(obj, mapping)
    return obj
