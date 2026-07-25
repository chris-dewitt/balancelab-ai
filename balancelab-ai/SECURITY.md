# Security

This document is the M0 threat model and security baseline for BalanceLab AI. It
follows [`docs/SHARED_ENGINEERING_STANDARD.md`](docs/SHARED_ENGINEERING_STANDARD.md)
§7 and will grow as later milestones add persistence, model providers, retrieval,
and external writes.

## Assets

- Integrity of authoritative figures (totals, reconciliations) and their lineage.
- Availability of the API.
- The synthetic-data-only guarantee (no real or confidential data enters the
  system in the MVP).
- Configuration and (future) secrets.

## Trust boundaries

| Boundary | M0 state |
| -------- | -------- |
| Client → API | Untrusted input; validated by Pydantic schemas with `extra="forbid"`. |
| API → domain core | Typed, in-process; the core assumes already-validated models. |
| Synthetic-data boundary | `synthetic.ensure_synthetic` rejects non-synthetic portfolios while the policy is in force. |
| Model output → system | **No models in M0.** When added, output is untrusted: parsed, validated, never used for arithmetic/authorization. |
| System → external writes | **None in M0.** When added, gated by explicit approval + audit event. |

## Attackers & abuse cases

- **Malformed / oversized / injection-style payloads** → rejected at the schema
  boundary; unknown fields are forbidden; string lengths are bounded.
- **Log injection via headers** → inbound `X-Correlation-ID` is length-bounded
  (128 chars) before use.
- **Attempt to submit real/uploaded data** → `DataOrigin.UPLOADED` is rejected by
  the synthetic-only policy; only `SYNTHETIC` (and, when policy is relaxed,
  `PUBLIC`) origins are accepted.
- **Tampered figures** → the reconciliation invariant (`assets == liabilities +
  equity` within tolerance) fails closed with a `reconciliation_failed` error;
  every number is independently traceable via lineage.
- **(Future) prompt injection via retrieved content** → retrieved text will be
  treated as data, never instructions; not applicable in M0.

## Mitigations in place (M0)

- **Input validation:** typed Pydantic v2 schemas, forbidden extras, bounded
  string lengths, currency allow-list, non-negative seed.
- **Deterministic core:** models cannot compute or override figures (they are not
  present); arithmetic uses `Decimal`.
- **Least privilege:** the runtime container runs as a non-root user; no external
  network calls or writes are performed.
- **Secret hygiene:** configuration is loaded from environment variables; no
  secrets are committed. `.env` is git-ignored. CI runs `pip-audit`
  (dependency vulnerabilities) and `bandit` (static analysis).
- **Redaction:** the structured JSON logger redacts common sensitive keys
  (`password`, `secret`, `token`, `authorization`, `api_key`).
- **Correlation & auditability:** every request/response carries a correlation
  ID for traceability. Immutable audit events for approvals/consequential actions
  arrive with the approval workflow (M3).

## Out of scope for M0 (tracked for later milestones)

- AuthN/AuthZ and scoped policy decisions for external writes.
- Persistence-layer security (row-level access, encryption at rest).
- Model/provider key management and provider-side data handling.
- Full audit-event store and replay.

## Reporting

Until a formal policy is published, report suspected vulnerabilities privately to
the repository owner rather than opening a public issue. Do not include real or
confidential data in any report; this project uses synthetic data only.
