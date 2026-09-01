from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from enterprise_rag.answering import ExtractiveAnswerGenerator
from enterprise_rag.corpus import load_chunks, load_questions
from enterprise_rag.embeddings import MiniLMEmbeddingProvider
from enterprise_rag.qdrant_store import QdrantVectorStore
from enterprise_rag.retrieval import QdrantHybridRetriever


def load_refusal_questions(path: Path) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSON in {path}:{line_number}"
                ) from exc

            required_fields = (
                "question_id",
                "query",
                "role",
                "expected_status",
            )
            missing_fields = [
                field
                for field in required_fields
                if not isinstance(row.get(field), str) or not row[field].strip()
            ]

            if missing_fields:
                missing_text = ", ".join(missing_fields)
                raise ValueError(
                    f"missing required fields in {path}:{line_number}: "
                    f"{missing_text}"
                )

            questions.append(
                {
                    "question_id": row["question_id"],
                    "query": row["query"],
                    "role": row["role"],
                    "expected_status": row["expected_status"],
                }
            )

    if not questions:
        raise ValueError(f"no refusal questions found in {path}")

    return questions


def percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = max(0, math.ceil(0.95 * len(sorted_values)) - 1)
    return sorted_values[index]


def ask_question(
    retriever: QdrantHybridRetriever,
    generator: ExtractiveAnswerGenerator,
    *,
    query: str,
    role: str,
    strategy: str,
    top_k: int,
):
    started = time.perf_counter()

    results = retriever.search(
        query,
        role=role,
        strategy=strategy,
        top_k=top_k,
    )
    answer = generator.generate(
        query,
        role,
        results,
    )

    latency_ms = (time.perf_counter() - started) * 1000.0
    return answer, latency_ms


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate grounded answers, citation coverage, and safe refusals "
            "against the Enterprise RAG benchmark."
        )
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
        "--refusals",
        type=Path,
        default=(
            PROJECT_ROOT
            / "data"
            / "evaluation"
            / "refusal_questions.jsonl"
        ),
    )
    parser.add_argument(
        "--collection",
        default=QdrantVectorStore.DEFAULT_COLLECTION,
    )
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
    args = parser.parse_args()

    if args.top_k <= 0:
        parser.error("--top-k must be positive")

    chunks = load_chunks(args.corpus)
    answerable_questions = load_questions(args.questions)
    refusal_questions = load_refusal_questions(args.refusals)

    provider = MiniLMEmbeddingProvider()
    store = QdrantVectorStore(collection_name=args.collection)

    if not store.client.collection_exists(store.collection_name):
        parser.error(
            f"Qdrant collection does not exist: {store.collection_name}. "
            "Run python scripts/index_corpus_qdrant.py first."
        )

    retriever = QdrantHybridRetriever(
        chunks,
        vector_store=store,
        embedding_provider=provider,
    )
    generator = ExtractiveAnswerGenerator()

    warmup_question = answerable_questions[0]
    ask_question(
        retriever,
        generator,
        query=warmup_question.query,
        role=warmup_question.role,
        strategy=args.strategy,
        top_k=args.top_k,
    )

    answerable_rows: list[dict[str, object]] = []
    refusal_rows: list[dict[str, object]] = []
    latencies_ms: list[float] = []

    answered_count = 0
    expected_citation_count = 0
    cited_answer_count = 0

    for question in answerable_questions:
        answer, latency_ms = ask_question(
            retriever,
            generator,
            query=question.query,
            role=question.role,
            strategy=args.strategy,
            top_k=args.top_k,
        )
        latencies_ms.append(latency_ms)

        citation_ids = [
            citation.chunk_id
            for citation in answer.citations
        ]
        answered = answer.status == "answered"
        expected_citation_found = (
            question.expected_chunk_id in citation_ids
        )

        if answered:
            answered_count += 1

        if answer.citations:
            cited_answer_count += 1

        if expected_citation_found:
            expected_citation_count += 1

        answerable_rows.append(
            {
                "question_id": question.question_id,
                "status": answer.status,
                "reason": answer.reason,
                "expected_chunk_id": question.expected_chunk_id,
                "citation_chunk_ids": citation_ids,
                "expected_citation_found": expected_citation_found,
                "confidence": answer.confidence,
                "latency_ms": round(latency_ms, 3),
            }
        )

    refused_count = 0
    unsafe_answer_count = 0

    for question in refusal_questions:
        answer, latency_ms = ask_question(
            retriever,
            generator,
            query=question["query"],
            role=question["role"],
            strategy=args.strategy,
            top_k=args.top_k,
        )
        latencies_ms.append(latency_ms)

        refused = answer.status == "refused"

        if refused:
            refused_count += 1
        else:
            unsafe_answer_count += 1

        refusal_rows.append(
            {
                "question_id": question["question_id"],
                "status": answer.status,
                "reason": answer.reason,
                "citation_count": len(answer.citations),
                "confidence": answer.confidence,
                "latency_ms": round(latency_ms, 3),
            }
        )

    answerable_total = len(answerable_questions)
    refusal_total = len(refusal_questions)
    total_questions = answerable_total + refusal_total

    report = {
        "evaluation_name": "m05_grounded_answer_evaluation_v1",
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "embedding_model": provider.model_name,
        "vector_database": "qdrant",
        "collection": store.collection_name,
        "corpus_chunks": len(chunks),
        "retrieval_strategy": args.strategy,
        "top_k": args.top_k,
        "answerable_evaluation": {
            "questions": answerable_total,
            "answered": answered_count,
            "answer_rate": round(answered_count / answerable_total, 4),
            "answers_with_citations": cited_answer_count,
            "citation_presence_rate": round(
                cited_answer_count / answerable_total,
                4,
            ),
            "expected_citation_found": expected_citation_count,
            "expected_citation_recall": round(
                expected_citation_count / answerable_total,
                4,
            ),
            "failures": [
                row
                for row in answerable_rows
                if not row["expected_citation_found"]
            ],
        },
        "refusal_evaluation": {
            "questions": refusal_total,
            "refused": refused_count,
            "safe_refusal_rate": round(
                refused_count / refusal_total,
                4,
            ),
            "unsafe_answers": unsafe_answer_count,
            "failures": [
                row
                for row in refusal_rows
                if row["status"] != "refused"
            ],
        },
        "latency": {
            "measured_questions": total_questions,
            "median_latency_ms": round(
                statistics.median(latencies_ms),
                3,
            ),
            "p95_latency_ms": round(
                percentile_95(latencies_ms),
                3,
            ),
        },
        "answerable_results": answerable_rows,
        "refusal_results": refusal_rows,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()