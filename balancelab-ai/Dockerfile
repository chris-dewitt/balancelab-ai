# syntax=docker/dockerfile:1

# Deterministic runtime image for the BalanceLab AI M0 service.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first for better layer caching. Copy only the metadata
# needed to resolve dependencies, then the source.
COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

# Run as an unprivileged user (least privilege).
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Liveness probe hits the framework-independent health endpoint.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"

CMD ["uvicorn", "balancelab.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
