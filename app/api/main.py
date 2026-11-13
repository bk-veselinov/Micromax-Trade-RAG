"""FastAPI app: /health, /search, /ask, /chat.

Phase 0 (/health), Phase 4 (the rest), Phase 5 (/chat).
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO(phase-4): create Chroma + Gemini clients and the retriever once
    print("Starting up...")
    yield
    print("Shutting down...")
    # TODO(phase-4): cleanup clients

app = FastAPI(title="Micromax Trade RAG", lifespan=lifespan)

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


# TODO(phase-4): lifespan: create Chroma + Gemini clients and the retriever once
# TODO(phase-4): POST /search, POST /ask; 503 when Chroma is down
# TODO(phase-4): log query, latency, source ids (no personal data)
# TODO(phase-5): POST /chat via ADK Runner + InMemorySessionService, keyed by session_id
