from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from time import perf_counter

from enterprise_rag import (
    MiniLMEmbeddingProvider,
    QdrantVectorStore,
    load_chunks,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "data" / "corpus" / "chunks.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Embed the enterprise corpus and index it in Qdrant."
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_CORPUS,
        help="Path to the chunked JSONL corpus.",
    )
    parser.add_argument(
        "--qdrant-url",
        default=os.getenv("QDRANT_URL", "http://localhost:6333"),
        help="Qdrant server URL.",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv(
            "QDRANT_COLLECTION",
            QdrantVectorStore.DEFAULT_COLLECTION,
        ),
        help="Qdrant collection name.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Embedding and upload batch size.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if not args.corpus.exists():
        raise FileNotFoundError(f"Corpus not found: {args.corpus}")
    if args.batch_size <= 0:
        raise ValueError("batch size must be positive")

    chunks = load_chunks(args.corpus)
    provider = MiniLMEmbeddingProvider()
    store = QdrantVectorStore(
        url=args.qdrant_url,
        collection_name=args.collection,
        dimensions=provider.dimensions,
    )

    started = perf_counter()
    collection_created = store.ensure_collection()
    indexed_chunks = store.upsert_chunks(
        chunks,
        provider,
        batch_size=args.batch_size,
    )
    elapsed_seconds = perf_counter() - started

    report = {
        "status": "indexed",
        "collection": store.collection_name,
        "collection_created": collection_created,
        "embedding_model": provider.model_name,
        "embedding_dimensions": provider.dimensions,
        "input_chunks": len(chunks),
        "indexed_chunks": indexed_chunks,
        "stored_points": store.count(),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "chunks_per_second": round(
            indexed_chunks / elapsed_seconds,
            2,
        )
        if elapsed_seconds > 0
        else None,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()