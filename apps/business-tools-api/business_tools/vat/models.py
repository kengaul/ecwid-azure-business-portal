from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ZERO_RATED_TAX_CLASS_CODE = "zero"


@dataclass(frozen=True)
class CategoryOption:
    id: int
    name: str
    enabled: bool
    parent_id: int | None = None
    product_count: int | None = None
    enabled_product_count: int | None = None


@dataclass(frozen=True)
class VatProduct:
    id: int
    sku: str
    name: str
    enabled: bool
    current_tax_class_code: str | None
    current_tax_rate: float | None
    taxable: bool | None


@dataclass(frozen=True)
class VatPlan:
    category: CategoryOption
    products_to_update: list[VatProduct]
    already_zero_rated: list[VatProduct]


@dataclass(frozen=True)
class VatUpdateResult:
    product: VatProduct
    success: bool
    error: str | None = None


@dataclass(frozen=True)
class VatApplyResult:
    plan: VatPlan
    updates: list[VatUpdateResult]
    partial_failure: bool


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
