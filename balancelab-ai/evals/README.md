# Evaluation harness

Deterministic evaluation for the BalanceLab AI M0 core. No network, no model
calls — every case is reproducible from a seed.

## Cases

`cases/golden_reconciliation.json` (dataset version `1`, `data_origin: synthetic`):

- **golden** cases pin exact totals (`total_assets`, `total_liabilities`,
  `total_equity`) and the lineage-node count for a fixed seed. They fail if a
  formula change alters any authoritative figure — a numerical-regression gate.
- **adversarial** cases corrupt a balanced portfolio and assert the engine
  raises a reconciliation error, proving the balance-sheet invariant is enforced.

## Running

```bash
python -m evals.runner                 # uses the default golden set
python -m evals.runner path/to.json    # a specific case file
```

The runner prints per-case `PASS`/`FAIL` lines and an aggregate, and exits
non-zero on any regression. It is wired into CI as the "evaluation smoke suite"
stage and is also covered by `tests/test_evals_smoke.py`.

## Extending the set

As later milestones add scenarios, forecasts, and explanations, add matching
case kinds here (malformed input, timeout, empty result, contradictory evidence,
dependency failure) per `SPEC.md` §10. Regenerate pinned golden values only when
a formula version is intentionally bumped, and record the bump in `CHANGELOG.md`.
