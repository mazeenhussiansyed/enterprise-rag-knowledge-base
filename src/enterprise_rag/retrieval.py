from __future__ import annotations

from .bm25 import BM25Index
from .embeddings import HashingEmbeddingProvider, cosine_similarity
from .models import Chunk, SearchResult
from .tokenize import tokenize


def _normalize_nonnegative(values: list[float]) -> list[float]:
    if not values:
        return []
    clipped = [max(0.0, value) for value in values]
    maximum = max(clipped)
    if maximum == 0:
        return [0.0] * len(clipped)
    return [value / maximum for value in clipped]


class HybridRetriever:
    def __init__(
        self,
        chunks: list[Chunk],
        *,
        embedding_provider: HashingEmbeddingProvider | None = None,
        vector_weight: float = 0.70,
        bm25_weight: float = 0.30,
    ) -> None:
        if not chunks:
            raise ValueError("chunks cannot be empty")
        if abs(vector_weight + bm25_weight - 1.0) > 1e-9:
            raise ValueError("retrieval weights must sum to 1.0")

        self.chunks = chunks
        self.embedding_provider = embedding_provider or HashingEmbeddingProvider()
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.embeddings = self.embedding_provider.embed_many(
            [self._searchable_text(chunk) for chunk in chunks]
        )
        self.bm25 = BM25Index([tokenize(self._searchable_text(chunk)) for chunk in chunks])

    @staticmethod
    def _searchable_text(chunk: Chunk) -> str:
        return f"{chunk.title} {chunk.section} {chunk.department} {chunk.text}"

    def search(
        self,
        query: str,
        *,
        role: str,
        top_k: int = 3,
        strategy: str = "hybrid",
    ) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if strategy not in {"vector", "bm25", "hybrid"}:
            raise ValueError("strategy must be vector, bm25, or hybrid")

        # Authorization is applied before scoring and ranking.
        authorized_indices = [
            index for index, chunk in enumerate(self.chunks) if chunk.is_authorized(role)
        ]
        if not authorized_indices:
            return []

        query_embedding = self.embedding_provider.embed(query)
        all_vector_scores = [
            cosine_similarity(query_embedding, embedding) for embedding in self.embeddings
        ]
        all_bm25_scores = self.bm25.score(tokenize(query))

        vector_raw = [all_vector_scores[index] for index in authorized_indices]
        bm25_raw = [all_bm25_scores[index] for index in authorized_indices]
        vector_normalized = _normalize_nonnegative(vector_raw)
        bm25_normalized = _normalize_nonnegative(bm25_raw)

        results: list[SearchResult] = []
        for position, chunk_index in enumerate(authorized_indices):
            vector_score = vector_normalized[position]
            bm25_score = bm25_normalized[position]
            if strategy == "vector":
                combined = vector_score
            elif strategy == "bm25":
                combined = bm25_score
            else:
                combined = (
                    self.vector_weight * vector_score
                    + self.bm25_weight * bm25_score
                )
            results.append(
                SearchResult(
                    chunk=self.chunks[chunk_index],
                    vector_score=vector_score,
                    bm25_score=bm25_score,
                    hybrid_score=combined,
                )
            )

        results.sort(key=lambda result: (-result.hybrid_score, result.chunk.chunk_id))
        return results[:top_k]
