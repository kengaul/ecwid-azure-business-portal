import logging
import argparse
from ecwid_api import update_product_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Combinations url = f"https://app.ecwid.com/api/v3/106830567/products/{product_id}/combinations"
# From response iterate through combinations and update images
# Get combination id JSONPath $.items[0].combinations[${iterationcount}].id
# Figure out how to match the combintation iteration_id or combination_id to the actual image...Looks like there is a sku so maybe can use the same process as I did for the lightspeed image load.
# url = "https://app.ecwid.com/api/v3/106830567/products/${product_id}/combinations/${combination_id}/images"
# 
# If there are extra images of different views etc then upload those to the gallery
# loop through gallery directory and upload images to the gallery
url = "https://app.ecwid.com/api/v3/106830567/products/${product_id}/gallery"


def main():
    ap = argparse.ArgumentParser(description="Upload iumages to produc on web only")
    ap.add_argument("--sku", default="1234567", help="sku of product to update")
    ap.add_argument("--image", default="image.jpg", help="image file to upload")
    args = ap.parse_args()
    update_product_image(args.sku, args.image)

if __name__ == "__main__":
    main()
