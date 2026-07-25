# AI Engineer Portfolio Master Roadmap

## Portfolio thesis

The portfolio demonstrates a coherent applied-AI platform:

- **EvalForge** proves the systems can be measured.
- **Atlas** proves evidence-grounded, data-intensive AI engineering.
- **Atticus** proves safe tool-using agents and human oversight.
- **FedLens** proves rigorous NLP, temporal comparison, and econometric analysis.
- **BalanceLab AI** proves deterministic financial computation with explainable AI.

## Recommended sequence

### Phase 0 â€” Shared foundation

Create reusable conventions for configuration, provider interfaces, tracing, structured errors, audit events, evaluation case formats, CI, and Docker development. Reuse patterns, not a prematurely coupled monorepo.

Exit: reference service passes lint, typing, tests, migration checks, telemetry smoke test, and container build.

### Phase 1 â€” EvalForge

Build datasets, runners, deterministic graders, trace ingestion, comparisons, and CI reporting before complex agents.

Exit: a pull request can compare baseline and candidate runs and fail on a configured regression.

### Phase 2 â€” Atlas

Build public-source ingestion, point-in-time storage, hybrid retrieval, citation validation, quantitative tools, and a research workflow.

Exit: the inflation-outlook demo produces a reproducible, cited report with contrary evidence and measured retrieval quality.

### Phase 3 â€” Atticus

Build a local-first agent around the shared evaluation and telemetry patterns. Prioritize policy enforcement, approval, replay, and auditability over breadth of tools.

Exit: the research-to-GitHub-issue demo pauses before publication and can be replayed from its trace.

### Phase 4 â€” FedLens

Specialize ingestion and analysis for Federal Reserve communications, semantic diffs, tone models, and event studies.

Exit: a user can compare two document vintages and reproduce the linked market-reaction analysis.

### Phase 5 â€” BalanceLab AI

Build a synthetic balance-sheet engine, scenario schemas, deterministic forecasts, natural-language scenario construction, and evidence-linked explanations.

Exit: every displayed figure traces to a calculation, inputs, versioned assumptions, and a reproducible run.

### Phase 6 â€” Publication

Publish case studies, technical articles, three-minute demos, architecture diagrams, and honest benchmark tables. The site should lead with outcomes and measured reliability rather than technology logos.

## Cross-project gates

Each phase requires: threat model, evaluation plan, representative fixtures, CI, telemetry, cost/latency measurement, demo script, known limitations, and an issue backlog for deferred scope.

## Suggested articles

1. Why AI Agents Need Regression Tests
2. Designing Human Approval into Tool-Using Agents
3. Evaluating RAG Beyond Cosine Similarity
4. Building Point-in-Time Retrieval for Economic Research
5. When an LLM Should Call Python Instead of Calculating
6. Threat Modeling a Local AI Assistant
7. Measuring Model-Routing Cost, Latency, and Reliability
8. What Quantitative Model Governance Can Teach AI Engineers