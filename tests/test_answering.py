from __future__ import annotations

import unittest

from enterprise_rag.answering import (
    AnswerabilityGate,
    ExtractiveAnswerGenerator,
)
from enterprise_rag.models import Chunk, SearchResult


def make_result(
    *,
    text: str,
    section: str,
    vector_score: float,
    hybrid_score: float,
) -> SearchResult:
    chunk = Chunk(
        chunk_id="TEST-01",
        document_id="TEST-2026",
        title="Information Security Access Policy",
        section=section,
        department="Information Security",
        version="1.0",
        effective_date="2026-09-01",
        roles=("all",),
        text=text,
    )
    return SearchResult(
        chunk=chunk,
        vector_score=vector_score,
        bm25_score=hybrid_score,
        hybrid_score=hybrid_score,
    )


class GroundedAnswerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = ExtractiveAnswerGenerator(
            AnswerabilityGate()
        )

    def test_answer_contains_numbered_citation(self) -> None:
        result = make_result(
            section="Multi-Factor Authentication",
            text=(
                "Multi-factor authentication is mandatory for remote "
                "access and cloud applications. Employees must use an "
                "approved authenticator application or hardware security key."
            ),
            vector_score=0.82,
            hybrid_score=1.0,
        )

        answer = self.generator.generate(
            "When is multi-factor authentication required and which "
            "authentication methods can employees use?",
            "all_employees",
            [result],
        )

        self.assertEqual(answer.status, "answered")
        self.assertIn("[1]", answer.answer)
        self.assertEqual(len(answer.citations), 1)
        self.assertEqual(
            answer.citations[0].section,
            "Multi-Factor Authentication",
        )

    def test_missing_authorized_evidence_is_refused(self) -> None:
        answer = self.generator.generate(
            "What is the password standard?",
            "all_employees",
            [],
        )

        self.assertEqual(answer.status, "refused")
        self.assertEqual(answer.reason, "no_authorized_evidence")
        self.assertEqual(answer.citations, ())

    def test_weak_retrieval_score_is_refused(self) -> None:
        result = make_result(
            section="Travel and Expense",
            text="Business travel requires manager approval.",
            vector_score=0.12,
            hybrid_score=0.20,
        )

        answer = self.generator.generate(
            "What is the vacation leave policy?",
            "all_employees",
            [result],
        )

        self.assertEqual(answer.status, "refused")
        self.assertEqual(
            answer.reason,
            "below_vector_score_threshold",
        )
        self.assertEqual(answer.citations, ())

    def test_unrelated_question_is_refused(self) -> None:
        result = make_result(
            section="Meal Limits",
            text=(
                "Business travel meals are reimbursed up to seventy-five "
                "dollars per traveler per day."
            ),
            vector_score=0.53,
            hybrid_score=1.0,
        )

        answer = self.generator.generate(
            "What meals are served in the company cafeteria?",
            "all_employees",
            [result],
        )

        self.assertEqual(answer.status, "refused")
        self.assertEqual(
            answer.reason,
            "insufficient_query_grounding",
        )
        self.assertEqual(answer.citations, ())

    def test_no_sentence_level_grounding_is_refused(self) -> None:
        result = make_result(
            section="Endpoint Access Governance",
            text="All computers must use disk encryption.",
            vector_score=0.85,
            hybrid_score=1.0,
        )

        answer = self.generator.generate(
            "What does Endpoint Access Governance say?",
            "all_employees",
            [result],
        )

        self.assertEqual(answer.status, "refused")
        self.assertEqual(
            answer.reason,
            "no_sentence_level_grounding",
        )
        self.assertEqual(answer.citations, ())


if __name__ == "__main__":
    unittest.main()