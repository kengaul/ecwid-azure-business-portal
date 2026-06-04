from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SupplierOption:
    name: str
    product_count: int


@dataclass(frozen=True)
class FeaturedCategory:
    id: int
    name: str


@dataclass(frozen=True)
class FeaturedProduct:
    id: int
    sku: str
    name: str
    enabled: bool
    supplier: str | None
    category_ids: list[int]
    default_category_id: int | None
    is_currently_featured: bool


@dataclass(frozen=True)
class FeaturedPlan:
    supplier: str
    featured_category: FeaturedCategory
    selected_products: list[FeaturedProduct]
    selectable_products: list[FeaturedProduct]
    products_to_add: list[FeaturedProduct]
    products_to_keep: list[FeaturedProduct]
    products_to_remove: list[FeaturedProduct]


@dataclass(frozen=True)
class FeaturedUpdateResult:
    product: FeaturedProduct
    success: bool
    action: str
    error: str | None = None


@dataclass(frozen=True)
class FeaturedApplyResult:
    plan: FeaturedPlan
    updates: list[FeaturedUpdateResult]
    partial_failure: bool


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
