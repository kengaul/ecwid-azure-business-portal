import argparse
import logging
from ecwid_api import get_product_by_sku, update_product_frontpage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_skus(filename, dry_run=False):
    with open(filename, "r") as file:
        skus = [line.strip() for line in file if line.strip()]

    for i, sku in enumerate(skus, start=1):
        product = get_product_by_sku(sku)
        if product:
            update_product_frontpage(product["id"], i, dry_run=dry_run)
        else:
            logger.warning(f"SKU not found: {sku}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore frontpage priority based on SKU list.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without updating Ecwid.")
    parser.add_argument("--sku-file", default="frontpage_skus.txt", help="Path to SKU list file.")

    args = parser.parse_args()

    process_skus(args.sku_file, dry_run=args.dry_run)
