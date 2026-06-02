import argparse
import logging
from ecwid_api import get_all_enabled_products, update_product_frontpage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup(dry_run=False):
    products = get_all_enabled_products()
    to_update = [p for p in products if p.get("showOnFrontpage", 0) > 0 and p.get('inStock', False) == False]

    logger.info(f"{len(to_update)} products will be removed from the front page.")

    for product in to_update:
        logger.info(f"product {product['sku']} will be removed from the front page - {product['inStock']}")
        update_product_frontpage(product["id"], -1, dry_run=dry_run)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove products from frontpage.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without updating Ecwid.")

    args = parser.parse_args()
    cleanup(dry_run=args.dry_run)
