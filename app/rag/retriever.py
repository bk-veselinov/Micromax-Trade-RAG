"""Hybrid retriever: Chroma vectors + BM25, merged with Reciprocal Rank Fusion.

"""
import math
import re
from collections import defaultdict
from dataclasses import dataclass

from chromadb.api.models.Collection import Collection
from rank_bm25 import BM25Okapi

from app.config import settings
from app.rag.embeddings import embed_query

TOKEN = re.compile(r"\w+(?:[-./]\w+)*")
DIAMETER = re.compile(r"[Øø⌀∅0]")
DECIMAL_COMMA = re.compile(r"(?<=\d),(?=\d)")
LOOKALIKE = str.maketrans("авекмнорстух", "abekmhopctyx") 
LATIN_OR_DIGIT = re.compile(r"[a-z0-9]")


def normalize(text: str) -> str:
    """Normalize text for BM25 indexing and searching."""
    text = text.lower()
    text = DIAMETER.sub("0", text)
    text = DECIMAL_COMMA.sub(".", text)
    return text


def tokenize(text: str) -> list[str]:
    """Tokenize text for BM25 indexing and searching."""
    tockens = []
    for token in TOKEN.findall(text):
        if LATIN_OR_DIGIT.search(token):
            token = token.translate(LOOKALIKE)
        tockens.append(token)

        if ("-", "_", "/") in token:
            subtokens = re.split(r"[-./]", token)
            tockens.extend(subtokens)
            tockens.append("".join(subtokens))

    return tockens

def code_tokens(text: str) -> set[str]:
    """Tokens that look like codes: contain a digit (12756, ss304, k1, rr-13)."""
    return {tocken for tocken in tokenize(text) if len(tocken) >= 2 and any(char.isdigit() for char in tocken)}

def rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    """Reciprocal Rank Fusion (RRF) of multiple rankings.

    Args:
        rankings: List of rankings.
        k: The RRF parameter that controls the influence of lower-ranked documents.

    Returns:
        A fused ranking as a dictionary mapping chunk IDs to their fused scores.
    """
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, chunck_id in enumerate(ranking):
            scores[chunck_id] += 1 / (k + rank)

    return scores


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

@dataclass
class Hit:
    chunk_id: str
    text: str
    metadata: dict
    score: float                  
    distance: float              
    vector_rank: int | None
    bm25_rank: int | None


class Retriever:
    """Hybrid retriever: Chroma vectors + BM25, merged with Reciprocal Rank Fusion."""

    def __init__(self, collection: Collection):
        self.collection = collection
        data = collection.get(include=["documents", "metadatas"])
        self.ids: list[str] = data["ids"]
        self.text = dict(zip(data["ids"], data["documents"]))
        self.meta = dict(zip(data["ids"], data["metadatas"]))
        self.bm25 = BM25Okapi([tokenize(doc) for doc in data["documents"]])


    def _vector_search(self, qvec: list[float], n: int, source: str | None) -> tuple[list[str], dict[str, float]]:
        """Search Chroma vector store."""
        result = self.collection.query(
            query_embeddings=[qvec],
            n_results=n,
            where={"source": source} if source else None,
            include=["distances"]
        )

        ids = result["ids"][0]
        distances = dict(zip(ids, result["distances"][0]))
        return ids, distances

    def _bm25_search(self, query: str, n: int, source: str | None) -> list[str]:
        """Search BM25 index."""
        tokens = tokenize(query)
        scores = self.bm25.get_scores(tokens)
        ranked_ids = sorted(zip(self.ids, scores), key=lambda x: x[1], reverse=True)
        if source:
            ranked_ids = [(id_, score) for id_, score in ranked_ids if self.meta[id_].get("source") == source]
        return [id_ for id_, score in ranked_ids[:n]]

    def search(self, query: str, k: int | None = None, source: str | None = None,
               mode: str | None = None) -> list[Hit]:
        """Search for relevant chunks using specified retrieval."""
        k = k or settings.top_k
        candidate_k = settings.candidate_k
        mode = mode or settings.retrieval_mode
        query_vec = embed_query(query)

        vector_ids, distances = self._vector_search(query_vec, candidate_k, source)
        bm25_ids = self._bm25_search(query, candidate_k, source)


        rankings = {"vector": [vector_ids], "bm25": [bm25_ids], "hybrid": [vector_ids, bm25_ids]}[mode]

        scores = rrf(rankings, k=settings.rrf_k)
        top_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

        missing = [cid for cid in top_results if cid not in distances]
        if missing:
            got = self.col.get(ids=missing, include=["embeddings"])
            for cid, emb in zip(got["ids"], got["embeddings"]):
                distances[cid] = cosine_similarity(query_vec, emb)

        return [
            Hit(
                chunk_id=cid,
                text=self.text[cid],
                metadata=self.meta[cid],
                score=scores[cid],
                distance=distances[cid],
                vector_rank=vector_ids.index(cid) + 1 if cid in vector_ids else None,
                bm25_rank=bm25_ids.index(cid) + 1 if cid in bm25_ids else None
            )
            for cid, _ in top_results
            if distances[cid] <= settings.distance_threshold
        ]