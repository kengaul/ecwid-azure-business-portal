from __future__ import annotations

import azure.functions as func

from business_tools.featured import routes as featured_routes
from business_tools.frontpage import routes
from business_tools.shared.responses import json_response
from business_tools.vat import routes as vat_routes

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return json_response({"ok": True})


@app.route(route="frontpage/preview", methods=["POST"])
def frontpage_preview(req: func.HttpRequest) -> func.HttpResponse:
    return routes.preview(req)


@app.route(route="frontpage/apply", methods=["POST"])
def frontpage_apply(req: func.HttpRequest) -> func.HttpResponse:
    return routes.apply(req)


@app.route(route="vat/categories", methods=["GET"])
def vat_categories(req: func.HttpRequest) -> func.HttpResponse:
    return vat_routes.categories(req)


@app.route(route="vat/preview", methods=["POST"])
def vat_preview(req: func.HttpRequest) -> func.HttpResponse:
    return vat_routes.preview(req)


@app.route(route="vat/apply", methods=["POST"])
def vat_apply(req: func.HttpRequest) -> func.HttpResponse:
    return vat_routes.apply(req)


@app.route(route="featured/suppliers", methods=["GET"])
def featured_suppliers(req: func.HttpRequest) -> func.HttpResponse:
    return featured_routes.suppliers(req)


@app.route(route="featured/preview", methods=["POST"])
def featured_preview(req: func.HttpRequest) -> func.HttpResponse:
    return featured_routes.preview(req)


@app.route(route="featured/apply", methods=["POST"])
def featured_apply(req: func.HttpRequest) -> func.HttpResponse:
    return featured_routes.apply(req)
