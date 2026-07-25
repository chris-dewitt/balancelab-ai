# 2. Adopt the shared standard stack

- Status: Accepted
- Date: 2026-07-25

## Context

`docs/SHARED_ENGINEERING_STANDARD.md` §3 prescribes a default stack for all
portfolio repositories. BalanceLab AI should reuse it unless there is a
documented reason not to.

## Decision

M0 adopts the standard stack as-is: Python 3.12, FastAPI, Pydantic v2, and
pytest, with ruff (format + lint), mypy (strict), bandit, and pip-audit in CI,
and Docker/Docker Compose for local dependencies. PostgreSQL (pgvector image) is
declared in Compose for the upcoming persistence milestone but not yet used by
code. Packaging uses Hatchling with a `src/` layout.

No deviations from the standard stack are made in M0.

## Consequences

- Consistency with the rest of the portfolio; reviewers can navigate quickly.
- `src/` layout keeps import paths honest (tests run against the installed
  package, not the working tree).
- Any future deviation (e.g. an alternative web framework or DB) requires its own
  ADR.
- Terraform/Azure deployment targets from the standard are deferred until there
  is something to deploy; see ADR 0005.
