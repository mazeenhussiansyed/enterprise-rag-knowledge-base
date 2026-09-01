from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Literal

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from .answering import ExtractiveAnswerGenerator
from .corpus import load_chunks
from .embeddings import MiniLMEmbeddingProvider
from .models import Chunk, SearchResult
from .qdrant_store import QdrantVectorStore
from .retrieval import QdrantHybridRetriever


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS_PATH = PROJECT_ROOT / "data" / "corpus" / "chunks.jsonl"


class RetrievalRequest(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=1000,
        description="Natural-language enterprise policy question.",
    )
    role: str = Field(
        min_length=1,
        max_length=128,
        description="Requesting user's resolved enterprise role.",
    )
    strategy: Literal["vector", "bm25", "hybrid"] = "hybrid"
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of evidence chunks to return.",
    )

    @field_validator("query", "role")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError("value cannot be blank")

        return normalized


@dataclass
class EnterpriseRAGRuntime:
    chunks: list[Chunk]
    provider: MiniLMEmbeddingProvider
    store: QdrantVectorStore
    retriever: QdrantHybridRetriever
    generator: ExtractiveAnswerGenerator


RuntimeFactory = Callable[[], EnterpriseRAGRuntime]


def build_runtime() -> EnterpriseRAGRuntime:
    """Build the live local runtime after Qdrant is available."""

    chunks = load_chunks(DEFAULT_CORPUS_PATH)
    provider = MiniLMEmbeddingProvider()
    store = QdrantVectorStore()

    if not store.client.collection_exists(store.collection_name):
        raise RuntimeError(
            "Qdrant collection does not exist. "
            "Run: python scripts/index_corpus_qdrant.py"
        )

    stored_points = store.count()

    if stored_points == 0:
        raise RuntimeError(
            "Qdrant collection is empty. "
            "Run: python scripts/index_corpus_qdrant.py"
        )

    retriever = QdrantHybridRetriever(
        chunks,
        vector_store=store,
        embedding_provider=provider,
    )
    generator = ExtractiveAnswerGenerator()

    return EnterpriseRAGRuntime(
        chunks=chunks,
        provider=provider,
        store=store,
        retriever=retriever,
        generator=generator,
    )


@asynccontextmanager
async def application_lifespan(app: FastAPI):
    runtime_factory: RuntimeFactory = app.state.runtime_factory
    runtime = runtime_factory()
    app.state.runtime = runtime

    try:
        yield
    finally:
        client = getattr(runtime.store, "client", None)
        close = getattr(client, "close", None)

        if callable(close):
            close()


def get_runtime(request: Request) -> EnterpriseRAGRuntime:
    runtime = getattr(request.app.state, "runtime", None)

    if runtime is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise RAG runtime is not ready.",
        )

    return runtime


def serialize_search_result(
    result: SearchResult,
    rank: int,
) -> dict[str, object]:
    chunk = result.chunk

    return {
        "rank": rank,
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "title": chunk.title,
        "section": chunk.section,
        "department": chunk.department,
        "version": chunk.version,
        "effective_date": chunk.effective_date,
        "roles": list(chunk.roles),
        "source_file": chunk.source_file,
        "page_number": chunk.page_number,
        "vector_score": round(result.vector_score, 6),
        "bm25_score": round(result.bm25_score, 6),
        "hybrid_score": round(result.hybrid_score, 6),
        "evidence": chunk.text,
    }


def create_app(
    runtime_factory: RuntimeFactory = build_runtime,
) -> FastAPI:
    app = FastAPI(
        title="Enterprise Policy RAG API",
        version="0.6.0",
        description=(
            "Evidence-first policy search with role-aware retrieval, "
            "citations, and safe refusals."
        ),
        lifespan=application_lifespan,
    )
    app.state.runtime_factory = runtime_factory

    @app.get(
        "/",
        tags=["service"],
        summary="Describe the Enterprise Policy RAG service.",
    )
    async def root() -> dict[str, str]:
        return {
            "service": "enterprise-policy-rag",
            "docs": "/docs",
            "health": "/health",
            "search": "/search",
            "ask": "/ask",
        }

    @app.get(
        "/health",
        tags=["service"],
        summary="Check local Qdrant-backed service health.",
    )
    async def health(
        runtime: EnterpriseRAGRuntime = Depends(get_runtime),
    ) -> dict[str, object]:
        try:
            stored_points = runtime.store.count()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Qdrant health check failed: {exc}",
            ) from exc

        return {
            "status": "ok",
            "collection": runtime.store.collection_name,
            "stored_points": stored_points,
            "corpus_chunks": len(runtime.chunks),
            "embedding_model": runtime.provider.model_name,
        }

    @app.get(
        "/stats",
        tags=["service"],
        summary="Return local corpus and vector-store statistics.",
    )
    async def stats(
        runtime: EnterpriseRAGRuntime = Depends(get_runtime),
    ) -> dict[str, object]:
        try:
            stored_points = runtime.store.count()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Qdrant statistics check failed: {exc}",
            ) from exc

        return {
            "collection": runtime.store.collection_name,
            "stored_points": stored_points,
            "corpus_chunks": len(runtime.chunks),
            "embedding_model": runtime.provider.model_name,
            "vector_weight": runtime.retriever.vector_weight,
            "bm25_weight": runtime.retriever.bm25_weight,
            "vector_candidate_k": runtime.retriever.vector_candidate_k,
        }

    @app.post(
        "/search",
        tags=["retrieval"],
        summary="Return role-filtered evidence chunks.",
    )
    async def search(
        payload: RetrievalRequest,
        runtime: EnterpriseRAGRuntime = Depends(get_runtime),
    ) -> dict[str, object]:
        try:
            results = runtime.retriever.search(
                payload.query,
                role=payload.role,
                strategy=payload.strategy,
                top_k=payload.top_k,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Retrieval failed: {exc}",
            ) from exc

        return {
            "query": payload.query,
            "role": payload.role,
            "strategy": payload.strategy,
            "result_count": len(results),
            "results": [
                serialize_search_result(result, rank)
                for rank, result in enumerate(results, start=1)
            ],
        }

    @app.post(
        "/ask",
        tags=["answers"],
        summary="Return a citation-backed answer or a safe refusal.",
    )
    async def ask(
        payload: RetrievalRequest,
        runtime: EnterpriseRAGRuntime = Depends(get_runtime),
    ) -> dict[str, object]:
        try:
            results = runtime.retriever.search(
                payload.query,
                role=payload.role,
                strategy=payload.strategy,
                top_k=payload.top_k,
            )
            answer = runtime.generator.generate(
                payload.query,
                payload.role,
                results,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Answer generation failed: {exc}",
            ) from exc

        return asdict(answer)

    return app


app = create_app()