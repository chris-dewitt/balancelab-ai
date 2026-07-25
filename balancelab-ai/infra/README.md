# Infrastructure

Deployment and persistence infrastructure for BalanceLab AI.

**M0 status:** intentionally minimal. Local dependencies are provided by
[`docker-compose.yml`](../docker-compose.yml) at the project root; the runtime
image is defined by [`Dockerfile`](../Dockerfile).

Planned (deferred to later milestones, tracked in `docs/adr` and `CHANGELOG.md`):

- `migrations/` — database migrations (introduced with the persistence layer in M1).
- Terraform modules for the Azure deployment target (providers remain replaceable
  per the shared engineering standard).

Nothing here provisions cloud resources yet, and no secrets are stored in this
directory.
