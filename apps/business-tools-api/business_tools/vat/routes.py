from __future__ import annotations

import logging

import azure.functions as func

from business_tools.ecwid.client import EcwidClient, EcwidClientError
from business_tools.shared.responses import error_response, json_response
from business_tools.shared.settings import load_settings
from business_tools.vat.models import to_jsonable
from business_tools.vat.service import apply_vat_plan, build_vat_plan, list_categories

logger = logging.getLogger(__name__)


def _client_from_settings() -> EcwidClient:
    settings = load_settings()
    return EcwidClient(settings.ecwid_api_token, settings.ecwid_shop_id)


def _category_id_from_request(req: func.HttpRequest) -> int | None:
    try:
        payload = req.get_json()
    except ValueError:
        payload = {}
    raw_category_id = payload.get("categoryId") if isinstance(payload, dict) else None
    try:
        return int(raw_category_id)
    except (TypeError, ValueError):
        return None


def categories(req: func.HttpRequest) -> func.HttpResponse:
    try:
        client = _client_from_settings()
        return json_response({"ok": True, "categories": to_jsonable(list_categories(client))})
    except (RuntimeError, EcwidClientError) as exc:
        logger.exception("Unable to list VAT categories.")
        return error_response(str(exc), status_code=500)


def preview(req: func.HttpRequest) -> func.HttpResponse:
    category_id = _category_id_from_request(req)
    if category_id is None:
        return error_response("Select a valid category.", status_code=400)

    try:
        client = _client_from_settings()
        plan = build_vat_plan(category_id, client=client)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except (RuntimeError, EcwidClientError) as exc:
        logger.exception("Unable to build VAT preview.")
        return error_response(str(exc), status_code=500)

    return json_response(
        {
            "ok": True,
            "canApply": len(plan.products_to_update) > 0,
            "plan": to_jsonable(plan),
        }
    )


def apply(req: func.HttpRequest) -> func.HttpResponse:
    category_id = _category_id_from_request(req)
    if category_id is None:
        return error_response("Select a valid category.", status_code=400)

    try:
        client = _client_from_settings()
        plan = build_vat_plan(category_id, client=client)
        if not plan.products_to_update:
            return error_response(
                "All products in this category are already zero-rated.",
                status_code=400,
                plan=to_jsonable(plan),
            )
        result = apply_vat_plan(plan, client=client)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except (RuntimeError, EcwidClientError) as exc:
        logger.exception("Unable to apply VAT update.")
        return error_response(str(exc), status_code=500)

    return json_response(
        {"ok": not result.partial_failure, "result": to_jsonable(result)},
        status_code=207 if result.partial_failure else 200,
    )
