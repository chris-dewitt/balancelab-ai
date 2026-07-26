# 7. Forecast model and upload validation

- Status: Accepted
- Date: 2026-07-26

## Context

M1 adds the deterministic forecast core and validated uploads (`SPEC.md` §4,
§13). Both must respect the deterministic-arithmetic boundary (ADR 0003) and the
synthetic-data policy (ADR 0004), and must keep every projected figure
explainable.

## Decision

**Forecast model.**

1. Assumptions are narrow and typed: per-category **growth rates** applied to
   assets and liabilities. Equity is never a growth target — it is derived.
2. Each period, assets and liabilities grow by their rate and **equity is a
   residual** (`assets − liabilities`), so the balance-sheet identity holds by
   construction every period (no drift to reconcile).
3. The engine is a pure transform (`compute_forecast`), emitting a `ForecastRun`
   with per-period `ForecastValue`s and full `CalculationNode` lineage stamped
   with `forecast-formulas@1`. Money stays `Decimal`; horizon is bounded.
4. Scenarios are immutable/versioned (no in-place update); a correction is a new
   scenario. Duplicate `(target, kind)` assumptions are rejected.

**Upload validation.**

1. `POST /v1/portfolios/validate` is a **dry run**: it validates and reports, and
   persists nothing. Admitting uploads to storage is deferred.
2. Three gates, all issues collected (never raise on bad input): schema
   (Pydantic), policy (declared origin permitted under `synthetic_data_only`),
   and reconciliation (identity within tolerance).
3. JSON and CSV are accepted; other content types return 415; oversized bodies
   are rejected; malformed JSON returns a structured 422.

## Consequences

- Forecasts are reproducible bit-for-bit and fully traceable; changing numeric
  behavior requires bumping `forecast-formulas@1` plus a changelog entry, and the
  pinned forecast golden evals fail until the baseline is regenerated.
- The growth-only assumption set is intentionally limited; rate shocks, macro
  paths, and per-account assumptions are deferred to later milestones and will
  extend `AssumptionKind` and the engine rather than replace them.
- Validation reports admissibility without side effects, which keeps the
  synthetic-only guarantee intact while still giving useful upload feedback.
