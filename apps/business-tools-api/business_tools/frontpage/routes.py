from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func

from business_tools.ecwid.client import EcwidClient, EcwidClientError
from business_tools.frontpage.models import to_jsonable
from business_tools.frontpage.service import apply_frontpage_plan, build_frontpage_plan
from business_tools.shared.responses import error_response, json_response
from business_tools.shared.settings import load_settings

logger = logging.getLogger(__name__)


def _request_payload(req: func.HttpRequest) -> dict[str, Any]:
    try:
        body = req.get_json()
    except ValueError:
        body = {}
    return body if isinstance(body, dict) else {}


def _client_from_settings() -> tuple[EcwidClient, int]:
    settings = load_settings()
    return EcwidClient(settings.ecwid_api_token, settings.ecwid_shop_id), settings.max_skus


def preview(req: func.HttpRequest) -> func.HttpResponse:
    payload = _request_payload(req)
    raw_skus = payload.get("skus", "")

    try:
        client, max_skus = _client_from_settings()
        plan = build_frontpage_plan(raw_skus, client=client, max_skus=max_skus)
    except (RuntimeError, EcwidClientError) as exc:
        logger.exception("Unable to build frontpage preview.")
        return error_response(str(exc), status_code=500)

    can_apply = len(plan.valid_skus) > 0
    return json_response({"ok": True, "canApply": can_apply, "plan": to_jsonable(plan)})


def apply(req: func.HttpRequest) -> func.HttpResponse:
    payload = _request_payload(req)
    raw_skus = payload.get("skus", "")

    try:
        client, max_skus = _client_from_settings()
        plan = build_frontpage_plan(raw_skus, client=client, max_skus=max_skus)
        if not plan.valid_skus:
            return error_response(
                "No valid SKUs were found. Nothing was changed.",
                status_code=400,
                plan=to_jsonable(plan),
            )
        result = apply_frontpage_plan(plan, client=client)
    except (RuntimeError, EcwidClientError) as exc:
        logger.exception("Unable to apply frontpage update.")
        return error_response(str(exc), status_code=500)

    status_code = 207 if result.partial_failure else 200
    return json_response({"ok": not result.partial_failure, "result": to_jsonable(result)}, status_code)
