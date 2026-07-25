# BalanceLab AI â€” Synthetic Balance-Sheet Forecasting and Scenario Copilot

Status: Repository source of truth  
Version: 1.0  
Audience: maintainers, coding agents, reviewers, and portfolio visitors

## 1. Product vision

A safe enterprise-style application that turns natural-language scenarios into validated assumptions, runs deterministic balance-sheet forecasts, and explains results with complete calculation lineage.

## 2. Target users

Finance and risk practitioners, model-governance teams, students, and reviewers; all demos use synthetic or explicitly public data.

## 3. Product principles

- Evidence and traceability before fluency
- Deterministic computation for authoritative results
- Least privilege and explicit approval for consequential actions
- Bounded, inspectable workflows rather than opaque autonomous loops
- Reproducible runs, versioned inputs, and measurable quality
- Public, synthetic, or properly licensed data only

## 4. MVP scope

### In scope

- Synthetic balance-sheet templates and validated uploads
- Versioned economic/rate scenarios and assumptions
- Deterministic balance, income, liquidity, and risk calculations
- Natural-language scenario builder producing a typed draft
- Human review before executing material scenario changes
- Methodology retrieval and evidence-linked explanations
- Deterministic versus ML forecast comparison
- Anomaly detection, model documentation, and scenario comparison

### Explicitly out of scope

- Production bank data
- Regulatory reporting or investment advice
- LLM-authored authoritative figures
- Opaque model overrides
- Claims that synthetic demonstrations represent a real institution

## 5. System architecture

`	ext
Client / CLI
     |
Typed API and identity boundary
     |
Application workflow / state machine
     |
+----------------+----------------+----------------+
| Domain services| AI adapters    | Policy/eval    |
+----------------+----------------+----------------+
     |                 |                 |
Postgres/artifacts  Model providers  Traces/metrics
`

### Major components

- Upload/schema validation and synthetic data generator
- Scenario editor, assumption registry, and approval workflow
- Deterministic calculation engine with versioned formulas
- Optional ML forecasting adapter and model registry
- Calculation-lineage and reconciliation service
- Methodology retrieval and explanation generator
- Dashboard, comparison views, exports, and evaluation adapter

Domain code must remain independent of FastAPI, provider SDKs, and deployment infrastructure. All long-running workflows persist checkpoints and expose cancellation and terminal failure.

## 6. Core data model

- Portfolio, Account, Instrument, CashFlow, Snapshot
- Scenario, Assumption, Curve, MacroPath, Approval
- ModelVersion, ForecastRun, ForecastValue, CalculationNode
- Explanation, EvidenceItem, Reconciliation, Anomaly, AuditEvent

All entities use stable identifiers and timestamps. Versioned records are immutable; corrections create a new version. Source-derived records retain source URI, retrieval time, content checksum, license/usage notes, and parser version.

## 7. API contract

Initial resource families:

- POST /v1/portfolios/validate and /synthetic
- CRUD /v1/scenarios; POST /v1/scenarios/from-language
- POST /v1/forecasts; GET /v1/forecasts/{id}
- GET /v1/forecasts/{id}/lineage and /reconciliation
- POST /v1/comparisons; GET /v1/methodology/search

APIs use versioned routes, Pydantic request/response schemas, idempotency keys for mutating operations, pagination for collections, and structured errors containing code, message, correlation ID, and safe details.

## 8. AI and workflow design

The workflow is an explicit state machine: validate request, assemble context, plan bounded work, execute typed operations, verify outputs, request approval when required, and finalize artifacts. Each transition is traceable. Model output is parsed against schemas and may not alter permissions, bypass deterministic validation, or invent unavailable evidence.

Provider adapters expose capabilities, context limits, structured-output support, usage, latency, and normalized failure modes. Fallback is allowed only by configured policy and is recorded in the run.

## 9. Security and privacy

- Classify inputs, outputs, tools, and stored artifacts by sensitivity.
- Keep secrets in an external secret mechanism and redact telemetry.
- Reject unsupported file types, unsafe paths, private-network URLs, and oversized payloads.
- Treat retrieved content as data, not instructions.
- Require an authenticated, scoped policy decision before external writes.
- Store approval actor, decision, exact action digest, expiry, and execution result.
- Document retention/deletion behavior and provide fixture data containing no confidential information.

## 10. Evaluation plan

Primary metrics:

- Schema-validation and assumption-extraction accuracy
- Forecast reconciliation, invariants, and numerical reproducibility
- Explanation faithfulness to calculation lineage
- Anomaly precision/recall on seeded synthetic cases
- Approval compliance, latency, and run cost

Maintain a versioned golden set plus adversarial, malformed, timeout, empty-result, contradictory-evidence, and dependency-failure cases. Report per-case outputs as well as aggregates. CI runs a deterministic smoke suite; scheduled evaluation runs cover models and external integrations.

## 11. Testing strategy

- Unit tests for domain rules, validation, policies, and calculations
- Contract tests for providers, tools, stores, and source adapters
- Integration tests against disposable Postgres/Redis/object storage
- Golden tests for stable transformations and reports
- End-to-end tests for the signature workflow
- Security tests for injection, authorization, path/URL handling, redaction, and replay
- Property tests for invariants and numerical or temporal boundaries where applicable

## 12. Observability and operations

Emit structured logs, distributed traces, and metrics keyed by correlation and run IDs. Track state-transition duration, dependency errors, retries, model and token usage, cost, evaluation scores, and project-specific quality. Jobs use bounded exponential backoff, dead-letter/quarantine behavior, and operator-visible recovery instructions.

## 13. Milestones

- M0: synthetic data boundary, schemas, formulas, CI
- M1: upload validation, scenario CRUD, deterministic forecast core
- M2: lineage graph, reconciliations, exports, golden tests
- M3: natural-language scenario drafts and approval workflow
- M4: methodology RAG, faithful explanations, anomaly detection
- M5: ML comparison, model documentation, evaluation report, signature demo

Each milestone must ship a demonstrable vertical slice with tests, evaluation cases, telemetry, and documentation. Deferred scope becomes tracked issues rather than hidden TODOs.

## 14. Signature demonstration

Upload a synthetic balance sheet, draft a rate-shock scenario in natural language, approve normalized assumptions, run forecasts, compare scenarios, and trace every explanation to calculations and methodology.

The demo must run from documented commands with public or synthetic fixtures, show a trace and quality report, and complete in approximately three minutes after setup.

## 15. MVP acceptance criteria

- All portfolio examples are synthetic or clearly licensed public data
- Every displayed number resolves to formula, inputs, units, assumptions, and code/model version
- Natural-language input creates a draft and never silently executes a changed scenario
- Golden-case totals reconcile within documented tolerances
- Explanations cannot introduce figures absent from calculation results
- The signature demo exports inputs, approvals, results, lineage, evidence, and audit history

Additionally, all applicable requirements in docs/SHARED_ENGINEERING_STANDARD.md must pass.

## 16. Repository layout

`	ext
README.md
SPEC.md
AGENTS.md
ARCHITECTURE.md
SECURITY.md
EVALUATION.md
MODEL_CARD.md
DATA_CARD.md
CHANGELOG.md
docs/adr/
src/
tests/
evals/
examples/
scripts/
infra/
`

## 17. Initial agent work order

1. Verify repository identity and read all source-of-truth documents.
2. Create the smallest M0 skeleton using the shared standard.
3. Add typed configuration, health/readiness endpoints, structured errors, correlation IDs, and telemetry.
4. Define domain schemas and interfaces before external integrations.
5. Add CI for formatting, linting, typing, tests, security, and container build.
6. Implement one representative end-to-end fixture.
7. Record assumptions and deferred decisions in ADRs and issues.

Do not begin later milestones until M0 acceptance evidence is recorded.