from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from business_tools.ecwid.client import EcwidClient, EcwidClientError
from business_tools.frontpage.models import to_jsonable
from business_tools.frontpage.service import apply_frontpage_plan, build_frontpage_plan
from business_tools.shared.settings import load_settings


def load_local_settings() -> None:
    settings_path = Path(__file__).with_name("local.settings.json")
    if not settings_path.exists():
        return

    data = json.loads(settings_path.read_text())
    for key, value in data.get("Values", {}).items():
        os.environ.setdefault(key, str(value))


def build_client() -> tuple[EcwidClient, int]:
    settings = load_settings()
    return EcwidClient(settings.ecwid_api_token, settings.ecwid_shop_id), settings.max_skus


class DevApiHandler(BaseHTTPRequestHandler):
    server_version = "BusinessToolsDevApi/0.1"

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self.write_json({"ok": True})
            return
        self.write_json({"ok": False, "error": "Not found"}, status=404)

    def do_POST(self) -> None:
        if self.path not in {"/api/frontpage/preview", "/api/frontpage/apply"}:
            self.write_json({"ok": False, "error": "Not found"}, status=404)
            return

        try:
            payload = self.read_json()
            client, max_skus = build_client()
            plan = build_frontpage_plan(payload.get("skus", ""), client=client, max_skus=max_skus)

            if self.path == "/api/frontpage/preview":
                self.write_json({"ok": True, "canApply": len(plan.valid_skus) > 0, "plan": to_jsonable(plan)})
                return

            if not plan.valid_skus:
                self.write_json(
                    {
                        "ok": False,
                        "error": "No valid SKUs were found. Nothing was changed.",
                        "plan": to_jsonable(plan),
                    },
                    status=400,
                )
                return

            result = apply_frontpage_plan(plan, client=client)
            self.write_json(
                {"ok": not result.partial_failure, "result": to_jsonable(result)},
                status=207 if result.partial_failure else 200,
            )
        except (RuntimeError, EcwidClientError, json.JSONDecodeError) as exc:
            self.write_json({"ok": False, "error": str(exc)}, status=500)

    def read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0:
            return {}
        raw_body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(raw_body)
        return data if isinstance(data, dict) else {}

    def write_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    load_local_settings()
    host = os.environ.get("DEV_API_HOST", "127.0.0.1")
    port = int(os.environ.get("DEV_API_PORT", "7071"))
    server = ThreadingHTTPServer((host, port), DevApiHandler)
    print(f"Business Tools dev API running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
