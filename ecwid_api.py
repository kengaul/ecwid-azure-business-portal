import os
import requests
import logging

# Configure module-level logger
logger = logging.getLogger(__name__)

API_TOKEN = os.environ.get("ECWID_API_TOKEN")
SHOP_ID = os.environ.get("ECWID_SHOP_ID")

if not API_TOKEN or not SHOP_ID:
    raise EnvironmentError("ECWID_API_TOKEN and ECWID_SHOP_ID must be set in the environment.")

BASE_URL = f"https://app.ecwid.com/api/v3/{SHOP_ID}"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "ecwid-api-client"
}

def get_product_by_sku(sku):
    url = f"{BASE_URL}/products?sku={sku}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        items = response.json().get("items", [])
        return items[0] if items else None
    else:
        logger.error(f"Error fetching product for SKU {sku}: {response.status_code} - {response.text}")
        return None

def update_product_frontpage(product_id, priority, dry_run=False):
    if dry_run:
        logger.info(f"[DRY RUN] Would update product {product_id} with showOnFrontpage = {priority}")
        return True

    url = f"{BASE_URL}/products/{product_id}"
    payload = {"showOnFrontpage": priority}
    response = requests.put(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        logger.info(f"Updated product {product_id} with frontpage priority {priority}")
        return True
    else:
        logger.error(f"Failed to update product {product_id}: {response.status_code} - {response.text}")
        return False


def get_all_enabled_products():
    """Return all enabled products using paging."""
    products = []
    offset = 0
    limit = 100

    while True:
        url = f"{BASE_URL}/products?offset={offset}&limit={limit}&enabled=true"
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            logger.error(f"Failed to fetch products: {response.status_code}")
            break

        data = response.json()
        items = data.get("items", [])
        if not items:
            break

        products.extend(items)
        offset += limit
        logger.debug(f"Fetched {len(items)} products; total so far: {len(products)}")

    return products

def get_all_categories():
    """Return all enabled products using paging."""
    categories = []
    offset = 0
    limit = 100

    while True:
        url = f"{BASE_URL}/categories?offset={offset}&limit={limit}&hidden_categories=true&withSubcategories=true"
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            logger.error(f"Failed to fetch categories: {response.status_code}")
            break

        data = response.json()
        items = data.get("items", [])
        if not items:
            break

        categories.extend(items)
        offset += limit
        logger.debug(f"Fetched {len(items)} categories; total so far: {len(categories)}")

    return categories

def update_category_enabled(category_id: int, enabled: bool, dry_run: bool = False):
    if dry_run:
        logger.info(f"[DRY RUN] Would set category {category_id} enabled={enabled}")
        return True
    url = f"{BASE_URL}/categories/{category_id}"
    payload = {"enabled": enabled}
    r = requests.put(url, headers=HEADERS, json=payload)
    if r.status_code == 200:
        logger.info(f"Category {category_id} set enabled={enabled}")
        return True
    logger.error(f"Failed to update category {category_id}: {r.status_code} - {r.text}")
    return False

def update_product_category(product_id: int, new_category_id: int, dry_run: bool = False):
    """
    Set the product's main category to new_category_id.
    Note: Ecwid uses 'categoryId' as the primary category field. We keep it simple here.
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would move product {product_id} -> category {new_category_id}")
        return True
    url = f"{BASE_URL}/products/{product_id}"
    payload = {"categoryId": new_category_id}
    r = requests.put(url, headers=HEADERS, json=payload)
    if r.status_code == 200:
        logger.info(f"Moved product {product_id} -> category {new_category_id}")
        return True
    logger.error(f"Failed to move product {product_id}: {r.status_code} - {r.text}")
    return False
def get_enabled_categories_map():
    """Returns {id: category_obj} for enabled categories."""
    cats = get_all_categories()
    return {c["id"]: c for c in cats if c.get("enabled", True)}

def resolve_enabled_category_id(name_or_id):
    """
    Accepts either an int-like id or a category name (case-insensitive).
    Returns an enabled category id or None.
    """
    enabled = get_enabled_categories_map()
    # try id
    try:
        cid = int(name_or_id)
        return cid if cid in enabled else None
    except (TypeError, ValueError):
        pass
    # try name
    lowered = str(name_or_id).strip().lower()
    for cid, c in enabled.items():
        if c.get("name", "").strip().lower() == lowered:
            return cid
    return None

def update_product_image(sku: str, image_path: str):
    # Get product
    img_headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "image/jpeg",
        "User-Agent": "ecwid-api-client"
    }
    # From response get the product id JSON extract $.items[0].id
    # Get the product id from the JSON
    if sku is None or image_path is None:
        logger.error("SKU and image_path must be provided.")
        return
    
    product_id = get_product_by_sku(sku)["id"]
    logger.info(f"Product ID: {product_id}")

    # Update main image
    # Get payload from file
    with open(image_path, "rb") as image:
        image_data = image.read()
    payload = image_data
    url = f"https://app.ecwid.com/api/v3/{product_id}/images"
    response = requests.request("POST", url, data=payload, headers=img_headers)