# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project uses
milestone-based versioning during pre-release (see [`SPEC.md`](SPEC.md) §13).

## [Unreleased]

### Added — Milestone M1 (persistence)

- Storage layer (`balancelab.storage`): typed repository Protocols
  (`PortfolioRepository`, `SnapshotRepository`, `UnitOfWork`) that speak domain
  models, with two interchangeable backends selected by
  `create_unit_of_work_factory` — an in-memory store (tests, DB-less runs) and a
  SQLAlchemy 2.0 / Postgres backend (JSONB + indexed scalar columns).
- Alembic migrations under `infra/migrations` (initial schema for portfolios and
  snapshots), wired to application settings; `scripts/check_migrations.py` now
  performs an offline SQL smoke always and `upgrade head` + `alembic check`
  (drift detection) when a database is configured.
- Persistence wired into the API: `POST /v1/portfolios/synthetic` and
  `POST /v1/snapshots` persist their results (idempotent by id), and new
  `GET /v1/portfolios/{id}` and `GET /v1/snapshots/{id}` retrieve them with a
  structured 404 when absent. Readiness reports a database check when configured.
- `BALANCELAB_DATABASE_URL` configuration (unset → in-memory backend).
- Backend-agnostic storage contract tests (in-memory always; Postgres opt-in via
  `BALANCELAB_TEST_DATABASE_URL`) plus API persistence e2e coverage.
- CI runs a disposable Postgres service for the storage-contract and live
  migration checks. docker-compose app service now consumes the database.
- ADR 0006 (persistence and the storage boundary). psycopg pinned to the 3.2
  line (3.3 returns the server version as bytes, which SQLAlchemy 2.0 cannot
  parse).

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
