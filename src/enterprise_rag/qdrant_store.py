from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from .embeddings import MiniLMEmbeddingProvider
from .models import Chunk, SearchResult


class QdrantVectorStore:
    """Persistent vector storage with governed, role-filtered retrieval."""

    DEFAULT_COLLECTION = "enterprise_policy_chunks_v1"

    PAYLOAD_INDEXES = {
        "roles": models.PayloadSchemaType.KEYWORD,
        "chunk_id": models.PayloadSchemaType.KEYWORD,
        "document_id": models.PayloadSchemaType.KEYWORD,
        "department": models.PayloadSchemaType.KEYWORD,
        "version": models.PayloadSchemaType.KEYWORD,
        "status": models.PayloadSchemaType.KEYWORD,
        "active": models.PayloadSchemaType.BOOL,
        "sync_run_id": models.PayloadSchemaType.KEYWORD,
    }

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
        """Create the collection and any missing payload indexes."""

        collection_created = False

        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.dimensions,
                    distance=models.Distance.COSINE,
                ),
            )
            collection_created = True

        collection_info = self.client.get_collection(self.collection_name)
        existing_indexes = set((collection_info.payload_schema or {}).keys())

        for field_name, field_schema in self.PAYLOAD_INDEXES.items():
            if field_name in existing_indexes:
                continue

            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field_name,
                field_schema=field_schema,
                wait=True,
            )

        return collection_created

    def upsert_chunks(
        self,
        chunks: list[Chunk],
        embedding_provider: MiniLMEmbeddingProvider,
        *,
        batch_size: int = 32,
        status: str = "active",
        active: bool = True,
        sync_run_id: str | None = None,
    ) -> int:
        """Generate embeddings and idempotently store governed chunks."""

        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if embedding_provider.dimensions != self.dimensions:
            raise ValueError(
                "embedding dimensions must match the Qdrant collection"
            )
        if not status.strip():
            raise ValueError("status cannot be empty")
        if sync_run_id is not None and not sync_run_id.strip():
            raise ValueError("sync_run_id cannot be empty")
        if not chunks:
            return 0

        self.ensure_collection()
        indexed_at = datetime.now(timezone.utc).isoformat()

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            texts = [self._searchable_text(chunk) for chunk in batch]
            vectors = embedding_provider.embed_many(texts)

            points = [
                models.PointStruct(
                    id=self._point_id(chunk),
                    vector=vector,
                    payload=self._payload(
                        chunk,
                        status=status,
                        active=active,
                        sync_run_id=sync_run_id,
                        indexed_at=indexed_at,
                    ),
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
        department: str | None = None,
        version: str | None = None,
        document_id: str | None = None,
        status: str | None = "active",
        active_only: bool = True,
    ) -> list[SearchResult]:
        """Search only evidence allowed by governance and role filters."""

        if not query.strip():
            raise ValueError("query cannot be empty")
        if not role.strip():
            raise ValueError("role cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        optional_values = {
            "department": department,
            "version": version,
            "document_id": document_id,
            "status": status,
        }
        for name, value in optional_values.items():
            if value is not None and not value.strip():
                raise ValueError(f"{name} cannot be empty")

        must_conditions = []

        if active_only:
            must_conditions.append(
                models.FieldCondition(
                    key="active",
                    match=models.MatchValue(value=True),
                )
            )

        if status is not None:
            must_conditions.append(
                models.FieldCondition(
                    key="status",
                    match=models.MatchValue(value=status),
                )
            )

        for field_name, value in (
            ("department", department),
            ("version", version),
            ("document_id", document_id),
        ):
            if value is not None:
                must_conditions.append(
                    models.FieldCondition(
                        key=field_name,
                        match=models.MatchValue(value=value),
                    )
                )

        authorization_filter = models.Filter(
            must=must_conditions,
            should=[
                models.FieldCondition(
                    key="roles",
                    match=models.MatchValue(value="all"),
                ),
                models.FieldCondition(
                    key="roles",
                    match=models.MatchValue(value=role),
                ),
            ],
        )

        query_vector = embedding_provider.embed(query)
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

    def set_document_version_state(
        self,
        document_id: str,
        version: str,
        *,
        active: bool,
        status: str | None = None,
        sync_run_id: str | None = None,
    ) -> int:
        """Update governance state for one stored document version."""

        if not document_id.strip():
            raise ValueError("document_id cannot be empty")
        if not version.strip():
            raise ValueError("version cannot be empty")
        if status is not None and not status.strip():
            raise ValueError("status cannot be empty")
        if sync_run_id is not None and not sync_run_id.strip():
            raise ValueError("sync_run_id cannot be empty")

        selector = self._document_version_filter(document_id, version)
        matched_points = self.count(selector)

        if matched_points == 0:
            return 0

        payload: dict[str, object] = {
            "active": active,
            "governance_updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if status is not None:
            payload["status"] = status
        if sync_run_id is not None:
            payload["sync_run_id"] = sync_run_id

        self.client.set_payload(
            collection_name=self.collection_name,
            payload=payload,
            points=selector,
            wait=True,
        )
        return matched_points

    def deactivate_other_versions(
        self,
        document_id: str,
        keep_version: str,
        *,
        sync_run_id: str | None = None,
    ) -> int:
        """Deactivate every stored version except the selected version."""

        if not document_id.strip():
            raise ValueError("document_id cannot be empty")
        if not keep_version.strip():
            raise ValueError("keep_version cannot be empty")
        if sync_run_id is not None and not sync_run_id.strip():
            raise ValueError("sync_run_id cannot be empty")

        selector = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id),
                )
            ],
            must_not=[
                models.FieldCondition(
                    key="version",
                    match=models.MatchValue(value=keep_version),
                )
            ],
        )
        matched_points = self.count(selector)

        if matched_points == 0:
            return 0

        payload: dict[str, object] = {
            "active": False,
            "governance_updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if sync_run_id is not None:
            payload["sync_run_id"] = sync_run_id

        self.client.set_payload(
            collection_name=self.collection_name,
            payload=payload,
            points=selector,
            wait=True,
        )
        return matched_points

    def count(self, count_filter: models.Filter | None = None) -> int:
        """Return the exact number of stored chunks matching a filter."""

        result = self.client.count(
            collection_name=self.collection_name,
            count_filter=count_filter,
            exact=True,
        )
        return int(result.count)

    def count_document_version(self, document_id: str, version: str) -> int:
        """Count points belonging to a specific document version."""

        return self.count(self._document_version_filter(document_id, version))

    @staticmethod
    def _document_version_filter(
        document_id: str,
        version: str,
    ) -> models.Filter:
        return models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id),
                ),
                models.FieldCondition(
                    key="version",
                    match=models.MatchValue(value=version),
                ),
            ]
        )

    @staticmethod
    def _searchable_text(chunk: Chunk) -> str:
        return f"{chunk.title} {chunk.section} {chunk.department} {chunk.text}"

    @staticmethod
    def _point_id(chunk: Chunk) -> str:
        identity = f"{chunk.document_id}:{chunk.version}:{chunk.chunk_id}"
        return str(uuid5(NAMESPACE_URL, f"enterprise-rag:{identity}"))

    @staticmethod
    def _payload(
        chunk: Chunk,
        *,
        status: str,
        active: bool,
        sync_run_id: str | None,
        indexed_at: str,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "title": chunk.title,
            "section": chunk.section,
            "department": chunk.department,
            "version": chunk.version,
            "effective_date": chunk.effective_date,
            "roles": list(chunk.roles),
            "status": status,
            "active": active,
            "text": chunk.text,
            "page_number": chunk.page_number,
            "source_file": chunk.source_file,
            "checksum": chunk.checksum,
            "char_start": chunk.char_start,
            "char_end": chunk.char_end,
            "indexed_at": indexed_at,
        }

        if sync_run_id is not None:
            payload["sync_run_id"] = sync_run_id

        return payload

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