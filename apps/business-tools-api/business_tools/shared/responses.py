from __future__ import annotations

import json
from typing import Any

import azure.functions as func


def json_response(payload: dict[str, Any], status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(payload, default=str),
        status_code=status_code,
        mimetype="application/json",
    )


def error_response(message: str, status_code: int = 400, **details: Any) -> func.HttpResponse:
    payload: dict[str, Any] = {"ok": False, "error": message}
    payload.update(details)
    return json_response(payload, status_code=status_code)
