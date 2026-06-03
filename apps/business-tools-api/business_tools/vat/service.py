from __future__ import annotations

from typing import Protocol

from business_tools.vat.models import (
    ZERO_RATED_TAX_CLASS_CODE,
    CategoryOption,
    VatApplyResult,
    VatPlan,
    VatProduct,
    VatUpdateResult,
)


class VatEcwidClient(Protocol):
    def get_all_categories(self) -> list[dict]:
        ...

    def get_products_by_category(self, category_id: int) -> list[dict]:
        ...

    def update_product_tax_class(self, product_id: int, tax_class_code: str) -> None:
        ...


def _category_option(category: dict) -> CategoryOption:
    return CategoryOption(
        id=int(category["id"]),
        name=str(category.get("name", "")),
        enabled=bool(category.get("enabled", True)),
        parent_id=category.get("parentId"),
        product_count=category.get("productCount"),
        enabled_product_count=category.get("enabledProductCount"),
    )


def _vat_product(product: dict) -> VatProduct:
    tax = product.get("tax") or {}
    return VatProduct(
        id=int(product["id"]),
        sku=str(product.get("sku", "")),
        name=str(product.get("name", "")),
        enabled=bool(product.get("enabled", True)),
        current_tax_class_code=tax.get("taxClassCode"),
        current_tax_rate=tax.get("defaultLocationIncludedTaxRate"),
        taxable=tax.get("taxable"),
    )


def list_categories(client: VatEcwidClient) -> list[CategoryOption]:
    categories = [_category_option(category) for category in client.get_all_categories()]
    return sorted(categories, key=lambda category: (category.name.casefold(), category.id))


def build_vat_plan(category_id: int, client: VatEcwidClient) -> VatPlan:
    categories = {category.id: category for category in list_categories(client)}
    if category_id not in categories:
        raise ValueError(f"Category {category_id} was not found.")

    products = [_vat_product(product) for product in client.get_products_by_category(category_id)]
    products_to_update = [
        product
        for product in products
        if (product.current_tax_class_code or "").casefold() != ZERO_RATED_TAX_CLASS_CODE
    ]
    already_zero_rated = [
        product
        for product in products
        if (product.current_tax_class_code or "").casefold() == ZERO_RATED_TAX_CLASS_CODE
    ]

    return VatPlan(
        category=categories[category_id],
        products_to_update=products_to_update,
        already_zero_rated=already_zero_rated,
    )


def apply_vat_plan(plan: VatPlan, client: VatEcwidClient) -> VatApplyResult:
    updates: list[VatUpdateResult] = []
    partial_failure = False

    for product in plan.products_to_update:
        try:
            client.update_product_tax_class(product.id, ZERO_RATED_TAX_CLASS_CODE)
            updates.append(VatUpdateResult(product=product, success=True))
        except Exception as exc:
            partial_failure = True
            updates.append(VatUpdateResult(product=product, success=False, error=str(exc)))
            return VatApplyResult(plan=plan, updates=updates, partial_failure=partial_failure)

    return VatApplyResult(plan=plan, updates=updates, partial_failure=partial_failure)
