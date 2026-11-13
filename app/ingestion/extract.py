"""Export the catalog from the WordPress REST API into data/raw/catalog.json.

Phase 1. Run with `make extract`. The output is committed, so later phases need no API keys.
"""

# TODO(phase-1): fetch_all(client, path, params) -> list[dict]
#   - per_page=100, follow the X-WP-TotalPages header
# TODO(phase-1): endpoints
#   - /wp-json/wc/v3/products (+ /products/{id}/variations for variable products)
#   - /wp-json/wc/v3/products/categories
#   - /wp-json/wp/v2/<services rest_base>
# TODO(phase-1): write catalog.json with ensure_ascii=False and print counts per type
# TODO(phase-1): `if __name__ == "__main__":` entry point
