# Architecture

This document describes the BalanceLab AI architecture as implemented through
milestone **M2 (lineage graph, reconciliations, exports)**, and the seams left
for later milestones. It complements [`SPEC.md`](SPEC.md) §5 (which describes the
full target system) by stating what is actually built today.

## Layering

```text
┌──────────────────────────────────────────────────────────────┐
│ API layer   src/balancelab/api                                 │
│   app factory · correlation-ID middleware · exception handlers │
│   health/readiness · v1 routes (thin adapters)                 │
├──────────────────────────────────────────────────────────────┤
│ Platform    src/balancelab/{config,errors,correlation,telemetry}│
│   typed settings · error taxonomy · correlation context · logs │
├──────────────────────────────────────────────────────────────┤
│ Domain core (framework-independent, fully typed)               │
│   domain/     schemas + invariants (portfolio, scenario,       │
│               forecast, lineage)                               │
│   synthetic/  seeded generator + synthetic-only boundary       │
│   ingest/     upload validation (schema · policy · identity)   │
│   calc/       versioned formulas · snapshot + forecast engines │
├──────────────────────────────────────────────────────────────┤
│ Storage    src/balancelab/storage                              │
│   interfaces (Protocols) · in-memory backend · SQLAlchemy/PG   │
│   backend · Alembic migrations (infra/migrations)              │
└──────────────────────────────────────────────────────────────┘
```

**Dependency rule.** Dependencies point downward only. `domain`, `synthetic`,
and `calc` never import `api`, `storage`, FastAPI, or any provider SDK. The
storage layer depends on the domain (it reads/writes domain models) but nothing
depends on a concrete backend — only on the storage Protocols. This is what makes
the core testable in isolation and portable across delivery mechanisms
(HTTP now, queue/CLI later). It is enforced by review and by the import
structure; a lint rule can formalize it in a later milestone.

## Storage layer (M1)

The `storage` package defines typed repository Protocols (`PortfolioRepository`,
`SnapshotRepository`, `UnitOfWork`) that speak domain models, with two
interchangeable backends selected by `create_unit_of_work_factory`:

- **In-memory** — used by tests and DB-less runs; a shared store outlives
  individual units of work.
- **SQLAlchemy / Postgres** — used when `database_url` is configured. Each table
  stores the full domain object as JSONB (authoritative; reconstructed via
  Pydantic) plus indexed scalar columns. Alembic migrations under
  `infra/migrations` manage the schema.

The API opens one unit of work per request (`api.dependencies.get_uow`),
committing on success and rolling back on error. Writes are idempotent by id.
See ADR 0006 for the rationale.

## Key decisions (see `docs/adr/`)

- **Deterministic arithmetic only.** All authoritative numbers are produced by
  `calc/`, using `decimal.Decimal` (never binary float) and a stamped
  `formula_version`. Models may never compute figures. (ADR 0003.)
- **Money as Decimal.** Amounts are carried and summed as `Decimal`, quantized to
  two minor units; reconciliation permits a documented absolute tolerance only.
- **Immutable, versioned records.** Domain models are frozen (`frozen=True`,
  `extra="forbid"`); corrections create new versions rather than mutating.
- **Synthetic-data boundary.** `synthetic.ensure_synthetic` is the single
  enforcement point for the `synthetic_data_only` policy. (ADR 0004.)

## Request flow (M0 signature path)

```text
POST /v1/portfolios/synthetic {seed}
  → generate_synthetic_portfolio(seed)            # deterministic, labeled
  → Portfolio (201)

POST /v1/snapshots {portfolio}
  → ensure_synthetic(portfolio)                   # policy boundary
  → compute_snapshot(portfolio)                   # totals + lineage
      ├─ leaf CalculationNode per account
      ├─ category-total nodes (assets/liabilities/equity)
      └─ reconciliation node (residual within tolerance, else 422)
  → Snapshot (201) with full lineage
```

Every request is assigned a correlation ID (honoring an inbound
`X-Correlation-ID`), which is bound to the logging context and echoed on the
response and in error bodies.

## Scenarios and forecasts (M1)

A `Scenario` is a bounded, versioned description of a forecast: a base portfolio,
a horizon, and typed `Assumption`s (per-category growth rates in this slice;
equity is never a target — it is a residual). `compute_forecast` projects assets
and liabilities forward period by period and carries equity as
`assets − liabilities`, so the balance-sheet identity holds in every period by
construction. The result is a `ForecastRun` with per-period `ForecastValue`s and
a full `CalculationNode` lineage stamped with `forecast-formulas@1`. Scenarios
follow the immutability rule: there is no in-place update — a correction is a new
scenario.

## Upload validation (M1)

`balancelab.ingest.validate_upload` is a dry-run validator: it builds a typed
portfolio from an untrusted JSON/CSV payload and reports schema, data-origin
policy, and reconciliation issues without persisting anything. It collects all
issues rather than failing on the first, and never raises on bad input.

## Calculation lineage

`Snapshot.lineage` (and `ForecastRun.lineage`) is a tuple of `CalculationNode`s.
Each node records its `label`, `formula`, `formula_version`, `inputs` (ids of
upstream nodes or source accounts), `value`, and `unit`. Leaf nodes reference the
source `Account` id; aggregate nodes reference the ids of the nodes they combine.
This makes every displayed number traceable end-to-end, satisfying the MVP
acceptance criterion that no figure is unexplained.

### Lineage graph, reconciliation, and export (M2)

`balancelab.domain.lineage` turns the flat node tuple into an explicit directed
graph: `build_lineage_graph` derives edges (`from_id -> to_id`), `root_ids`
(nodes consumed by nothing — the final figures), and `source_ids` (external
inputs such as accounts), all in deterministic first-appearance order.
`resolve_lineage(nodes, target_id)` returns the transitive input closure that
explains a single figure — the API exposes this per node.

`balancelab.reconcile` derives `Reconciliation` records (one identity check for a
snapshot; one per period for a forecast) deterministically from stored results.
`balancelab.export` assembles self-contained `SnapshotExport` / `ForecastExport`
bundles — inputs, result, reconciliation, and lineage graph, tagged with an
export schema version — served as downloadable JSON. All three are pure
functions; nothing here performs I/O or persists.

## Error handling

Domain/platform code raises typed `BalanceLabError` subclasses carrying a stable
`ErrorCode` and safe `details`. The API layer maps them to structured responses;
unexpected exceptions are logged with the correlation ID and returned as a
generic internal error so internals never leak.

## What is deliberately deferred

Model/provider adapters, scenario and forecast state machines, methodology
retrieval, and explanation generation are **not** built yet. Persistence
(Postgres + migrations) landed in M1 (see above). The layering leaves clear seams
for the rest: new typed interfaces in the platform/storage layers, new domain
services below the API, and additional lineage node kinds. Deferred scope is
tracked in `docs/adr/0005-deferred-scope.md` and `CHANGELOG.md`.
