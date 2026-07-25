# Examples

## `demo.py` — M0 deterministic trace

Runs the full M0 path (synthetic portfolio → snapshot → lineage) with no server
and no model calls, and prints a trace where every total resolves to a formula,
its inputs, a unit, and a formula version.

```bash
python examples/demo.py          # default seed 2025
python examples/demo.py 7        # any non-negative seed is reproducible
```

For the HTTP equivalent, run the service (`uvicorn balancelab.api.app:app`) and
`POST /v1/portfolios/synthetic` then `POST /v1/snapshots`; see the root
[`README.md`](../README.md).
