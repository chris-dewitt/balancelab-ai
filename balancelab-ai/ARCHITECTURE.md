# Architecture

This document describes the BalanceLab AI architecture as implemented at
milestone **M0**, and the seams left for later milestones. It complements
[`SPEC.md`](SPEC.md) §5 (which describes the full target system) by stating what
is actually built today.

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
│   domain/     schemas + invariants                             │
│   synthetic/  seeded generator + synthetic-only boundary       │
│   calc/       versioned formulas + lineage engine              │
└──────────────────────────────────────────────────────────────┘
```

**Dependency rule.** Dependencies point downward only. `domain`, `synthetic`,
and `calc` never import `api`, FastAPI, or any provider SDK. This is what makes
the core testable in isolation and portable across delivery mechanisms
(HTTP now, queue/CLI later). It is enforced by review and by the import
structure; a lint rule can formalize it in a later milestone.

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

## Calculation lineage

`Snapshot.lineage` is a tuple of `CalculationNode`s. Each node records its
`label`, `formula`, `formula_version`, `inputs` (ids of upstream nodes or source
accounts), `value`, and `unit`. Leaf nodes reference the source `Account` id;
aggregate nodes reference the ids of the nodes they combine. This makes every
displayed number traceable end-to-end, satisfying the MVP acceptance criterion
that no figure is unexplained.

## Error handling

Domain/platform code raises typed `BalanceLabError` subclasses carrying a stable
`ErrorCode` and safe `details`. The API layer maps them to structured responses;
unexpected exceptions are logged with the correlation ID and returned as a
generic internal error so internals never leak.

## What is deliberately deferred

Persistence (Postgres + migrations), model/provider adapters, scenario and
forecast state machines, methodology retrieval, and explanation generation are
**not** in M0. The layering leaves clear seams for them: new typed interfaces in
the platform layer, new domain services below the API, and additional lineage
node kinds. Deferred scope is tracked in `docs/adr/0005-deferred-scope.md` and
`CHANGELOG.md`.
