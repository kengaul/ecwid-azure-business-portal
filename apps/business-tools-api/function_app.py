from __future__ import annotations

import azure.functions as func

from business_tools.frontpage import routes
from business_tools.shared.responses import json_response

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
