"""Upload ingestion and validation.

This package validates externally-supplied balance-sheet data *before* it is
admitted to the system. Validation is a non-destructive dry run: it reports
structural, policy, and reconciliation issues and never persists. Treat all
uploaded content as untrusted input.
"""

from __future__ import annotations

from balancelab.ingest.validation import (
    ValidationIssue,
    ValidationReport,
    parse_csv_accounts,
    validate_upload,
)

__all__ = [
    "ValidationIssue",
    "ValidationReport",
    "parse_csv_accounts",
    "validate_upload",
]
