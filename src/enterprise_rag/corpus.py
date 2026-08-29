from __future__ import annotations

import json
from pathlib import Path

from .models import Chunk, EvaluationQuestion


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on {path}:{line_number}") from exc
    return rows


def load_chunks(path: str | Path) -> list[Chunk]:
    chunks = []
    for row in _read_jsonl(Path(path)):
        chunks.append(
            Chunk(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                title=row["title"],
                section=row["section"],
                department=row["department"],
                version=row["version"],
                effective_date=row["effective_date"],
                roles=tuple(row["roles"]),
                text=row["text"],
                page_number=row.get("page_number"),
                source_file=row.get("source_file", ""),
                checksum=row.get("checksum", ""),
                char_start=row.get("char_start", 0),
                char_end=row.get("char_end", 0),
            )
        )
    return chunks


def load_questions(path: str | Path) -> list[EvaluationQuestion]:
    questions = []
    for row in _read_jsonl(Path(path)):
        questions.append(
            EvaluationQuestion(
                question_id=row["question_id"],
                query=row["query"],
                expected_chunk_id=row["expected_chunk_id"],
                role=row["role"],
            )
        )
    return questions
