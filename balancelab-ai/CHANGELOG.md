# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project uses
milestone-based versioning during pre-release (see [`SPEC.md`](SPEC.md) §13).

## [Unreleased]

### Added — Milestone M0 (deterministic core)

- Repository contract and packaging: `pyproject.toml` (Python 3.12, ruff, mypy,
  pytest, bandit), Apache-2.0 `LICENSE`, and the standard directory layout.
- Platform layer: typed configuration (`config`), structured error taxonomy
  (`errors`), correlation-ID context (`correlation`), and structured JSON logging
  with redaction (`telemetry`).
- Domain schemas (`domain`): `Portfolio`, `Account`, `Instrument`, `CashFlow`,
  `Snapshot`, `CalculationNode`, `Provenance`; immutable, `extra="forbid"`,
  `Decimal` money, currency allow-list, and prefixed stable ids.
- Synthetic data boundary (`synthetic`): deterministic seeded generator
  (`synthetic-generator@1`) producing balanced, labeled portfolios, and
  `ensure_synthetic` enforcing the `synthetic_data_only` policy.
- Deterministic calculation engine (`calc`, formulas `balance-formulas@1`):
  category totals, reconciliation invariant, and full calculation lineage.
- FastAPI surface (`api`): app factory, `/healthz` and `/readyz`, correlation-ID
  middleware, structured exception handlers, and v1 routes
  (`POST /v1/portfolios/synthetic`, `POST /v1/snapshots`).
- Tests: 43 unit/contract/integration tests plus an end-to-end API fixture
  exercising the synthetic → snapshot → lineage path.
- Evaluation: versioned golden + adversarial case set (`evals/`) with a
  deterministic runner and CI smoke stage.
- CI (`.github/workflows/ci.yml`): format, lint, static typing, tests, migration
  check, security scan (bandit), dependency audit (pip-audit), evaluation smoke,
  and container build.
- Containerization: non-root `Dockerfile` and `docker-compose.yml` (Postgres
  wired for M1).
- Documentation: operational `README.md`, `ARCHITECTURE.md`, `SECURITY.md`,
  `EVALUATION.md`, `MODEL_CARD.md`, `DATA_CARD.md`, and ADRs 0001–0005.

### Deferred (tracked for later milestones)

See `docs/adr/0005-deferred-scope.md`. Highlights: persistence + migrations,
scenario/forecast state machines, methodology retrieval, explanation generation,
ML comparison, authN/Z, and the approval + audit-event workflow.
