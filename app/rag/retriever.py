"""Hybrid retriever: Chroma vectors + BM25, merged with Reciprocal Rank Fusion.

Phase 3. See asd.md -> "Hybrid search".
"""

# TODO(phase-3): tokenize(text) -> list[str]
#   - lowercase, split on non-word chars, keep codes/SKUs whole (EN 12756, K1, NBR, MPN)
# TODO(phase-3): build BM25Okapi at startup from the same ids/texts stored in Chroma
# TODO(phase-3): rrf(rankings, k=60) -> fused ranking
# TODO(phase-3): search(query, k=5, source=None, mode="hybrid") -> list of hits
#   - top 20 from each side, same `source` filter on both
#   - keep vector and BM25 ranks on each hit for /search debugging
#   - drop hits beyond the distance threshold
