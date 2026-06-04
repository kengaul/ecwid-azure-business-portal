from __future__ import annotations

import logging

import azure.functions as func

from business_tools.ecwid.client import EcwidClient, EcwidClientError
from business_tools.featured.models import to_jsonable
from business_tools.featured.service import apply_featured_plan, build_featured_plan, list_suppliers
from business_tools.shared.responses import error_response, json_response
from business_tools.shared.settings import Settings, load_settings

logger = logging.getLogger(__name__)


def _client_and_settings() -> tuple[EcwidClient, Settings]:
    settings = load_settings()
    return EcwidClient(settings.ecwid_api_token, settings.ecwid_shop_id), settings


def _request_payload(req: func.HttpRequest) -> dict:
    try:
        payload = req.get_json()
    except ValueError:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def _selected_product_ids(payload: dict) -> set[int] | None:
    if "productIds" not in payload:
        return None
    product_ids = payload.get("productIds")
    if not isinstance(product_ids, list):
        raise ValueError("Product selection must be a list.")

    selected: set[int] = set()
    for product_id in product_ids:
        try:
            selected.add(int(product_id))
        except (TypeError, ValueError):
            raise ValueError("Product selection contains an invalid product ID.") from None
    return selected


def suppliers(req: func.HttpRequest) -> func.HttpResponse:
    try:
        client, settings = _client_and_settings()
        return json_response(
            {
                "ok": True,
                "supplierAttributeName": settings.supplier_attribute_name,
                "suppliers": to_jsonable(list_suppliers(client, settings.supplier_attribute_name)),
            }
        )
    except (RuntimeError, EcwidClientError) as exc:
        logger.exception("Unable to list suppliers.")
        return error_response(str(exc), status_code=500)


def preview(req: func.HttpRequest) -> func.HttpResponse:
    payload = _request_payload(req)
    supplier = str(payload.get("supplier", "")).strip()

    try:
        client, settings = _client_and_settings()
        plan = build_featured_plan(
            supplier=supplier,
            client=client,
            supplier_attribute_name=settings.supplier_attribute_name,
            featured_category_name=settings.featured_products_category_name,
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except (RuntimeError, EcwidClientError) as exc:
        logger.exception("Unable to build featured products preview.")
        return error_response(str(exc), status_code=500)

    return json_response({"ok": True, "canApply": True, "plan": to_jsonable(plan)})


def apply(req: func.HttpRequest) -> func.HttpResponse:
    payload = _request_payload(req)
    supplier = str(payload.get("supplier", "")).strip()

    try:
        selected_product_ids = _selected_product_ids(payload)
        client, settings = _client_and_settings()
        plan = build_featured_plan(
            supplier=supplier,
            client=client,
            supplier_attribute_name=settings.supplier_attribute_name,
            featured_category_name=settings.featured_products_category_name,
            selected_product_ids=selected_product_ids,
        )
        result = apply_featured_plan(plan, client=client)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except (RuntimeError, EcwidClientError) as exc:
        logger.exception("Unable to apply featured products update.")
        return error_response(str(exc), status_code=500)

    return json_response(
        {"ok": not result.partial_failure, "result": to_jsonable(result)},
        status_code=207 if result.partial_failure else 200,
    )
