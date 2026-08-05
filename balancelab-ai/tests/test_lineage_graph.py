"""Tests for the lineage graph builders."""

from __future__ import annotations

from decimal import Decimal

import pytest

from balancelab.calc.engine import compute_snapshot
from balancelab.domain.lineage import build_lineage_graph, resolve_lineage
from balancelab.domain.models import CalculationNode
from balancelab.synthetic.generator import generate_synthetic_portfolio


def _nodes() -> tuple[CalculationNode, ...]:
    leaf_a = CalculationNode(
        label="a",
        formula="source",
        formula_version="v",
        inputs=("acct_x",),
        value=Decimal("1"),
        unit="USD",
    )
    leaf_b = CalculationNode(
        label="b",
        formula="source",
        formula_version="v",
        inputs=("acct_y",),
        value=Decimal("2"),
        unit="USD",
    )
    total = CalculationNode(
        label="total",
        formula="a+b",
        formula_version="v",
        inputs=(leaf_a.id, leaf_b.id),
        value=Decimal("3"),
        unit="USD",
    )
    return (leaf_a, leaf_b, total)


def test_graph_edges_roots_and_sources() -> None:
    leaf_a, leaf_b, total = _nodes()
    graph = build_lineage_graph((leaf_a, leaf_b, total))
    assert len(graph.nodes) == 3
    # 2 leaf->source edges + 2 leaf->total edges.
    assert len(graph.edges) == 4
    # Only the total node is not consumed by anything else.
    assert graph.root_ids == (total.id,)
    # The two account ids are external sources, in first-appearance order.
    assert graph.source_ids == ("acct_x", "acct_y")


def test_resolve_returns_transitive_closure() -> None:
    leaf_a, leaf_b, total = _nodes()
    nodes = (leaf_a, leaf_b, total)
    sub = resolve_lineage(nodes, total.id)
    assert {n.id for n in sub.nodes} == {leaf_a.id, leaf_b.id, total.id}

    leaf_only = resolve_lineage(nodes, leaf_a.id)
    assert {n.id for n in leaf_only.nodes} == {leaf_a.id}


def test_resolve_unknown_node_raises() -> None:
    with pytest.raises(KeyError):
        resolve_lineage(_nodes(), "calc_missing")


def test_snapshot_graph_root_is_reconciliation() -> None:
    snapshot = compute_snapshot(generate_synthetic_portfolio(seed=1))
    graph = build_lineage_graph(snapshot.lineage)
    roots = [n for n in graph.nodes if n.id in graph.root_ids]
    assert len(roots) == 1
    assert roots[0].label == "balance_residual"
