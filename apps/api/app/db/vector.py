"""Vector store client for semantic similarity search.

Provides two implementations:
- ``OpenAIEmbeddingStore`` — uses ``text-embedding-3-small`` for real
  semantic similarity (requires ``USE_OPENAI=true`` and an API key).
- ``InMemoryVectorStore`` — cosine similarity over TF-IDF-style bag-of-words
  vectors; zero-dependency fallback for offline / test use.

Call ``build_vector_store(settings)`` to get the right one automatically.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    doc_id: str
    text: str
    embedding: list[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# OpenAI embedding store
# ---------------------------------------------------------------------------

class OpenAIEmbeddingStore:
    """Semantic vector store backed by OpenAI text-embedding-3-small.

    Embeddings are stored in memory (replace with pgvector for production).
    """

    MODEL = "text-embedding-3-small"

    def __init__(self, api_key: str) -> None:
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key)
        self._docs: dict[str, VectorDocument] = {}

    def add(self, doc: VectorDocument) -> None:
        if not doc.embedding:
            doc.embedding = self._embed(doc.text)
        self._docs[doc.doc_id] = doc

    def delete(self, doc_id: str) -> None:
        self._docs.pop(doc_id, None)

    def similarity_search(self, query: str, top_k: int = 5) -> list[tuple[VectorDocument, float]]:
        if not self._docs:
            return []
        query_vec = self._embed(query)
        scored = [
            (doc, self._cosine(query_vec, doc.embedding))
            for doc in self._docs.values()
            if doc.embedding
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def _embed(self, text: str) -> list[float]:
        try:
            response = self._client.embeddings.create(
                model=self.MODEL,
                input=text[:8000],  # token limit guard
            )
            return response.data[0].embedding
        except Exception as exc:
            logger.warning("OpenAI embedding failed: %s", exc)
            return []

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# In-memory keyword fallback
# ---------------------------------------------------------------------------

class InMemoryVectorStore:
    """Keyword-overlap cosine similarity — zero dependencies, offline-safe."""

    def __init__(self) -> None:
        self._docs: dict[str, VectorDocument] = {}

    def add(self, doc: VectorDocument) -> None:
        self._docs[doc.doc_id] = doc

    def delete(self, doc_id: str) -> None:
        self._docs.pop(doc_id, None)

    def similarity_search(self, query: str, top_k: int = 5) -> list[tuple[VectorDocument, float]]:
        query_vec = self._to_vec(query)
        scored: list[tuple[VectorDocument, float]] = []
        for doc in self._docs.values():
            doc_vec = self._to_vec(doc.text)
            score = self._cosine(query_vec, doc_vec)
            if score > 0:
                scored.append((doc, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _to_vec(text: str) -> dict[str, float]:
        tokens = text.lower().split()
        vec: dict[str, float] = {}
        for token in tokens:
            vec[token] = vec.get(token, 0.0) + 1.0
        return vec

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        dot = sum(a.get(k, 0.0) * v for k, v in b.items())
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_vector_store(settings=None) -> OpenAIEmbeddingStore | InMemoryVectorStore:
    """Return the best available vector store given current settings."""
    if settings and getattr(settings, "use_openai", False) and getattr(settings, "openai_api_key", None):
        logger.info("Using OpenAI text-embedding-3-small vector store")
        return OpenAIEmbeddingStore(api_key=settings.openai_api_key)
    logger.info("Using in-memory keyword vector store (set USE_OPENAI=true for semantic search)")
    return InMemoryVectorStore()


# Default singleton (keyword mode) — replaced by deps.py when settings are available
vector_store: InMemoryVectorStore | OpenAIEmbeddingStore = InMemoryVectorStore()

