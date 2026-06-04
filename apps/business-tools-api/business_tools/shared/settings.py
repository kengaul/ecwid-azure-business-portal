from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ecwid_api_token: str
    ecwid_shop_id: str
    max_skus: int = 200
    app_environment: str = "production"
    featured_products_category_name: str = "Featured Products"


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} must be set.")
    return value


def load_settings() -> Settings:
    max_skus = int(os.environ.get("FRONTPAGE_MAX_SKUS", "200"))
    return Settings(
        ecwid_api_token=_required_env("ECWID_API_TOKEN"),
        ecwid_shop_id=_required_env("ECWID_SHOP_ID"),
        max_skus=max_skus,
        app_environment=os.environ.get("APP_ENVIRONMENT", "production"),
        featured_products_category_name=os.environ.get(
            "FEATURED_PRODUCTS_CATEGORY_NAME", "Featured Products"
        ),
    )
