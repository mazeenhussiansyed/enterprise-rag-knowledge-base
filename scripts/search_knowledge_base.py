from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from enterprise_rag import (
    MiniLMEmbeddingProvider,
    QdrantHybridRetriever,
    QdrantVectorStore,
    load_chunks,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = PROJECT_ROOT / "data" / "corpus" / "chunks.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search the enterprise policy knowledge base."
    )
    parser.add_argument(
        "query",
        help="Natural-language question to search for.",
    )
    parser.add_argument(
        "--role",
        default="all_employees",
        help="Requester role used for access filtering.",
    )
    parser.add_argument(
        "--strategy",
        choices=("vector", "bm25", "hybrid"),
        default="hybrid",
        help="Retrieval strategy.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of evidence chunks to return.",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_CORPUS,
        help="Path to the chunked corpus.",
    )
    parser.add_argument(
        "--qdrant-url",
        default=os.getenv("QDRANT_URL", "http://localhost:6333"),
    )
    parser.add_argument(
        "--collection",
        default=os.getenv(
            "QDRANT_COLLECTION",
            QdrantVectorStore.DEFAULT_COLLECTION,
        ),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.top_k <= 0:
        raise ValueError("top-k must be positive")

    chunks = load_chunks(args.corpus)
    provider = MiniLMEmbeddingProvider()
    store = QdrantVectorStore(
        url=args.qdrant_url,
        collection_name=args.collection,
        dimensions=provider.dimensions,
    )

    if (
        args.strategy in {"vector", "hybrid"}
        and not store.client.collection_exists(store.collection_name)
    ):
        raise RuntimeError(
            "Qdrant collection does not exist. "
            "Run scripts/index_corpus_qdrant.py first."
        )

    retriever = QdrantHybridRetriever(
        chunks,
        vector_store=store,
        embedding_provider=provider,
        vector_weight=0.70,
        bm25_weight=0.30,
        vector_candidate_k=20,
    )

    results = retriever.search(
        args.query,
        role=args.role,
        top_k=args.top_k,
        strategy=args.strategy,
    )

    report = {
        "query": args.query,
        "role": args.role,
        "strategy": args.strategy,
        "result_count": len(results),
        "results": [
            {
                "rank": rank,
                "chunk_id": result.chunk.chunk_id,
                "document_id": result.chunk.document_id,
                "title": result.chunk.title,
                "section": result.chunk.section,
                "version": result.chunk.version,
                "effective_date": result.chunk.effective_date,
                "department": result.chunk.department,
                "source_file": result.chunk.source_file,
                "page_number": result.chunk.page_number,
                "vector_score": round(result.vector_score, 6),
                "bm25_score": round(result.bm25_score, 6),
                "hybrid_score": round(result.hybrid_score, 6),
                "evidence": result.chunk.text,
            }
            for rank, result in enumerate(results, start=1)
        ],
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()