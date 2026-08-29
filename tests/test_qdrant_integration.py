from __future__ import annotations

import os
import unittest
from pathlib import Path

from enterprise_rag import (
    MiniLMEmbeddingProvider,
    QdrantHybridRetriever,
    QdrantVectorStore,
    load_chunks,
    load_questions,
)


ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "corpus" / "chunks.jsonl"
QUESTIONS = ROOT / "data" / "evaluation" / "questions.jsonl"
RUN_INTEGRATION = os.getenv("RUN_QDRANT_INTEGRATION") == "1"


@unittest.skipUnless(
    RUN_INTEGRATION,
    "Set RUN_QDRANT_INTEGRATION=1 to run Qdrant integration tests.",
)
class QdrantIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.provider = MiniLMEmbeddingProvider()
        cls.store = QdrantVectorStore()

        if not cls.store.client.collection_exists(cls.store.collection_name):
            raise unittest.SkipTest(
                "Qdrant collection is missing. "
                "Run scripts/index_corpus_qdrant.py first."
            )

        cls.chunks = load_chunks(CHUNKS)
        cls.questions = load_questions(QUESTIONS)
        cls.hybrid_retriever = QdrantHybridRetriever(
            cls.chunks,
            vector_store=cls.store,
            embedding_provider=cls.provider,
            vector_weight=0.70,
            bm25_weight=0.30,
            vector_candidate_k=20,
        )

    def test_collection_contains_expected_points(self) -> None:
        self.assertEqual(self.store.count(), 26)

    def test_minilm_retrieves_expected_security_chunk(self) -> None:
        results = self.store.search(
            (
                "When is multi-factor authentication required and "
                "which authentication methods can employees use?"
            ),
            self.provider,
            role="all_employees",
            top_k=3,
        )

        self.assertEqual(results[0].chunk.chunk_id, "SEC-01")
        self.assertEqual(len(results), 3)
        self.assertGreater(
            results[0].vector_score,
            results[1].vector_score,
        )

    def test_qdrant_enforces_role_filter(self) -> None:
        query = (
            "What cyber insurance and liability clauses are "
            "required in vendor contracts?"
        )

        employee_results = self.store.search(
            query,
            self.provider,
            role="all_employees",
            top_k=10,
        )
        employee_ids = {
            result.chunk.chunk_id for result in employee_results
        }
        self.assertNotIn("VM-02", employee_ids)

        legal_results = self.store.search(
            query,
            self.provider,
            role="legal",
            top_k=3,
        )
        self.assertEqual(legal_results[0].chunk.chunk_id, "VM-02")

    def test_production_hybrid_reaches_quality_floor(self) -> None:
        hits = 0

        for question in self.questions:
            results = self.hybrid_retriever.search(
                question.query,
                role=question.role,
                top_k=3,
                strategy="hybrid",
            )
            ranked_ids = [
                result.chunk.chunk_id for result in results
            ]
            hits += question.expected_chunk_id in ranked_ids

        self.assertGreaterEqual(
            hits / len(self.questions),
            0.95,
        )


if __name__ == "__main__":
    unittest.main()