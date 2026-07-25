# 3. Deterministic calculation boundary and Decimal money

- Status: Accepted
- Date: 2026-07-25

## Context

The product's core promise is that every displayed figure is authoritative,
reproducible, and traceable, and that language models never author numbers
(`SPEC.md` §3, §15; shared standard §6). Binary floating point is unsuitable for
financial arithmetic.

## Decision

1. **All authoritative arithmetic lives in `balancelab.calc`** and nowhere else.
   Functions there are pure (no I/O, no randomness, no model calls).
2. **Monetary amounts use `decimal.Decimal`**, quantized to two minor units.
   Reconciliation permits only a documented absolute tolerance
   (`reconciliation_abs_tolerance`).
3. **Every authoritative number is emitted with lineage.** `compute_snapshot`
   produces a `CalculationNode` for each source account and each aggregate, each
   stamped with a `formula_version`.
4. **Models may never compute figures.** No model exists in M0; when introduced,
   models only produce schema-validated drafts and narrate existing lineage.

## Consequences

- Results are reproducible bit-for-bit given the same input.
- Formula changes are visible: a `formula_version` bump plus a `CHANGELOG.md`
  entry are required, and pinned golden evals fail until the baseline is
  regenerated intentionally.
- A small tolerance is accepted for reconciliation to absorb representable
  rounding; it is configurable and defaults to one cent.
