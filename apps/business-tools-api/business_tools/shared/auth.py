from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class UserContext:
    name: str | None
    roles: list[str]


def parse_static_web_apps_user(header_value: str | None) -> UserContext:
    """Parse x-ms-client-principal when Static Web Apps forwards an authenticated user."""
    if not header_value:
        return UserContext(name=None, roles=[])

    try:
        import base64

        decoded = base64.b64decode(header_value).decode("utf-8")
        data = json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        return UserContext(name=None, roles=[])

    return UserContext(
        name=data.get("userDetails"),
        roles=data.get("userRoles", []),
    )
