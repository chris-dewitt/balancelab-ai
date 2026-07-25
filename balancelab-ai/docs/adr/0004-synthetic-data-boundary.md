# 4. Synthetic-data-only boundary

- Status: Accepted
- Date: 2026-07-25

## Context

The MVP must use only synthetic or explicitly public data, must never ingest
confidential data, and must never claim a synthetic demo represents a real
institution (`SPEC.md` §4, §9, §15). We need a single, testable enforcement point
rather than scattered ad-hoc checks.

## Decision

1. A `synthetic_data_only` policy flag (default **on**) is part of typed config.
2. Every `Portfolio` carries `Provenance` with a `DataOrigin`
   (`synthetic` / `public` / `uploaded`). The synthetic generator always labels
   its output `synthetic` and records the generator version and seed.
3. `balancelab.synthetic.ensure_synthetic` is the single boundary: while the
   policy is on, it rejects any portfolio not labeled synthetic with a
   `PolicyViolationError`. API write paths call it before computation.
4. `uploaded` origin is defined for the future upload path but is rejected while
   the policy is on.

## Consequences

- The guarantee is enforced in one place and covered by tests
  (`tests/test_synthetic_generator.py`).
- Relaxing the policy (e.g. to admit vetted public data in a later milestone) is
  a deliberate, visible configuration change plus new validation, not a silent
  code path.
- Provenance fields required by the spec for source-derived data
  (`source_uri`, `retrieved_at`, `content_checksum`, `license_notes`) already
  exist on the model, ready for that milestone.
