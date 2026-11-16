"""Gemini embedding wrapper.
"""

import logging
import time

from google import genai
from google.genai import errors, types

from app.config import settings

log = logging.getLogger(__name__)
_client: genai.Client | None = None


def client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.google_api_key)
    return _client

def embed(texts: list[str], task: str) -> list[list[float]]:
    """task: "RETRIEVAL_DOCUMENT" for chunks, "RETRIEVAL_QUERY" for questions."""
    vectors: list[list[float]] = []
    size = settings.embed_batch_size
    batches = (texts[j:j + size] for j in range(0, len(texts), size))
    for i, batch in enumerate(batches, start=1):
        for attempt in range(6):
            try:
                response = client().models.embed_content(
                    model=settings.embed_model,
                    contents=[types.Content(parts=[types.Part(text=t)]) for t in batch],
                    config=types.EmbedContentConfig(
                        task_type=task,
                        output_dimensionality=settings.embed_dim,
                    ),
                )
                break
            except errors.APIError as e:
                if e.code != 429 or attempt == 5:
                    raise
                wait = 2 ** attempt * 5
                log.warning("Rate limited, retrying in %ss", wait)
                time.sleep(wait)
        if len(response.embeddings) != len(batch):
            raise RuntimeError(
                f"Batch {i}: sent {len(batch)} texts, got {len(response.embeddings)} embeddings"
            )
        vectors.extend(emb.values for emb in response.embeddings)
        log.info("Embedded batch %d (%d texts)", i, len(batch))
    return vectors


def embed_query(question: str) -> list[float]:
    return embed([question], "RETRIEVAL_QUERY")[0]