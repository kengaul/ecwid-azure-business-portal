from __future__ import annotations

from typing import Protocol

from business_tools.frontpage.models import (
    ApplyResult,
    FrontpagePlan,
    FrontpageProduct,
    SkuWarning,
    UpdateResult,
)
from business_tools.frontpage.parser import parse_skus


class FrontpageEcwidClient(Protocol):
    def get_product_by_sku(self, sku: str) -> dict | None:
        ...

    def get_all_enabled_products(self) -> list[dict]:
        ...

    def update_product_frontpage(self, product_id: int, priority: int) -> None:
        ...


def _frontpage_product(product: dict, target_priority: int | None = None) -> FrontpageProduct:
    return FrontpageProduct(
        id=int(product["id"]),
        sku=str(product.get("sku", "")),
        name=str(product.get("name", "")),
        current_priority=product.get("showOnFrontpage"),
        target_priority=target_priority,
    )


def build_frontpage_plan(
    raw_skus: object,
    client: FrontpageEcwidClient,
    max_skus: int,
) -> FrontpagePlan:
    submitted_skus, warnings = parse_skus(raw_skus, max_skus=max_skus)

    current_frontpage = [
        product
        for product in client.get_all_enabled_products()
        if int(product.get("showOnFrontpage", 0) or 0) > 0
    ]
    resolved_products: list[dict] = []
    for sku in submitted_skus:
        product = client.get_product_by_sku(sku)
        if product is None:
            warnings.append(
                SkuWarning(
                    code="not_found",
                    sku=sku,
                    message=f"SKU {sku} was not found and will be skipped.",
                )
            )
            continue
        resolved_products.append(product)

    valid_skus = [str(product.get("sku", "")) for product in resolved_products]
    removals = [
        _frontpage_product(product)
        for product in sorted(current_frontpage, key=lambda item: int(item.get("showOnFrontpage", 0)))
    ]

    additions: list[FrontpageProduct] = []
    for priority, product in enumerate(resolved_products, start=1):
        planned = _frontpage_product(product, target_priority=priority)
        additions.append(planned)

    return FrontpagePlan(
        valid_skus=valid_skus,
        warnings=warnings,
        removals=removals,
        additions=additions,
        unchanged=[],
    )


def apply_frontpage_plan(plan: FrontpagePlan, client: FrontpageEcwidClient) -> ApplyResult:
    updates: list[UpdateResult] = []
    partial_failure = False

    for product in plan.removals:
        try:
            client.update_product_frontpage(product.id, -1)
            updates.append(UpdateResult(product=product, success=True, action="remove"))
        except Exception as exc:
            partial_failure = True
            updates.append(UpdateResult(product=product, success=False, action="remove", error=str(exc)))
            return ApplyResult(plan=plan, updates=updates, partial_failure=partial_failure)

    products_to_place = sorted(
        [*plan.additions, *plan.unchanged],
        key=lambda product: product.target_priority or 0,
    )
    for product in products_to_place:
        try:
            client.update_product_frontpage(product.id, product.target_priority or 1)
            updates.append(UpdateResult(product=product, success=True, action="set_priority"))
        except Exception as exc:
            partial_failure = True
            updates.append(
                UpdateResult(product=product, success=False, action="set_priority", error=str(exc))
            )
            return ApplyResult(plan=plan, updates=updates, partial_failure=partial_failure)

    return ApplyResult(plan=plan, updates=updates, partial_failure=partial_failure)
