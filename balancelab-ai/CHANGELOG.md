# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project uses
milestone-based versioning during pre-release (see [`SPEC.md`](SPEC.md) §13).

## [Unreleased]

### Added — Milestone M2 (lineage graph, reconciliations, exports)

- Calculation-lineage graph (`balancelab.domain.lineage`): `build_lineage_graph`
  turns a flat node tuple into a directed graph (edges, roots, external sources
  in deterministic order); `resolve_lineage` returns the transitive input closure
  explaining a single figure.
- Reconciliation records (`balancelab.domain.reconciliation`,
  `balancelab.reconcile`): derived deterministically — one identity check for a
  snapshot, one per period for a forecast, each with residual and tolerance.
- Export bundles (`balancelab.domain.export`, `balancelab.export`): self-contained
  `SnapshotExport` / `ForecastExport` (inputs + result + reconciliation + lineage
  graph), tagged with an export schema version.
- API: `GET /v1/snapshots/{id}/lineage`, `/lineage/graph`, `/lineage/{node_id}`,
  `/reconciliation`, and `/export` (download); the same family under
  `/v1/forecasts/{id}`.
- Golden report tests: pinned snapshot/forecast export fixtures under
  `tests/golden/` with an id/timestamp normalizer (`tests/golden_utils.py`).
- New `unsupported_media_type` error already existed; no schema changes to
  persisted tables (M2 additions are all derived/computed on demand).

### Added — Milestone M1 (upload validation, scenarios, forecast core)

- Upload validation: `POST /v1/portfolios/validate` accepts a candidate balance
  sheet as JSON or CSV and returns a structured, non-persisting
  `ValidationReport` checking schema, the data-origin policy, and the
  balance-sheet identity. New `balancelab.ingest` package; all issues are
  collected rather than failing on the first.
- Scenario/forecast domain schemas (`Assumption`, `Scenario`, `ForecastValue`,
  `ForecastRun`) — immutable, typed, with per-category growth-rate assumptions
  and a bounded horizon; equity may not be a growth target.
- Deterministic forecast engine (`balancelab.calc.forecast`, formulas
  `forecast-formulas@1`): projects assets/liabilities by growth rate and carries
  equity as a residual so the identity holds every period; emits full
  `CalculationNode` lineage.
- Scenario CRUD: `POST/GET/DELETE /v1/scenarios` and `GET /v1/scenarios`
  (paginated, newest first); creation validates the base portfolio exists.
  Per the immutability rule, there is no in-place update.
- Forecast routes: `POST /v1/forecasts`, `GET /v1/forecasts/{id}`, and
  `GET /v1/forecasts/{id}/lineage`.
- Storage: `ScenarioRepository` and `ForecastRepository` added to the unit of
  work (in-memory + SQLAlchemy), with ORM tables and Alembic migration `0002`.
- Forecast golden eval set (`evals/cases/golden_forecast.json`) with pinned
  per-period totals; the runner and smoke test now cover both case files.
- New `unsupported_media_type` (415) error code; validation-error details are
  sanitized to JSON-safe primitives.

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
