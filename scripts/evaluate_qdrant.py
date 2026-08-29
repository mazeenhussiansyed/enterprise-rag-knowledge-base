from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from enterprise_rag import (  # noqa: E402
    MiniLMEmbeddingProvider,
    QdrantHybridRetriever,
    QdrantVectorStore,
    load_chunks,
    load_questions,
)


def evaluate(retriever, questions, strategy: str) -> dict:
    hit_at_1 = 0
    hit_at_3 = 0
    reciprocal_ranks: list[float] = []
    latencies_ms: list[float] = []
    failures: list[dict] = []

    for question in questions:
        started = time.perf_counter()
        results = retriever.search(
            question.query,
            role=question.role,
            top_k=3,
            strategy=strategy,
        )
        latencies_ms.append((time.perf_counter() - started) * 1000.0)
        ranked_ids = [result.chunk.chunk_id for result in results]

        if ranked_ids and ranked_ids[0] == question.expected_chunk_id:
            hit_at_1 += 1

        if question.expected_chunk_id in ranked_ids:
            hit_at_3 += 1
            rank = ranked_ids.index(question.expected_chunk_id) + 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)
            failures.append(
                {
                    "question_id": question.question_id,
                    "expected": question.expected_chunk_id,
                    "retrieved": ranked_ids,
                }
            )

    total = len(questions)
    sorted_latencies = sorted(latencies_ms)
    p95_index = max(
        0,
        min(
            len(sorted_latencies) - 1,
            round(0.95 * len(sorted_latencies)) - 1,
        ),
    )

    return {
        "strategy": strategy,
        "questions": total,
        "hit_at_1": round(hit_at_1 / total, 4),
        "hit_at_3": round(hit_at_3 / total, 4),
        "mrr": round(sum(reciprocal_ranks) / total, 4),
        "median_latency_ms": round(statistics.median(latencies_ms), 3),
        "p95_latency_ms": round(sorted_latencies[p95_index], 3),
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate production MiniLM, Qdrant and BM25 retrieval."
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=PROJECT_ROOT / "data" / "corpus" / "chunks.jsonl",
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=PROJECT_ROOT / "data" / "evaluation" / "questions.jsonl",
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
    args = parser.parse_args()

    chunks = load_chunks(args.corpus)
    questions = load_questions(args.questions)

    if not chunks:
        raise ValueError("corpus chunks cannot be empty")
    if not questions:
        raise ValueError("evaluation questions cannot be empty")

    provider = MiniLMEmbeddingProvider()
    store = QdrantVectorStore(
        url=args.qdrant_url,
        collection_name=args.collection,
        dimensions=provider.dimensions,
    )

    if not store.client.collection_exists(store.collection_name):
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

    # Warm up ONNX inference and the Qdrant connection before timing.
    retriever.search(
        questions[0].query,
        role=questions[0].role,
        top_k=1,
        strategy="hybrid",
    )

    report = {
        "benchmark_version": "v1",
        "embedding_model": provider.model_name,
        "embedding_dimensions": provider.dimensions,
        "vector_database": "qdrant",
        "collection": store.collection_name,
        "stored_points": store.count(),
        "corpus_chunks": len(chunks),
        "evaluation_questions": len(questions),
        "vector_weight": 0.70,
        "bm25_weight": 0.30,
        "vector_candidate_k": 20,
        "warmup_queries": 1,
        "results": [
            evaluate(retriever, questions, strategy)
            for strategy in ("vector", "bm25", "hybrid")
        ],
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()