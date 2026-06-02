from __future__ import annotations

import re

from business_tools.frontpage.models import SkuWarning

SKU_SPLIT_RE = re.compile(r"[\s,]+")
MAX_SKU_LENGTH = 128


def parse_skus(raw_skus: object, max_skus: int) -> tuple[list[str], list[SkuWarning]]:
    if isinstance(raw_skus, str):
        candidates = SKU_SPLIT_RE.split(raw_skus.strip())
    elif isinstance(raw_skus, list):
        candidates = []
        for item in raw_skus:
            candidates.extend(SKU_SPLIT_RE.split(str(item).strip()))
    else:
        candidates = []

    warnings: list[SkuWarning] = []
    skus: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        sku = candidate.strip()
        if not sku:
            continue

        if len(sku) > MAX_SKU_LENGTH or any(ord(char) < 32 for char in sku):
            warnings.append(
                SkuWarning(
                    code="invalid_format",
                    sku=sku,
                    message=f"SKU {sku} was skipped because it has an unsupported format.",
                )
            )
            continue

        key = sku.casefold()
        if key in seen:
            warnings.append(
                SkuWarning(
                    code="duplicate",
                    sku=sku,
                    message=f"Duplicate SKU {sku} was skipped.",
                )
            )
            continue

        seen.add(key)
        skus.append(sku)

    if len(skus) > max_skus:
        for sku in skus[max_skus:]:
            warnings.append(
                SkuWarning(
                    code="max_skus_exceeded",
                    sku=sku,
                    message=f"SKU {sku} was skipped because the list is limited to {max_skus} SKUs.",
                )
            )
        skus = skus[:max_skus]

    return skus, warnings
