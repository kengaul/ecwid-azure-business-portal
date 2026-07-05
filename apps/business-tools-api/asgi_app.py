from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from business_tools.ecwid.client import EcwidClient, EcwidClientError
from business_tools.featured.models import to_jsonable as featured_to_jsonable
from business_tools.featured.service import apply_featured_plan, build_featured_plan, list_suppliers
from business_tools.frontpage.models import to_jsonable as frontpage_to_jsonable
from business_tools.frontpage.service import apply_frontpage_plan, build_frontpage_plan
from business_tools.shared.settings import Settings, load_settings
from business_tools.vat.models import to_jsonable as vat_to_jsonable
from business_tools.vat.service import apply_vat_plan, build_vat_plan, list_categories

logger = logging.getLogger(__name__)

app = FastAPI(title="Business Tools API", version="0.1.0")

cors_origins = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "").split(",") if origin.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )


def _client_and_settings() -> tuple[EcwidClient, Settings]:
    settings = load_settings()
    return EcwidClient(settings.ecwid_api_token, settings.ecwid_shop_id), settings


def _selected_product_ids(payload: dict[str, Any]) -> set[int] | None:
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


def _server_error(exc: Exception) -> HTTPException:
    logger.exception("Business Tools API request failed.")
    return HTTPException(status_code=500, detail=str(exc))


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/frontpage/preview")
def frontpage_preview(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        client, settings = _client_and_settings()
        plan = build_frontpage_plan(payload.get("skus", ""), client=client, max_skus=settings.max_skus)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (RuntimeError, EcwidClientError) as exc:
        raise _server_error(exc) from exc

    return {"ok": True, "canApply": len(plan.valid_skus) > 0, "plan": frontpage_to_jsonable(plan)}


@app.post("/api/frontpage/apply")
def frontpage_apply(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        client, settings = _client_and_settings()
        plan = build_frontpage_plan(payload.get("skus", ""), client=client, max_skus=settings.max_skus)
        if not plan.valid_skus:
            raise HTTPException(
                status_code=400,
                detail="No valid SKUs were found. Nothing was changed.",
            )
        result = apply_frontpage_plan(plan, client=client)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (RuntimeError, EcwidClientError) as exc:
        raise _server_error(exc) from exc

    return {"ok": not result.partial_failure, "result": frontpage_to_jsonable(result)}


@app.get("/api/vat/categories")
def vat_categories() -> dict[str, Any]:
    try:
        client, _settings = _client_and_settings()
        categories = list_categories(client)
    except (RuntimeError, EcwidClientError) as exc:
        raise _server_error(exc) from exc

    return {"ok": True, "categories": vat_to_jsonable(categories)}


@app.post("/api/vat/preview")
def vat_preview(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        client, _settings = _client_and_settings()
        category_id = int(payload.get("categoryId"))
        selected_product_ids = _selected_product_ids(payload)
        plan = build_vat_plan(category_id, client=client, selected_product_ids=selected_product_ids)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (RuntimeError, EcwidClientError) as exc:
        raise _server_error(exc) from exc

    return {"ok": True, "canApply": len(plan.products_to_update) > 0, "plan": vat_to_jsonable(plan)}


@app.post("/api/vat/apply")
def vat_apply(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        client, _settings = _client_and_settings()
        category_id = int(payload.get("categoryId"))
        selected_product_ids = _selected_product_ids(payload)
        plan = build_vat_plan(category_id, client=client, selected_product_ids=selected_product_ids)
        if not plan.products_to_update:
            raise HTTPException(status_code=400, detail="No selected products need updating.")
        result = apply_vat_plan(plan, client=client)
    except HTTPException:
        raise
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (RuntimeError, EcwidClientError) as exc:
        raise _server_error(exc) from exc

    return {"ok": not result.partial_failure, "result": vat_to_jsonable(result)}


@app.get("/api/featured/suppliers")
def featured_suppliers() -> dict[str, Any]:
    try:
        client, _settings = _client_and_settings()
        suppliers = list_suppliers(client)
    except (RuntimeError, EcwidClientError) as exc:
        raise _server_error(exc) from exc

    return {
        "ok": True,
        "supplierAttributeName": "Supplier",
        "suppliers": featured_to_jsonable(suppliers),
    }


@app.post("/api/featured/preview")
def featured_preview(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        client, settings = _client_and_settings()
        plan = build_featured_plan(
            supplier=str(payload.get("supplier", "")).strip(),
            client=client,
            featured_category_name=settings.featured_products_category_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (RuntimeError, EcwidClientError) as exc:
        raise _server_error(exc) from exc

    return {"ok": True, "canApply": True, "plan": featured_to_jsonable(plan)}


@app.post("/api/featured/apply")
def featured_apply(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        selected_product_ids = _selected_product_ids(payload)
        client, settings = _client_and_settings()
        plan = build_featured_plan(
            supplier=str(payload.get("supplier", "")).strip(),
            client=client,
            featured_category_name=settings.featured_products_category_name,
            selected_product_ids=selected_product_ids,
        )
        result = apply_featured_plan(plan, client=client)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (RuntimeError, EcwidClientError) as exc:
        raise _server_error(exc) from exc

    return {"ok": not result.partial_failure, "result": featured_to_jsonable(result)}
