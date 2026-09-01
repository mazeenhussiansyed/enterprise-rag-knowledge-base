from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from enterprise_rag import (  # noqa: E402
    EnterpriseRAGService,
    MiniLMEmbeddingProvider,
    QdrantHybridRetriever,
    QdrantVectorStore,
    load_chunks,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Ask the enterprise knowledge base and return a "
            "grounded answer with citations."
        )
    )
    parser.add_argument("query")
    parser.add_argument("--role", required=True)
    parser.add_argument(
        "--strategy",
        choices=("vector", "bm25", "hybrid"),
        default="hybrid",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=(
            PROJECT_ROOT
            / "data"
            / "corpus"
            / "chunks.jsonl"
        ),
    )
    parser.add_argument(
        "--qdrant-url",
        default="http://localhost:6333",
    )
    parser.add_argument(
        "--collection",
        default=QdrantVectorStore.DEFAULT_COLLECTION,
    )

    args = parser.parse_args()

    try:
        chunks = load_chunks(args.corpus)
        embedding_provider = MiniLMEmbeddingProvider()
        vector_store = QdrantVectorStore(
            url=args.qdrant_url,
            collection_name=args.collection,
        )
        retriever = QdrantHybridRetriever(
            chunks,
            vector_store=vector_store,
            embedding_provider=embedding_provider,
        )
        service = EnterpriseRAGService(
            retriever=retriever,
        )
        answer = service.ask(
            args.query,
            role=args.role,
            top_k=args.top_k,
            strategy=args.strategy,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"question failed: {exc}\n")

    print(json.dumps(asdict(answer), indent=2))


if __name__ == "__main__":
    main()