"""Embed chunks and upsert them into Chroma.

Phase 2. Run with `make ingest`.
"""

# TODO(phase-2): load catalog.json + knowledge md -> clean -> chunk
# TODO(phase-2): embed with app.rag.embeddings (document task type)
# TODO(phase-2): HttpClient, collection with cosine distance, no embedding function
# TODO(phase-2): upsert by stable id, print chunk count
# TODO(phase-2): `if __name__ == "__main__":` entry point
