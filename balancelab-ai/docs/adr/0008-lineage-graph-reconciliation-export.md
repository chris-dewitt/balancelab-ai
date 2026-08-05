# 8. Lineage graph, reconciliation, and export

- Status: Accepted
- Date: 2026-07-26

## Context

M2 makes lineage first-class and adds reconciliations, exports, and golden report
tests (`SPEC.md` §13; §7 API contract lists `/lineage`, `/reconciliation`, and
comparison/export surfaces). Snapshots and forecasts already carry a flat tuple
of `CalculationNode`s; M2 exposes and packages that provenance.

## Decision

1. **Lineage is derived, not stored separately.** `build_lineage_graph` and
   `resolve_lineage` are pure functions over the existing node tuples. Graphs are
   computed on demand; no new tables. `source_ids` are ordered by first
   appearance (not by random id) so output is deterministic.
2. **Reconciliations are derived and computed on demand.** One identity check per
   snapshot; one per period per forecast. They are reproducible from stored
   results, so persisting them would only duplicate derivable state — deferred.
3. **Exports are self-contained JSON bundles** (`SnapshotExport` /
   `ForecastExport`) carrying inputs, result, reconciliation, and lineage graph,
   tagged with an export schema version and served with a download header. This
   is the M2 precursor to the signature-demo audit export (which will add
   approvals and evidence).
4. **Golden report tests** pin whole export bundles after normalizing volatile
   ids/timestamps to stable placeholders, preserving referential structure. They
   gate report regressions; fixtures are regenerated deliberately with a
   changelog note.

## Consequences

- Every reported figure is now independently traceable (per-node resolution) and
  exportable for offline verification, advancing the "no unexplained number"
  acceptance criterion toward the signature demo.
- Keeping reconciliations/lineage derived (not persisted) keeps the schema small
  and avoids drift between stored and recomputed values; if query/audit needs
  demand it later, a persisted projection can be added behind the same types.
- Determinism of graph ordering and export shape is now covered by golden tests,
  so accidental changes to provenance structure fail CI.
