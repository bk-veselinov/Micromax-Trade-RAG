"""Clean raw catalog records before chunking.

Phase 2.
"""

# TODO(phase-2): strip_html(html) -> str  (BeautifulSoup, normalise whitespace)
# TODO(phase-2): drop price fields: price, regular_price, sale_price, price_html
# TODO(phase-2): variation_summary(variations) -> str
#   - distinct attribute values in 1-2 lines, never one chunk per variation
