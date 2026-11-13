"""Export the catalog from the WordPress REST API into data/raw/catalog.json.

Phase 1. Run with `make extract`. The output is committed, so later phases need no API keys.
"""
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.config import settings

OUT = Path("data/raw/catalog.json")
BRANCHES_DATA = Path("data/raw/branches.json")
PRICE_FIELDS = {"price", "regular_price", "sale_price", "price_html"}
log = logging.getLogger(__name__)

def fetch_all(client: httpx.Client, path: str, params: dict | None = None, auth: tuple[str, str] | None = None) -> list[dict]:
    if params is None:
        params = {}

    items:list[dict] = []
    page = 1
    total_pages = 1
    while True:
        if page > total_pages:
            break
        params.update({"per_page": 100, "page": page})
        response = client.get(path, params=params, auth=auth)
        response.raise_for_status()
        total_pages = int(response.headers.get("X-WP-TotalPages", 1))

        data = response.json()
        items.extend(data)
        page += 1
        log.info(f"Fetched {len(data)} items from {path} (page {page-1}/{total_pages})")

    return items

def write_catalog_json(categories: list[dict], products: list[dict], services: list[dict]) -> None:
    
    catalog = {
        "timestamp": datetime.now(UTC).isoformat(),
        "source": {
            "wp_base_url": settings.wp_base_url,
            "services_rest_base": settings.services_rest_base,
        },
        "categories": sorted(categories, key=lambda c: c["id"]),
        "products": sorted(products, key=lambda p: p["id"]),
        "services": sorted(services, key=lambda s: s["id"])
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

def strip_price_fields(item: dict) -> dict:
    """Remove price fields from a product or variation dict."""
    return {k: v for k, v in item.items() if k not in PRICE_FIELDS}

def main():
    if settings.wc_key is None or settings.wc_secret is None:
        raise ValueError("WC_KEY and WC_SECRET must be set in .env")
    if settings.wp_base_url is None or settings.services_rest_base is None:
        raise ValueError("WP_BASE_URL and SERVICES_REST_BASE must be set in .env")
    if settings.branch_rest_base is None:
        raise ValueError("BRANCH_REST_BASE must be set in .env")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    auth = (settings.wc_key, settings.wc_secret)

    with httpx.Client(timeout=30.0, base_url=settings.wp_base_url) as client:
        branches = fetch_all(client, f"{settings.branch_rest_base}")
        products = fetch_all(client, "/wc/v3/products", auth=auth)
        products = [strip_price_fields(product) for product in products]
        for product in products:
            if product["type"] == "variable":
                product_id = product["id"]
                variations = []
                variations.extend(fetch_all(client, f"/wc/v3/products/{product_id}/variations", auth=auth))
                variations = [strip_price_fields(variation) for variation in variations]
                product["variations_data"] = variations
        categories = fetch_all(client, "/wc/v3/products/categories", auth=auth)
        services = fetch_all(client, f"{settings.services_rest_base}")

    write_catalog_json(categories, products, services)
    with open(BRANCHES_DATA, "w", encoding="utf-8") as f:
        json.dump(sorted(branches, key=lambda b: b["menu_order"]), f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()