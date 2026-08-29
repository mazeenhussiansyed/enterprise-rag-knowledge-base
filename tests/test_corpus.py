from pathlib import Path
import unittest

from enterprise_rag import load_chunks, load_questions


ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "corpus" / "chunks.jsonl"
QUESTIONS = ROOT / "data" / "evaluation" / "questions.jsonl"


class CorpusTests(unittest.TestCase):
    def test_frozen_benchmark_shape_and_references(self) -> None:
        chunks = load_chunks(CHUNKS)
        questions = load_questions(QUESTIONS)

        self.assertEqual(len(chunks), 26)
        self.assertEqual(len(questions), 20)
        chunk_ids = {chunk.chunk_id for chunk in chunks}
        self.assertEqual(len(chunk_ids), len(chunks))

        by_id = {chunk.chunk_id: chunk for chunk in chunks}
        for question in questions:
            self.assertIn(question.expected_chunk_id, chunk_ids)
            self.assertTrue(by_id[question.expected_chunk_id].is_authorized(question.role))

    def test_every_chunk_contains_lineage_and_access_metadata(self) -> None:
        for chunk in load_chunks(CHUNKS):
            self.assertTrue(chunk.version)
            self.assertTrue(chunk.effective_date)
            self.assertTrue(chunk.department)
            self.assertTrue(chunk.roles)
            self.assertGreaterEqual(len(chunk.text), 80)


if __name__ == "__main__":
    unittest.main()
