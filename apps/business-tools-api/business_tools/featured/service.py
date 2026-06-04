from __future__ import annotations

from collections import Counter
from typing import Protocol

from business_tools.featured.models import (
    FeaturedApplyResult,
    FeaturedCategory,
    FeaturedPlan,
    FeaturedProduct,
    FeaturedUpdateResult,
    SupplierOption,
)


class FeaturedEcwidClient(Protocol):
    def get_all_categories(self) -> list[dict]:
        ...

    def search_enabled_products(self, extra_params: dict[str, str] | None = None) -> list[dict]:
        ...

    def get_products_by_category(self, category_id: int) -> list[dict]:
        ...

    def update_product_category_ids(self, product_id: int, category_ids: list[int]) -> None:
        ...


def _attribute_value(product: dict, attribute_name: str) -> str | None:
    for attribute in product.get("attributes") or []:
        if str(attribute.get("name", "")).casefold() == attribute_name.casefold():
            value = str(attribute.get("value", "")).strip()
            return value or None
    return None


def _supplier_value(product: dict) -> str | None:
    for attribute in product.get("attributes") or []:
        if str(attribute.get("type", "")).casefold() == "supplier":
            value = str(attribute.get("value", "")).strip()
            return value or None
    return _attribute_value(product, "Supplier") or _attribute_value(product, "Brand")


def _category_ids(product: dict) -> list[int]:
    ids = product.get("categoryIds")
    if isinstance(ids, list):
        return [int(category_id) for category_id in ids]
    categories = product.get("categories") or []
    return [int(category["id"]) for category in categories if "id" in category]


def _featured_product(product: dict, featured_category_id: int) -> FeaturedProduct:
    category_ids = _category_ids(product)
    default_category_id = product.get("defaultCategoryId")
    return FeaturedProduct(
        id=int(product["id"]),
        sku=str(product.get("sku", "")),
        name=str(product.get("name", "")),
        enabled=bool(product.get("enabled", True)),
        supplier=_supplier_value(product),
        category_ids=category_ids,
        default_category_id=int(default_category_id) if default_category_id is not None else None,
        is_currently_featured=featured_category_id in category_ids,
    )


def resolve_featured_category(
    client: FeaturedEcwidClient,
    featured_category_name: str,
) -> FeaturedCategory:
    categories = client.get_all_categories()
    matches = [
        category
        for category in categories
        if str(category.get("name", "")).strip().casefold() == featured_category_name.strip().casefold()
    ]
    if len(matches) == 1:
        category = matches[0]
        return FeaturedCategory(id=int(category["id"]), name=str(category.get("name", "")))
    if len(matches) > 1:
        raise ValueError(
            f"Multiple categories named {featured_category_name!r} were found. Rename one of them before using this tool."
        )
    raise ValueError(
        f"Featured category {featured_category_name!r} was not found. Create it or check FEATURED_PRODUCTS_CATEGORY_NAME."
    )


def list_suppliers(client: FeaturedEcwidClient) -> list[SupplierOption]:
    counts: Counter[str] = Counter()
    for product in client.search_enabled_products():
        supplier = _supplier_value(product)
        if supplier:
            counts[supplier] += 1

    return [
        SupplierOption(name=name, product_count=count)
        for name, count in sorted(counts.items(), key=lambda item: item[0].casefold())
    ]


def build_featured_plan(
    supplier: str,
    client: FeaturedEcwidClient,
    featured_category_name: str,
    selected_product_ids: set[int] | None = None,
) -> FeaturedPlan:
    supplier = supplier.strip()
    if not supplier:
        raise ValueError("Select a supplier.")

    featured_category = resolve_featured_category(client, featured_category_name)
    supplier_products = [
        _featured_product(product, featured_category.id)
        for product in client.search_enabled_products()
        if (_supplier_value(product) or "").casefold() == supplier.casefold()
    ]
    selectable_products = sorted(supplier_products, key=lambda product: (product.name.casefold(), product.id))
    if selected_product_ids is None:
        selected_product_ids = {product.id for product in selectable_products}

    selected_products = [product for product in selectable_products if product.id in selected_product_ids]
    selected_ids = {product.id for product in selected_products}
    current_featured = [
        _featured_product(product, featured_category.id)
        for product in client.get_products_by_category(featured_category.id)
    ]
    selected_existing_ids = {product.id for product in selected_products if product.is_currently_featured}
    current_by_id = {product.id: product for product in current_featured}

    products_to_add = [product for product in selected_products if not product.is_currently_featured]
    products_to_keep = [
        current_by_id[product_id]
        for product_id in sorted(selected_existing_ids)
        if product_id in current_by_id
    ]
    products_to_remove = [
        product for product in current_featured if product.id not in selected_ids
    ]

    return FeaturedPlan(
        supplier=supplier,
        featured_category=featured_category,
        selected_products=selected_products,
        selectable_products=selectable_products,
        products_to_add=products_to_add,
        products_to_keep=products_to_keep,
        products_to_remove=products_to_remove,
    )


def apply_featured_plan(plan: FeaturedPlan, client: FeaturedEcwidClient) -> FeaturedApplyResult:
    updates: list[FeaturedUpdateResult] = []
    partial_failure = False
    featured_category_id = plan.featured_category.id

    for product in plan.products_to_remove:
        try:
            category_ids = [category_id for category_id in product.category_ids if category_id != featured_category_id]
            client.update_product_category_ids(product.id, category_ids)
            updates.append(FeaturedUpdateResult(product=product, success=True, action="remove"))
        except Exception as exc:
            partial_failure = True
            updates.append(FeaturedUpdateResult(product=product, success=False, action="remove", error=str(exc)))
            return FeaturedApplyResult(plan=plan, updates=updates, partial_failure=partial_failure)

    for product in plan.products_to_add:
        try:
            category_ids = sorted({*product.category_ids, featured_category_id})
            client.update_product_category_ids(product.id, category_ids)
            updates.append(FeaturedUpdateResult(product=product, success=True, action="add"))
        except Exception as exc:
            partial_failure = True
            updates.append(FeaturedUpdateResult(product=product, success=False, action="add", error=str(exc)))
            return FeaturedApplyResult(plan=plan, updates=updates, partial_failure=partial_failure)

    for product in plan.products_to_keep:
        updates.append(FeaturedUpdateResult(product=product, success=True, action="keep"))

    return FeaturedApplyResult(plan=plan, updates=updates, partial_failure=partial_failure)
