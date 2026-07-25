# 5. Deferred scope after M0

- Status: Accepted
- Date: 2026-07-25

## Context

`AGENTS.md` requires that deferred scope become tracked decisions/issues rather
than hidden TODOs, and that we not build beyond the active milestone. M0's charter
is "synthetic data boundary, schemas, formulas, CI" (`SPEC.md` §13). This ADR
records what is intentionally *not* built yet and where it lands.

## Decision

The following are deferred to later milestones and must not be assumed present:

| Deferred capability | Target milestone |
| ------------------- | ---------------- |
| Persistence (Postgres) + migrations; real `scripts/check_migrations.py` | M1 |
| Upload validation for portfolios; broader domain calcs (income, liquidity, risk) | M1 |
| Scenario/Assumption/Curve/MacroPath schemas + scenario CRUD | M1 |
| Lineage graph persistence, reconciliations, exports, golden report tests | M2 |
| Natural-language scenario drafting + human approval workflow + audit events | M3 |
| Methodology retrieval (RAG), faithful explanations, anomaly detection | M4 |
| ML forecast comparison, model registry, evaluation report, signature demo | M5 |
| AuthN/AuthZ, scoped policy decisions for external writes | M3+ |
| Terraform/Azure deployment infrastructure | Deployment phase |
| OpenTelemetry traces (M0 ships structured logs + correlation IDs only) | M1+ |

## Consequences

- Reviewers can see the boundary of M0 at a glance and hold changes to it.
- Each deferred item carries a milestone; when work begins, it should get a
  tracked issue and, where it involves a significant decision, its own ADR.
- Placeholders that exist today (e.g. `scripts/check_migrations.py`, the Compose
  `db` service, unused `Provenance` source fields) are explicitly wired for their
  target milestone and documented as no-ops until then.
