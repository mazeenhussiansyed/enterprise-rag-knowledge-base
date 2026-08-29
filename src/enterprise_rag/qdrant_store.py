from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from .embeddings import MiniLMEmbeddingProvider
from .models import Chunk, SearchResult


class QdrantVectorStore:
    """Persistent vector storage and role-filtered semantic retrieval."""

    DEFAULT_COLLECTION = "enterprise_policy_chunks_v1"

    def __init__(
        self,
        *,
        url: str = "http://localhost:6333",
        collection_name: str = DEFAULT_COLLECTION,
        dimensions: int = 384,
        client: QdrantClient | None = None,
    ) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")

        self.url = url
        self.collection_name = collection_name
        self.dimensions = dimensions
        self.client = client or QdrantClient(url=url)

    def ensure_collection(self) -> bool:
        """Create the collection and payload indexes when they do not exist."""

        if self.client.collection_exists(self.collection_name):
            return False

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.dimensions,
                distance=models.Distance.COSINE,
            ),
        )

        for field_name in (
            "roles",
            "chunk_id",
            "document_id",
            "department",
            "version",
        ):
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field_name,
                field_schema=models.PayloadSchemaType.KEYWORD,
                wait=True,
            )

        return True

    def upsert_chunks(
        self,
        chunks: list[Chunk],
        embedding_provider: MiniLMEmbeddingProvider,
        *,
        batch_size: int = 32,
    ) -> int:
        """Generate MiniLM vectors and idempotently store document chunks."""

        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if embedding_provider.dimensions != self.dimensions:
            raise ValueError(
                "embedding dimensions must match the Qdrant collection"
            )
        if not chunks:
            return 0

        self.ensure_collection()

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            texts = [self._searchable_text(chunk) for chunk in batch]
            vectors = embedding_provider.embed_many(texts)

            points = [
                models.PointStruct(
                    id=self._point_id(chunk),
                    vector=vector,
                    payload=self._payload(chunk),
                )
                for chunk, vector in zip(batch, vectors)
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True,
            )

        return len(chunks)

    def search(
        self,
        query: str,
        embedding_provider: MiniLMEmbeddingProvider,
        *,
        role: str,
        top_k: int = 3,
    ) -> list[SearchResult]:
        """Run semantic search with authorization enforced by Qdrant."""

        if not query.strip():
            raise ValueError("query cannot be empty")
        if not role.strip():
            raise ValueError("role cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        query_vector = embedding_provider.embed(query)
        authorization_filter = models.Filter(
            should=[
                models.FieldCondition(
                    key="roles",
                    match=models.MatchValue(value="all"),
                ),
                models.FieldCondition(
                    key="roles",
                    match=models.MatchValue(value=role),
                ),
            ]
        )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=authorization_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )

        results: list[SearchResult] = []
        for point in response.points:
            if point.payload is None:
                continue

            score = float(point.score)
            results.append(
                SearchResult(
                    chunk=self._chunk_from_payload(point.payload),
                    vector_score=score,
                    bm25_score=0.0,
                    hybrid_score=score,
                )
            )

        return results

    def count(self) -> int:
        """Return the exact number of stored chunks."""

        result = self.client.count(
            collection_name=self.collection_name,
            exact=True,
        )
        return int(result.count)

    @staticmethod
    def _searchable_text(chunk: Chunk) -> str:
        return f"{chunk.title} {chunk.section} {chunk.department} {chunk.text}"

    @staticmethod
    def _point_id(chunk: Chunk) -> str:
        identity = f"{chunk.document_id}:{chunk.version}:{chunk.chunk_id}"
        return str(uuid5(NAMESPACE_URL, f"enterprise-rag:{identity}"))

    @staticmethod
    def _payload(chunk: Chunk) -> dict[str, object]:
        return {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "title": chunk.title,
            "section": chunk.section,
            "department": chunk.department,
            "version": chunk.version,
            "effective_date": chunk.effective_date,
            "roles": list(chunk.roles),
            "text": chunk.text,
            "page_number": chunk.page_number,
            "source_file": chunk.source_file,
            "checksum": chunk.checksum,
            "char_start": chunk.char_start,
            "char_end": chunk.char_end,
        }

    @staticmethod
    def _chunk_from_payload(payload: dict[str, object]) -> Chunk:
        roles_value = payload["roles"]
        if not isinstance(roles_value, list):
            raise ValueError("Qdrant payload roles must be a list")

        page_value = payload.get("page_number")

        return Chunk(
            chunk_id=str(payload["chunk_id"]),
            document_id=str(payload["document_id"]),
            title=str(payload["title"]),
            section=str(payload["section"]),
            department=str(payload["department"]),
            version=str(payload["version"]),
            effective_date=str(payload["effective_date"]),
            roles=tuple(str(role) for role in roles_value),
            text=str(payload["text"]),
            page_number=int(page_value) if page_value is not None else None,
            source_file=str(payload.get("source_file", "")),
            checksum=str(payload.get("checksum", "")),
            char_start=int(payload.get("char_start", 0)),
            char_end=int(payload.get("char_end", 0)),
        )