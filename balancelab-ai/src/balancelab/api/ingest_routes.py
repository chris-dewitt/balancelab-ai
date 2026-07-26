"""Upload validation route.

``POST /v1/portfolios/validate`` accepts an uploaded balance sheet and returns a
structured :class:`~balancelab.ingest.validation.ValidationReport`. It is a dry
run: nothing is persisted. Two content types are supported:

* ``application/json`` — a full candidate object (name, currency, as_of_date,
  origin, accounts[...]).
* ``text/csv`` — account rows (``name,category,currency,balance`` header); the
  portfolio metadata (name, currency, as_of_date, origin) is supplied as query
  parameters.

Malformed JSON returns a structured 422; an unsupported content type returns 415;
an oversized body returns 413-style structured error. An upload that parses but
fails schema/policy/reconciliation returns 200 with ``valid: false`` and issues.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request

from balancelab.errors import UnsupportedMediaTypeError, ValidationError
from balancelab.ingest import ValidationReport, parse_csv_accounts, validate_upload

router = APIRouter(prefix="/v1", tags=["balancelab"])

# 2 MiB cap on validation uploads.
_MAX_BODY_BYTES = 2 * 1024 * 1024


async def _read_bounded_body(request: Request) -> bytes:
    body = await request.body()
    if len(body) > _MAX_BODY_BYTES:
        raise ValidationError(
            "upload too large",
            details={"max_bytes": _MAX_BODY_BYTES, "received_bytes": len(body)},
        )
    return body


@router.post("/portfolios/validate", response_model=ValidationReport)
async def validate_portfolio_upload(request: Request) -> ValidationReport:
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    body = await _read_bounded_body(request)

    if content_type == "application/json":
        try:
            raw: Any = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            raise ValidationError(
                "request body is not valid JSON", details={"error": str(exc)}
            ) from exc
        if not isinstance(raw, dict):
            raise ValidationError("JSON body must be an object")
        return validate_upload(raw)

    if content_type == "text/csv":
        try:
            accounts = parse_csv_accounts(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValidationError("invalid CSV upload", details={"error": str(exc)}) from exc
        params = request.query_params
        raw = {
            "name": params.get("name", "Uploaded Portfolio"),
            "currency": params.get("currency", "USD"),
            "as_of_date": params.get("as_of_date"),
            "origin": params.get("origin", "uploaded"),
            "source_uri": params.get("source_uri"),
            "accounts": accounts,
        }
        return validate_upload(raw)

    raise UnsupportedMediaTypeError(
        "unsupported content type; use application/json or text/csv",
        details={"content_type": content_type or "(none)"},
    )
