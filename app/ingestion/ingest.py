"""Embed chunks and upsert them into Chroma.

"""

import contextlib
import logging
from collections import Counter

import chromadb

from app.config import settings
from app.ingestion.chunking import all_chunks
from app.rag.embeddings import embed

def main() -> None:
    """Ingest catalog and knowledge into Chroma."""

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    client = chromadb.HttpClient(host=settings.chroma_host,
                                 port=settings.chroma_port)
    client.heartbeat()

    chunks = all_chunks()
    print(f"Built {len(chunks)} chunks: {dict(Counter(c.metadata['type'] for c in chunks))}")

    vectors = embed([chunk.text for chunk in chunks], task="RETRIEVAL_DOCUMENT")
    dims = {len(v) for v in vectors}
    if dims != {settings.embed_dim}:
        raise ValueError(f"Unexpected embedding dimension(s): {dims}, expected {settings.embed_dim}")

    with contextlib.suppress(chromadb.errors.NotFoundError):
        client.delete_collection(name=settings.chroma_collection)
    collection = client.create_collection(
        name=settings.chroma_collection,
        configuration={"hnsw": {"space": "cosine"}},
        embedding_function=None,
    )

    step = client.get_max_batch_size()
    for i in range(0, len(chunks), step):
        batch = chunks[i:i + step]
        collection.add(
            ids=[chunk.id for chunk in batch],
            metadatas=[chunk.metadata for chunk in batch],
            documents=[chunk.text for chunk in batch],
            embeddings=vectors[i:i + step],
        )
        print(f"Added {len(batch)} chunks ({i + len(batch)}/{len(chunks)})")

    print(f"Collection '{settings.chroma_collection}' now has {collection.count()} chunks")

if __name__ == "__main__":
    main()
