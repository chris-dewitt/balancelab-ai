"""Calculation-lineage graph.

Snapshots and forecasts each carry a flat tuple of
:class:`~balancelab.domain.models.CalculationNode`. This module turns that tuple
into an explicit directed graph so any reported figure can be traced to the
inputs that produced it.

Edges point from an input to the node that consumes it (``from_id -> to_id``).
An input id that is not itself produced by a node is a *source* (e.g. a source
account id); a node consumed by no other node is a *root* (e.g. the final
reconciliation node). Both the builders here are pure functions over domain
models — no I/O, no mutation of inputs.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping

from balancelab.domain.base import DomainModel
from balancelab.domain.models import CalculationNode


class LineageEdge(DomainModel):
    """A directed dependency: ``from_id`` feeds ``to_id``."""

    from_id: str
    to_id: str


class LineageGraph(DomainModel):
    """A directed acyclic graph of calculation nodes.

    ``source_ids`` are input ids not produced by any node (external sources such
    as source accounts). ``root_ids`` are nodes not consumed by any other node.
    """

    nodes: tuple[CalculationNode, ...]
    edges: tuple[LineageEdge, ...]
    source_ids: tuple[str, ...] = ()
    root_ids: tuple[str, ...] = ()

    def node_ids(self) -> frozenset[str]:
        return frozenset(node.id for node in self.nodes)


def _index(nodes: Iterable[CalculationNode]) -> dict[str, CalculationNode]:
    return {node.id: node for node in nodes}


def build_lineage_graph(nodes: Iterable[CalculationNode]) -> LineageGraph:
    """Build the full lineage graph from a flat node collection."""

    node_list = tuple(nodes)
    by_id = _index(node_list)
    edges: list[LineageEdge] = []
    consumed: set[str] = set()
    # dict preserves first-appearance order (deterministic), unlike a set.
    sources: dict[str, None] = {}

    for node in node_list:
        for input_id in node.inputs:
            edges.append(LineageEdge(from_id=input_id, to_id=node.id))
            if input_id in by_id:
                consumed.add(input_id)
            else:
                sources.setdefault(input_id, None)

    roots = tuple(node.id for node in node_list if node.id not in consumed)
    return LineageGraph(
        nodes=node_list,
        edges=tuple(edges),
        source_ids=tuple(sources),
        root_ids=roots,
    )


def resolve_lineage(nodes: Iterable[CalculationNode], target_id: str) -> LineageGraph:
    """Return the sub-graph explaining ``target_id``.

    The result contains ``target_id`` and the transitive closure of the nodes
    that feed it, so a client can trace a single figure end to end. Raises
    ``KeyError`` if ``target_id`` is not a node in the collection.
    """

    by_id: Mapping[str, CalculationNode] = _index(nodes)
    if target_id not in by_id:
        raise KeyError(target_id)

    # Walk inputs backwards from the target, collecting reachable nodes.
    kept: dict[str, CalculationNode] = {}
    queue: deque[str] = deque([target_id])
    while queue:
        current = queue.popleft()
        if current in kept or current not in by_id:
            continue
        node = by_id[current]
        kept[current] = node
        queue.extend(node.inputs)

    return build_lineage_graph(kept.values())
