import argparse
import csv
import logging
from typing import Optional
from collections import defaultdict

from ecwid_api import get_all_enabled_products, get_all_categories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_primary_category_id(p: dict) -> Optional[int]:
    if p.get("defaultCategoryId"):
        return p["defaultCategoryId"]
    if p.get("categoryId"):
        return p["categoryId"]
    if p.get("categories"):
        return p["categories"][0].get("id")
    if p.get("categoryIds"):
        return p["categoryIds"][0]
    return None

def get_effective_enabled_category_id(p: dict, cat_enabled: dict[int, bool]) -> Optional[int]:
    primary = get_primary_category_id(p)
    if primary is not None and cat_enabled.get(primary, True):
        return primary
    for c in p.get("categories", []):
        cid = c.get("id")
        if cid is not None and c.get("enabled", cat_enabled.get(cid, True)):
            return cid
    for cid in p.get("categoryIds", []):
        if cat_enabled.get(cid, True):
            return cid
    return None

def export_csv(path: str):
    products = get_all_enabled_products()
    categories = get_all_categories()
    cat_by_id = {c["id"]: c for c in categories}
    cat_enabled = {c["id"]: bool(c.get("enabled", True)) for c in categories}

    rows = []
    for p in products:
        primary = get_primary_category_id(p)
        effective = get_effective_enabled_category_id(p, cat_enabled)

        # “Needs attention” if no effective, or effective exists but disabled
        needs = (effective is None) or (not cat_enabled.get(effective, True))
        if not needs:
            continue

        assigned_ids = p.get("categoryIds", [])
        assigned_names = [cat_by_id.get(cid, {}).get("name", "") for cid in assigned_ids]

        rows.append({
            "product_id": p["id"],
            "sku": p.get("sku", ""),
            "product_name": p.get("name", ""),
            "primary_category_id": primary or "",
            "primary_category_name": cat_by_id.get(primary, {}).get("name", "") if primary else "",
            "effective_category_id": effective or "",
            "effective_category_name": cat_by_id.get(effective, {}).get("name", "") if effective else "",
            "assigned_category_ids": ",".join(str(x) for x in assigned_ids),
            "assigned_category_names": "|".join(assigned_names),
            "new_category": "",  # YOU fill this in later (id or name of enabled category)
            "notes": "",
        })

    if not rows:
        logger.info("No products requiring category fixes found.")
        return

    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Wrote {len(rows)} rows to {path}")

def main():
    ap = argparse.ArgumentParser(description="Export products needing category fix to a CSV.")
    ap.add_argument("--out", default="category_fixes.csv", help="Output CSV path")
    args = ap.parse_args()
    export_csv(args.out)

if __name__ == "__main__":
    main()
