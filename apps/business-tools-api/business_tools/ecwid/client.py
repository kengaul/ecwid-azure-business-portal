from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class EcwidClientError(RuntimeError):
    pass


class EcwidClient:
    def __init__(self, api_token: str, shop_id: str, timeout_seconds: int = 20):
        self.base_url = f"https://app.ecwid.com/api/v3/{shop_id}"
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
                "User-Agent": "business-tools-frontpage/0.1",
            }
        )

    def get_product_by_sku(self, sku: str) -> dict[str, Any] | None:
        response = self.session.get(
            f"{self.base_url}/products",
            params={"sku": sku},
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            raise EcwidClientError(
                f"Failed to fetch SKU {sku}: {response.status_code} - {response.text}"
            )

        items = response.json().get("items", [])
        return items[0] if items else None

    def get_all_enabled_products(self) -> list[dict[str, Any]]:
        products: list[dict[str, Any]] = []
        offset = 0
        limit = 100

        while True:
            response = self.session.get(
                f"{self.base_url}/products",
                params={"offset": offset, "limit": limit, "enabled": "true"},
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                raise EcwidClientError(
                    f"Failed to fetch products: {response.status_code} - {response.text}"
                )

            items = response.json().get("items", [])
            if not items:
                return products

            products.extend(items)
            offset += limit

    def get_all_categories(self) -> list[dict[str, Any]]:
        categories: list[dict[str, Any]] = []
        offset = 0
        limit = 100

        while True:
            response = self.session.get(
                f"{self.base_url}/categories",
                params={
                    "offset": offset,
                    "limit": limit,
                    "hidden_categories": "true",
                    "withSubcategories": "true",
                    "responseFields": "items(id,parentId,name,enabled,productCount,enabledProductCount)",
                },
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                raise EcwidClientError(
                    f"Failed to fetch categories: {response.status_code} - {response.text}"
                )

            items = response.json().get("items", [])
            if not items:
                return categories

            categories.extend(items)
            offset += limit

    def get_products_by_category(self, category_id: int) -> list[dict[str, Any]]:
        products: list[dict[str, Any]] = []
        offset = 0
        limit = 100

        while True:
            response = self.session.get(
                f"{self.base_url}/products",
                params={
                    "offset": offset,
                    "limit": limit,
                    "category": str(category_id),
                    "includeProductsFromSubcategories": "false",
                    "responseFields": (
                        "items(id,sku,name,enabled,tax(taxable,defaultLocationIncludedTaxRate,"
                        "enabledManualTaxes,taxClassCode),categories(id,name,enabled))"
                    ),
                },
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                raise EcwidClientError(
                    f"Failed to fetch products for category {category_id}: "
                    f"{response.status_code} - {response.text}"
                )

            items = response.json().get("items", [])
            if not items:
                return products

            products.extend(items)
            offset += limit

    def update_product_frontpage(self, product_id: int, priority: int) -> None:
        response = self.session.put(
            f"{self.base_url}/products/{product_id}",
            json={"showOnFrontpage": priority},
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            raise EcwidClientError(
                f"Failed to update product {product_id}: {response.status_code} - {response.text}"
            )

    def update_product_tax_class(self, product_id: int, tax_class_code: str) -> None:
        response = self.session.put(
            f"{self.base_url}/products/{product_id}",
            json={"tax": {"taxable": True, "taxClassCode": tax_class_code}},
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            raise EcwidClientError(
                f"Failed to update tax class for product {product_id}: "
                f"{response.status_code} - {response.text}"
            )
