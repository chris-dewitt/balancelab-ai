# Model Card

## Summary

At milestone **M0, BalanceLab AI uses no machine-learning or large-language
model.** All outputs are produced by a deterministic calculation engine. This
card documents that engine and, importantly, the boundary that keeps models out
of authoritative computation as models are introduced in later milestones.

This card exists now (rather than when the first model ships) to make the "no
model in the arithmetic path" guarantee explicit and auditable from the start.

## The deterministic engine (M0)

- **Component:** `balancelab.calc` (formulas `balance-formulas@1`).
- **Inputs:** a validated `Portfolio` (typed, synthetic-labeled).
- **Outputs:** a `Snapshot` with `total_assets`, `total_liabilities`,
  `total_equity`, a `balances` flag, and a full `lineage` of `CalculationNode`s.
- **Method:** exact `Decimal` summation per account category and a reconciliation
  check (`assets − (liabilities + equity)`) against a configured absolute
  tolerance. No learning, no randomness in computation, no external calls.
- **Versioning:** every lineage node stamps `formula_version`; changing numeric
  behavior requires bumping it and recording it in `CHANGELOG.md`.
- **Determinism:** identical input → identical output, always.

## Intended use

Demonstration and testing of deterministic balance-sheet computation with full
lineage, on synthetic data. **Not** for real financial reporting, regulatory
use, or investment advice (see [`SPEC.md`](SPEC.md) §4 out-of-scope).

## Limitations

- Covers balance-sheet totals and the accounting identity only; income,
  liquidity, and risk calculations are deferred.
- Single-currency portfolios only.

## The model boundary (applies to all future milestones)

When LLMs are introduced (natural-language scenario drafting in M3, methodology
explanations in M4, ML forecast comparison in M5), the following rules are
non-negotiable and enforced by design:

- Models **never** perform authoritative arithmetic, authorization, or policy
  decisions. They may only produce typed drafts (validated against schemas) and
  narrate results that reference already-computed lineage.
- Model output is untrusted input: parsed, schema-validated, and unable to
  introduce figures absent from calculation results.
- Provider selection and any fallback are explicit and traceable; no silent
  fallback.
- Prompts and evaluation datasets are versioned; model changes require evaluation
  against a pinned regression suite.
- Synthetic or LLM-generated evaluation data is labeled as such.

Each future model integration will add its own section here (provider, version,
prompt version, evaluation results, cost/latency, and known failure modes).
