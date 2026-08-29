from pathlib import Path
import unittest

from enterprise_rag import HashingEmbeddingProvider, HybridRetriever, load_chunks, load_questions


ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "corpus" / "chunks.jsonl"
QUESTIONS = ROOT / "data" / "evaluation" / "questions.jsonl"


class RetrievalTests(unittest.TestCase):
    def test_hashing_provider_returns_normalized_384_dimension_vector(self) -> None:
        vector = HashingEmbeddingProvider().embed("role based enterprise retrieval")
        self.assertEqual(len(vector), 384)
        norm = sum(value * value for value in vector) ** 0.5
        self.assertLess(abs(norm - 1.0), 1e-9)

    def test_hybrid_retrieval_reaches_quality_floor(self) -> None:
        chunks = load_chunks(CHUNKS)
        questions = load_questions(QUESTIONS)
        retriever = HybridRetriever(chunks)

        hits = 0
        for question in questions:
            ids = [
                result.chunk.chunk_id
                for result in retriever.search(question.query, role=question.role, top_k=3)
            ]
            hits += question.expected_chunk_id in ids

        self.assertGreaterEqual(hits / len(questions), 0.90)

    def test_role_filter_prevents_restricted_contract_retrieval(self) -> None:
        retriever = HybridRetriever(load_chunks(CHUNKS))
        results = retriever.search(
            "What cyber insurance and liability clauses are required in vendor contracts?",
            role="all_employees",
            top_k=10,
        )
        self.assertNotIn("VM-02", {result.chunk.chunk_id for result in results})

        authorized = retriever.search(
            "What cyber insurance and liability clauses are required in vendor contracts?",
            role="legal",
            top_k=3,
        )
        self.assertEqual(authorized[0].chunk.chunk_id, "VM-02")


if __name__ == "__main__":
    unittest.main()
