"""Shared HTTP helpers for lineage and export routes."""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import Response

from balancelab.domain.lineage import LineageGraph, resolve_lineage
from balancelab.domain.models import CalculationNode
from balancelab.errors import NotFoundError


def resolve_or_404(nodes: Iterable[CalculationNode], node_id: str) -> LineageGraph:
    """Resolve the sub-graph explaining ``node_id``, or raise a structured 404."""

    try:
        return resolve_lineage(nodes, node_id)
    except KeyError as exc:
        raise NotFoundError("lineage node not found", details={"node_id": node_id}) from exc


def attach_download_headers(response: Response, filename: str) -> None:
    """Mark a JSON response as a downloadable attachment."""

    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
