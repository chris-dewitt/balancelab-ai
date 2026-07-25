# 1. Record architecture decisions

- Status: Accepted
- Date: 2026-07-25

## Context

`AGENTS.md` requires recording meaningful architectural decisions in
`docs/adr/`. We need a lightweight, consistent format so decisions are
discoverable and their rationale survives.

## Decision

We use Architecture Decision Records (ADRs), one Markdown file per decision,
numbered sequentially (`NNNN-title.md`). Each ADR states status, date, context,
decision, and consequences. We follow Michael Nygard's lightweight ADR style.

## Consequences

- Decisions and their rationale are versioned alongside the code.
- Superseded decisions are kept for history and marked as such rather than
  deleted.
- New significant decisions add a new ADR instead of editing old ones.
