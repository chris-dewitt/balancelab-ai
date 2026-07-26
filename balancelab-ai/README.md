# BalanceLab AI

**Synthetic balance-sheet forecasting and scenario copilot — deterministic core (milestone M0).**

BalanceLab AI turns natural-language scenarios into validated, typed assumptions,
runs **deterministic** balance-sheet forecasts, and explains every result with
complete calculation lineage. Authoritative numbers are always computed by code,
never authored by a language model.

> **Status — M0 complete; M1 complete.** This repository ships the deterministic
> core (synthetic-data boundary, typed domain schemas, balance-sheet formulas
> with full lineage, FastAPI surface, telemetry, evaluation smoke tests, CI) and
> all of **M1**: a typed persistence boundary with in-memory and
> SQLAlchemy/Postgres backends and Alembic migrations; upload validation;
> versioned scenarios with CRUD; and a deterministic forecast engine with full
> lineage. Remaining scope (M2–M5: lineage graph/exports, natural-language
> scenario drafting + approval, methodology retrieval, explanations, ML
> comparison) is not yet built. **Do not treat planned capabilities as shipped.**
> See [`SPEC.md`](SPEC.md) §13 for the milestone map.

## What problem this solves

Finance and risk practitioners need forecasts they can *defend*: every displayed
figure must trace to a formula, its inputs, its units, and the exact code version
that produced it. LLMs are excellent at turning intent into structure and
explaining results, but unsuitable for authoritative arithmetic. BalanceLab
splits those roles — the language model (in later milestones) only proposes typed
drafts and narrates; a deterministic engine computes the numbers and records
lineage.

## Why AI is appropriate here

AI is scoped to the tasks it is reliable at: converting natural-language
scenarios into a *typed draft* that a human approves, and explaining results by
referencing already-computed lineage. It never performs calculations,
authorization, or policy decisions. This boundary is a hard architectural rule,
not a guideline (see [`AGENTS.md`](AGENTS.md) and
[`docs/SHARED_ENGINEERING_STANDARD.md`](docs/SHARED_ENGINEERING_STANDARD.md) §6).

## Architecture (M0)

```text
Client / CLI
     |
FastAPI (src/balancelab/api)      # health, structured errors, correlation IDs
     |
Deterministic domain core         # framework-independent, fully typed
  ├─ domain/     typed schemas (Portfolio, Account, ..., CalculationNode)
  ├─ synthetic/  seeded, labeled synthetic data + the synthetic-only boundary
  └─ calc/       versioned formulas + lineage-producing engine
     |
(future) Postgres/artifacts, model providers, retrieval — deferred to M1+
```

The domain core does not import FastAPI, the storage layer, or any provider SDK.
Persistence sits behind typed repository Protocols with in-memory and
Postgres backends; the app runs without a database (in-memory) or with one when
`BALANCELAB_DATABASE_URL` is set. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for
details.

## Local setup

Requires Python 3.12 (and Docker for the container/compose targets).

```bash
cd balancelab-ai
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Run the service

Without a database (in-memory store — data is not durable):

```bash
uvicorn balancelab.api.app:app --reload
curl localhost:8000/healthz
curl localhost:8000/readyz
```

With Postgres (durable), set the connection URL and apply migrations first:

```bash
export BALANCELAB_DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/balancelab"
python -m alembic upgrade head
uvicorn balancelab.api.app:app --reload
```

Or bring up the app with a local Postgres via Compose (see
[`docker-compose.yml`](docker-compose.yml) for the migration step):

```bash
docker compose up --build
```

### Validation commands (mirror CI)

```bash
./scripts/check.sh          # runs everything below in order
# individually:
ruff format --check .       # formatting
ruff check .                # lint
mypy                        # static typing (strict)
pytest -q                   # unit, contract, integration & e2e tests
python scripts/check_migrations.py   # migrations: offline smoke; live check if DB configured
bandit -q -c pyproject.toml -r src   # static security scan
pip-audit --skip-editable --progress-spinner off   # dependency audit
python -m evals.runner      # deterministic evaluation smoke suite
```

## Demo (≈ deterministic, offline)

`examples/demo.py` runs the full M0 path and prints a trace where every total
resolves to a formula, inputs, unit, and formula version:

```bash
python examples/demo.py 7
```

```text
Snapshot (deterministic):
  total_assets       = 6583581.11 USD
  total_liabilities  = 3801462.86 USD
  total_equity       = 2782118.25 USD
  balances (A=L+E)   = True

Calculation lineage:
  ...
  total_asset: 6583581.11 USD  [formula='sum(account.balance for account in category)' v=balance-formulas@1 inputs=calc_..., calc_..., calc_...]
  balance_residual: 0.00 USD   [formula='total_asset - (total_liability + total_equity)' v=balance-formulas@1 inputs=...]
```

The HTTP equivalent: `POST /v1/portfolios/synthetic` then `POST /v1/snapshots`.

## API (v1)

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET  | `/healthz` | Liveness. |
| GET  | `/readyz`  | Readiness + core policy checks. |
| POST | `/v1/portfolios/synthetic` | Generate and persist a reproducible synthetic portfolio from a seed. |
| POST | `/v1/portfolios/validate` | Validate an uploaded balance sheet (JSON or CSV); returns a structured report, persists nothing. |
| GET  | `/v1/portfolios/{id}` | Retrieve a stored portfolio (structured 404 if absent). |
| POST | `/v1/snapshots` | Compute and persist a fully-traced deterministic snapshot (enforces the synthetic-only boundary). |
| GET  | `/v1/snapshots/{id}` | Retrieve a stored snapshot (structured 404 if absent). |
| POST | `/v1/scenarios` | Create a forecast scenario over an existing portfolio. |
| GET  | `/v1/scenarios` · `/v1/scenarios/{id}` | List / retrieve scenarios. |
| DELETE | `/v1/scenarios/{id}` | Delete a scenario. |
| POST | `/v1/forecasts` | Run and persist a deterministic forecast for a scenario. |
| GET  | `/v1/forecasts/{id}` · `/v1/forecasts/{id}/lineage` | Retrieve a forecast run / its calculation lineage. |

All responses carry an `X-Correlation-ID`; errors use a structured body
(`code`, `message`, `correlation_id`, `details`). See
[`SPEC.md`](SPEC.md) §7 for the full planned API contract.

## Quality, cost & latency

- **Deterministic evaluation:** golden cases pin exact totals per seed;
  adversarial cases assert the reconciliation invariant. See
  [`EVALUATION.md`](EVALUATION.md) and `evals/`.
- **Cost/latency:** M0 makes **no model or network calls** — the core is pure
  computation, so per-request cost is compute-only and there is no token spend.
  Model cost/latency budgets are introduced with the LLM milestones (M3+).

## Security

Threat model, trust boundaries, and the synthetic-data policy are documented in
[`SECURITY.md`](SECURITY.md). Highlights: synthetic-or-public data only, model
output treated as untrusted, secrets never committed, structured-log redaction,
and least-privilege containers.

## Data & model cards

- [`DATA_CARD.md`](DATA_CARD.md) — synthetic data generation, labeling, limits.
- [`MODEL_CARD.md`](MODEL_CARD.md) — M0 uses no ML/LLM model; documents the
  deterministic engine and the boundary that keeps models out of arithmetic.

## Known limitations (M0)

- Single-currency portfolios only; no multi-currency consolidation yet.
- Forecast assumptions are per-category growth rates over a bounded horizon;
  rate shocks, macro paths, and per-account assumptions are deferred.
- Upload validation is a dry run — validated uploads are not yet admitted to
  storage (persisting uploads is deferred).
- Natural-language scenario drafting, approval workflow, methodology retrieval,
  explanations, and ML comparison are not built yet (M2–M5).
- The synthetic generator produces balance-sheet totals only; income,
  liquidity, and risk calculations are deferred.

## Repository layout

See [`docs/SHARED_ENGINEERING_STANDARD.md`](docs/SHARED_ENGINEERING_STANDARD.md)
§4 for the repository contract. Source-of-truth documents:
[`SPEC.md`](SPEC.md), [`AGENTS.md`](AGENTS.md), and the shared standard.
Architecture decisions are recorded under [`docs/adr/`](docs/adr/).

## License

[Apache License 2.0](LICENSE).
