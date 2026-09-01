from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from enterprise_rag.answering import GroundedAnswer
from enterprise_rag.api import EnterpriseRAGRuntime, create_app
class FakeProvider:
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
from enterprise_rag.models import Chunk, SearchResult


class FakeClient:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeStore:
    def __init__(self) -> None:
        self.collection_name = "enterprise_policy_chunks_v1"
        self.client = FakeClient()

    def count(self) -> int:
        return 26


class FakeRetriever:
    vector_weight = 0.70
    bm25_weight = 0.30
    vector_candidate_k = 20

    def __init__(self, result: SearchResult) -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    def search(
        self,
        query: str,
        *,
        role: str,
        top_k: int,
        strategy: str,
    ) -> list[SearchResult]:
        self.calls.append(
            {
                "query": query,
                "role": role,
                "top_k": top_k,
                "strategy": strategy,
            }
        )
        return [self.result]


class FakeGenerator:
    def __init__(self, answer: GroundedAnswer) -> None:
        self.answer = answer
        self.calls: list[dict[str, object]] = []

    def generate(
        self,
        query: str,
        role: str,
        results: list[SearchResult],
    ) -> GroundedAnswer:
        self.calls.append(
            {
                "query": query,
                "role": role,
                "result_count": len(results),
            }
        )
        return self.answer


def build_fake_runtime() -> EnterpriseRAGRuntime:
    chunk = Chunk(
        chunk_id="SEC-01",
        document_id="SEC-2026",
        title="Information Security Access Policy",
        section="Multi-Factor Authentication",
        department="Information Security",
        version="2.1",
        effective_date="2026-01-15",
        roles=("all",),
        text=(
            "Multi-factor authentication is mandatory for remote access "
            "and cloud applications."
        ),
    )
    result = SearchResult(
        chunk=chunk,
        vector_score=0.82,
        bm25_score=1.0,
        hybrid_score=0.95,
    )
    answer = GroundedAnswer(
        query=(
            "When is multi-factor authentication required and which "
            "authentication methods can employees use?"
        ),
        role="all_employees",
        status="answered",
        answer=(
            "Multi-factor authentication is mandatory for remote access "
            "and cloud applications. [1]"
        ),
        confidence=0.91,
        reason="sufficient_authorized_evidence",
        citations=(),
        provider="extractive-grounded-baseline",
    )

    return EnterpriseRAGRuntime(
        chunks=[chunk],
        provider=FakeProvider(),
        store=FakeStore(),
        retriever=FakeRetriever(result),
        generator=FakeGenerator(answer),
    )


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = build_fake_runtime()
        self.app = create_app(lambda: self.runtime)
        self.client = TestClient(self.app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)

    def test_health_reports_runtime_state(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["stored_points"], 26)
        self.assertEqual(response.json()["corpus_chunks"], 1)

    def test_stats_reports_retrieval_configuration(self) -> None:
        response = self.client.get("/stats")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["vector_weight"], 0.70)
        self.assertEqual(response.json()["bm25_weight"], 0.30)
        self.assertEqual(response.json()["vector_candidate_k"], 20)

    def test_search_returns_ranked_evidence(self) -> None:
        response = self.client.post(
            "/search",
            json={
                "query": "When is multi-factor authentication required?",
                "role": "all_employees",
                "strategy": "hybrid",
                "top_k": 3,
            },
        )

        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["result_count"], 1)
        self.assertEqual(body["results"][0]["rank"], 1)
        self.assertEqual(body["results"][0]["chunk_id"], "SEC-01")
        self.assertEqual(
            self.runtime.retriever.calls[0]["role"],
            "all_employees",
        )

    def test_ask_returns_grounded_answer_shape(self) -> None:
        response = self.client.post(
            "/ask",
            json={
                "query": "When is multi-factor authentication required?",
                "role": "all_employees",
            },
        )

        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "answered")
        self.assertIn("[1]", body["answer"])
        self.assertEqual(
            body["provider"],
            "extractive-grounded-baseline",
        )
        self.assertEqual(
            self.runtime.generator.calls[0]["result_count"],
            1,
        )

    def test_blank_query_is_rejected(self) -> None:
        response = self.client.post(
            "/search",
            json={
                "query": "   ",
                "role": "all_employees",
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()