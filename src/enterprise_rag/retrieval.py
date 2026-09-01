from __future__ import annotations

from .bm25 import BM25Index
from .embeddings import (
    HashingEmbeddingProvider,
    MiniLMEmbeddingProvider,
    cosine_similarity,
)
from .models import Chunk, SearchResult
from .qdrant_store import QdrantVectorStore
from .tokenize import tokenize


EmbeddingProvider = (
    HashingEmbeddingProvider
    | MiniLMEmbeddingProvider
)


def _normalize_nonnegative(
    values: list[float],
) -> list[float]:
    if not values:
        return []

    clipped = [
        max(0.0, value)
        for value in values
    ]
    maximum = max(clipped)

    if maximum == 0:
        return [0.0] * len(clipped)

    return [
        value / maximum
        for value in clipped
    ]


class HybridRetriever:
    """Offline baseline using in-memory vectors and BM25."""

    def __init__(
        self,
        chunks: list[Chunk],
        *,
        embedding_provider: (
            EmbeddingProvider | None
        ) = None,
        vector_weight: float = 0.70,
        bm25_weight: float = 0.30,
    ) -> None:
        if not chunks:
            raise ValueError(
                "chunks cannot be empty"
            )

        if (
            abs(
                vector_weight
                + bm25_weight
                - 1.0
            )
            > 1e-9
        ):
            raise ValueError(
                "retrieval weights must sum to 1.0"
            )

        self.chunks = chunks
        self.embedding_provider = (
            embedding_provider
            or HashingEmbeddingProvider()
        )
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight

        self.embeddings = (
            self.embedding_provider.embed_many(
                [
                    self._searchable_text(chunk)
                    for chunk in chunks
                ]
            )
        )
        self.bm25 = BM25Index(
            [
                tokenize(
                    self._searchable_text(chunk)
                )
                for chunk in chunks
            ]
        )

    @staticmethod
    def _searchable_text(
        chunk: Chunk,
    ) -> str:
        return (
            f"{chunk.title} "
            f"{chunk.section} "
            f"{chunk.department} "
            f"{chunk.text}"
        )

    def search(
        self,
        query: str,
        *,
        role: str,
        top_k: int = 3,
        strategy: str = "hybrid",
    ) -> list[SearchResult]:
        if not query.strip():
            raise ValueError(
                "query cannot be empty"
            )

        if not role.strip():
            raise ValueError(
                "role cannot be empty"
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be positive"
            )

        if strategy not in {
            "vector",
            "bm25",
            "hybrid",
        }:
            raise ValueError(
                "strategy must be vector, "
                "bm25, or hybrid"
            )

        authorized_indices = [
            index
            for index, chunk
            in enumerate(self.chunks)
            if chunk.is_authorized(role)
        ]

        if not authorized_indices:
            return []

        query_embedding = (
            self.embedding_provider.embed(
                query
            )
        )

        all_vector_scores = [
            cosine_similarity(
                query_embedding,
                embedding,
            )
            for embedding in self.embeddings
        ]
        all_bm25_scores = self.bm25.score(
            tokenize(query)
        )

        vector_raw = [
            all_vector_scores[index]
            for index in authorized_indices
        ]
        bm25_raw = [
            all_bm25_scores[index]
            for index in authorized_indices
        ]

        vector_normalized = (
            _normalize_nonnegative(
                vector_raw
            )
        )
        bm25_normalized = (
            _normalize_nonnegative(
                bm25_raw
            )
        )

        results: list[SearchResult] = []

        for (
            position,
            chunk_index,
        ) in enumerate(
            authorized_indices
        ):
            vector_score = (
                vector_normalized[position]
            )
            bm25_score = (
                bm25_normalized[position]
            )

            if strategy == "vector":
                combined = vector_score
            elif strategy == "bm25":
                combined = bm25_score
            else:
                combined = (
                    self.vector_weight
                    * vector_score
                    + self.bm25_weight
                    * bm25_score
                )

            results.append(
                SearchResult(
                    chunk=self.chunks[
                        chunk_index
                    ],
                    vector_score=vector_score,
                    bm25_score=bm25_score,
                    hybrid_score=combined,
                )
            )

        results.sort(
            key=lambda result: (
                -result.hybrid_score,
                result.chunk.chunk_id,
            )
        )

        return results[:top_k]


class QdrantHybridRetriever:
    """Production MiniLM, Qdrant and BM25 retrieval."""

    def __init__(
        self,
        chunks: list[Chunk],
        *,
        vector_store: QdrantVectorStore,
        embedding_provider: (
            MiniLMEmbeddingProvider
        ),
        vector_weight: float = 0.70,
        bm25_weight: float = 0.30,
        vector_candidate_k: int = 20,
    ) -> None:
        if not chunks:
            raise ValueError(
                "chunks cannot be empty"
            )

        if (
            abs(
                vector_weight
                + bm25_weight
                - 1.0
            )
            > 1e-9
        ):
            raise ValueError(
                "retrieval weights must sum to 1.0"
            )

        if vector_candidate_k <= 0:
            raise ValueError(
                "vector_candidate_k must be positive"
            )

        if (
            vector_store.dimensions
            != embedding_provider.dimensions
        ):
            raise ValueError(
                "embedding dimensions must match "
                "the Qdrant collection"
            )

        self.chunks = chunks
        self.vector_store = vector_store
        self.embedding_provider = (
            embedding_provider
        )
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.vector_candidate_k = (
            vector_candidate_k
        )

        self.bm25 = BM25Index(
            [
                tokenize(
                    self._searchable_text(chunk)
                )
                for chunk in chunks
            ]
        )

    @staticmethod
    def _searchable_text(
        chunk: Chunk,
    ) -> str:
        return (
            f"{chunk.title} "
            f"{chunk.section} "
            f"{chunk.department} "
            f"{chunk.text}"
        )

    @staticmethod
    def _chunk_key(
        chunk: Chunk,
    ) -> tuple[str, str, str]:
        return (
            chunk.document_id,
            chunk.version,
            chunk.chunk_id,
        )

    def search(
        self,
        query: str,
        *,
        role: str,
        top_k: int = 3,
        strategy: str = "hybrid",
    ) -> list[SearchResult]:
        if not query.strip():
            raise ValueError(
                "query cannot be empty"
            )

        if not role.strip():
            raise ValueError(
                "role cannot be empty"
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be positive"
            )

        if strategy not in {
            "vector",
            "bm25",
            "hybrid",
        }:
            raise ValueError(
                "strategy must be vector, "
                "bm25, or hybrid"
            )

        authorized_indices = [
            index
            for index, chunk
            in enumerate(self.chunks)
            if chunk.is_authorized(role)
        ]

        if not authorized_indices:
            return []

        all_bm25_scores = self.bm25.score(
            tokenize(query)
        )
        bm25_raw = [
            all_bm25_scores[index]
            for index in authorized_indices
        ]
        bm25_normalized = (
            _normalize_nonnegative(
                bm25_raw
            )
        )

        bm25_by_key = {
            self._chunk_key(
                self.chunks[chunk_index]
            ): bm25_normalized[position]
            for (
                position,
                chunk_index,
            ) in enumerate(
                authorized_indices
            )
        }

        vector_raw_by_key: dict[
            tuple[str, str, str],
            float,
        ] = {}

        vector_normalized_by_key: dict[
            tuple[str, str, str],
            float,
        ] = {}

        if strategy in {
            "vector",
            "hybrid",
        }:
            candidate_count = min(
                len(authorized_indices),
                max(
                    top_k,
                    self.vector_candidate_k,
                ),
            )

            vector_results = (
                self.vector_store.search(
                    query,
                    self.embedding_provider,
                    role=role,
                    top_k=candidate_count,
                )
            )

            vector_normalized = (
                _normalize_nonnegative(
                    [
                        result.vector_score
                        for result
                        in vector_results
                    ]
                )
            )

            vector_raw_by_key = {
                self._chunk_key(
                    result.chunk
                ): result.vector_score
                for result in vector_results
            }

            vector_normalized_by_key = {
                self._chunk_key(
                    result.chunk
                ): vector_normalized[
                    position
                ]
                for (
                    position,
                    result,
                ) in enumerate(
                    vector_results
                )
            }

        results: list[SearchResult] = []

        for chunk_index in authorized_indices:
            chunk = self.chunks[
                chunk_index
            ]
            key = self._chunk_key(chunk)

            vector_score = (
                vector_raw_by_key.get(
                    key,
                    0.0,
                )
            )
            vector_ranking_score = (
                vector_normalized_by_key.get(
                    key,
                    0.0,
                )
            )
            bm25_score = (
                bm25_by_key.get(
                    key,
                    0.0,
                )
            )

            if strategy == "vector":
                combined = (
                    vector_ranking_score
                )
            elif strategy == "bm25":
                combined = bm25_score
            else:
                combined = (
                    self.vector_weight
                    * vector_ranking_score
                    + self.bm25_weight
                    * bm25_score
                )

            results.append(
                SearchResult(
                    chunk=chunk,
                    vector_score=vector_score,
                    bm25_score=bm25_score,
                    hybrid_score=combined,
                )
            )

        results.sort(
            key=lambda result: (
                -result.hybrid_score,
                result.chunk.chunk_id,
            )
        )

        return results[:top_k]