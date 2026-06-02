from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SkuWarning:
    code: str
    sku: str
    message: str


@dataclass(frozen=True)
class FrontpageProduct:
    id: int
    sku: str
    name: str
    current_priority: int | None = None
    target_priority: int | None = None


@dataclass(frozen=True)
class FrontpagePlan:
    valid_skus: list[str]
    warnings: list[SkuWarning]
    removals: list[FrontpageProduct]
    additions: list[FrontpageProduct]
    unchanged: list[FrontpageProduct]


@dataclass(frozen=True)
class UpdateResult:
    product: FrontpageProduct
    success: bool
    action: str
    error: str | None = None


@dataclass(frozen=True)
class ApplyResult:
    plan: FrontpagePlan
    updates: list[UpdateResult]
    partial_failure: bool


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
