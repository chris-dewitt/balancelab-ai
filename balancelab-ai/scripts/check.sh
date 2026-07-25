#!/usr/bin/env bash
# Run the full local check suite mirroring CI. Run from the project directory:
#   ./scripts/check.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> ruff format --check"
ruff format --check .

echo "==> ruff check"
ruff check .

echo "==> mypy"
mypy

echo "==> pytest"
pytest -q

echo "==> migration check"
python scripts/check_migrations.py

echo "==> bandit"
bandit -q -c pyproject.toml -r src

echo "==> pip-audit"
pip-audit --skip-editable --progress-spinner off

echo "==> evaluation smoke suite"
python -m evals.runner

echo "All checks passed."
