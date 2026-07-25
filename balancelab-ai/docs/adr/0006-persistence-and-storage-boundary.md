# 6. Persistence and the storage boundary

- Status: Accepted
- Date: 2026-07-25

## Context

M1 introduces persistence (deferred in M0, see ADR 0005). The domain and API
layers must not become coupled to a database, and the service must remain
runnable and testable without one. The shared standard mandates PostgreSQL,
migrations, and integration tests against a disposable database.

## Decision

1. **A storage boundary of typed Protocols.** `PortfolioRepository`,
   `SnapshotRepository`, and a `UnitOfWork` (in `balancelab.storage.interfaces`)
   speak domain models, never ORM rows. The rest of the app depends only on these
   Protocols and a `UnitOfWorkFactory` callable.
2. **Two interchangeable backends.** An in-memory backend (tests, DB-less runs)
   and a SQLAlchemy 2.0 / Postgres backend. `create_unit_of_work_factory` selects
   Postgres when `database_url` is configured, otherwise in-memory. The same
   contract tests run against both.
3. **JSONB + typed scalar columns.** Each table stores the full domain object as
   JSONB (the authoritative source, reconstructed via Pydantic validation) plus a
   few indexed scalar columns for querying. This keeps the schema stable as
   domain models evolve while preserving queryability.
4. **Alembic migrations** live under `infra/migrations`. The migration check runs
   an offline SQL smoke always, and `upgrade head` + `alembic check` (drift
   detection) when a database is configured; CI runs the online path against a
   disposable Postgres.
5. **Idempotent writes by id.** `add` is a no-op when the id already exists,
   returning the stored record, so retried mutations do not duplicate data.
6. **psycopg pinned to the 3.2 line.** psycopg 3.3 returns the server version as
   bytes, which SQLAlchemy 2.0's psycopg dialect cannot parse; pinned until
   resolved upstream.

## Consequences

- Domain/API code is backend-agnostic; unit tests stay fast on the in-memory
  backend while integration tests validate the real Postgres path.
- Reconstruction through Pydantic means a row that cannot form a valid domain
  model fails loudly rather than yielding a malformed object.
- The JSONB approach trades some relational normalization for schema stability;
  when query patterns demand it, columns or child tables can be promoted in a
  later migration.
- Multi-currency consolidation, richer domain calculations, and scenario/forecast
  entities remain deferred (ADR 0005); this ADR covers persistence of the
  existing M0 domain objects only.
