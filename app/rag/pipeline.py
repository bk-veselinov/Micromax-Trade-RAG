"""Fixed RAG flow: retrieve -> prompt -> Gemini -> answer + sources.
"""

import re

from google.genai import types

from app.config import settings
from app.rag.embeddings import client
from app.rag.prompts import (
    NOT_FOUND,
    PRICE_FALLBACK,
    SYSTEM_PROMPT,
    format_context,
    user_prompt,
)
from app.rag.retriever import Hit, Retriever

PRICE = re.compile(r"\d[\d\s.,]*\s?(?:€|eur\b|евро|лв\.?|лева|bgn)", re.IGNORECASE)
CITATION = re.compile(r"\[(\d+)\]")

def to_sources(hits: list[Hit]) -> list[dict]:
    sources, seen = [], set()
    for h in hits:
        key = h.metadata.get("permalink") or h.metadata.get("parent_id", h.chunk_id)
        if key in seen:
            continue
        seen.add(key)
        sources.append({"title": h.metadata.get("title"), "url": h.metadata.get("permalink"),
                        "chunk_id": h.chunk_id})
    return sources

def answer(question: str, retriever: Retriever, source: str | None = None,
           mode: str | None = None) -> dict:
    """Answer a question with context from the retriever and Gemini."""

    hits = retriever.search(question, source=source, mode=mode)

    if not hits:
        return {"answer": NOT_FOUND, "sources": []}

    response = client().models.generate_content(
        model=settings.llm_model,
        contents=user_prompt(question, format_context(hits)),
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )

    text = (response.text or "").strip() or NOT_FOUND
    
    if any(PRICE.search(h.text) for h in hits):
        return {"answer": PRICE_FALLBACK, "sources": []}
   
    cited = {int(n) for n in CITATION.findall(text)}
    used = [h for i, h in enumerate(hits, start=1) if i in cited] or hits
    return {"answer": text, "sources": to_sources(used)}

