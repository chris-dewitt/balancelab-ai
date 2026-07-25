# Evaluation

BalanceLab AI's evaluation follows
[`docs/SHARED_ENGINEERING_STANDARD.md`](docs/SHARED_ENGINEERING_STANDARD.md) §8
and [`SPEC.md`](SPEC.md) §10. This document describes what is measured at
milestone **M0**.

## Dataset

- **Name / version:** `balancelab-m0-reconciliation`, version `1`.
- **Location:** `evals/cases/golden_reconciliation.json`.
- **Data origin:** synthetic (seeded, reproducible). Labeled `data_origin:
  synthetic` in the file.

The dataset contains two case kinds:

| Kind | What it checks |
| ---- | -------------- |
| `golden` | Pins exact totals (`total_assets`, `total_liabilities`, `total_equity`) and lineage-node count per seed. Fails on any numerical change → **regression gate**. |
| `adversarial` | Corrupts a balanced portfolio and asserts the engine raises a reconciliation error → **invariant enforcement**. |

## Metrics (M0)

- **Numerical reproducibility:** identical seed → identical figures (deterministic
  generator + `Decimal` arithmetic). Verified by golden cases and unit tests.
- **Reconciliation correctness:** `assets == liabilities + equity` within the
  configured absolute tolerance; violations fail closed. Verified by adversarial
  cases and `tests/test_calc_engine.py`.
- **Schema-validation behavior:** malformed input is rejected with a structured
  error. Verified by `tests/test_domain_models.py` and `tests/test_api_e2e.py`.
- **Latency / cost:** M0 performs no model or network calls, so there is no token
  cost; runtime is compute-only and the full suite completes in well under a
  second locally. Model quality/cost/latency metrics are introduced with the LLM
  milestones (M3+).

Deterministic checks are primary. LLM-as-judge scoring is **not** used in M0 and,
per the shared standard, may only ever supplement (never replace) deterministic
checks, using pinned prompts/models/calibration.

## Baseline vs candidate

The pinned golden values are the **baseline**. Any change that alters an
authoritative figure makes the current build the **candidate** and fails the
eval, forcing an intentional formula-version bump plus a `CHANGELOG.md` entry
before the baseline is regenerated. This is the M0 form of the cross-project
"fail on regression" gate.

## Running

```bash
python -m evals.runner        # prints per-case PASS/FAIL + aggregate; non-zero on regression
```

Wired into CI as the *Evaluation smoke suite* stage and covered by
`tests/test_evals_smoke.py`.

## Known limitations & expected failure modes

- Coverage is limited to balance-sheet totals and the reconciliation invariant;
  income/liquidity/risk calculations and their cases are deferred.
- No adversarial coverage yet for timeout, empty-result, contradictory-evidence,
  or dependency-failure paths (these become relevant once external
  dependencies/models exist — M1+). They are listed in `evals/README.md` as the
  extension backlog.
