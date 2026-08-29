from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    title: str
    section: str
    department: str
    version: str
    effective_date: str
    roles: tuple[str, ...]
    text: str
    page_number: int | None = None
    source_file: str = ""
    checksum: str = ""
    char_start: int = 0
    char_end: int = 0

    def is_authorized(self, role: str) -> bool:
        return "all" in self.roles or role in self.roles


@dataclass(frozen=True)
class EvaluationQuestion:
    question_id: str
    query: str
    expected_chunk_id: str
    role: str


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    vector_score: float
    bm25_score: float
    hybrid_score: float


@dataclass(frozen=True)
class DocumentMetadata:
    document_id: str
    title: str
    version: str
    effective_date: str
    department: str
    roles: tuple[str, ...]
    status: str = "active"

    def __post_init__(self) -> None:
        required = {
            "document_id": self.document_id,
            "title": self.title,
            "version": self.version,
            "effective_date": self.effective_date,
            "department": self.department,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"missing document metadata: {', '.join(missing)}")
        if not self.roles:
            raise ValueError("roles cannot be empty")
        try:
            date.fromisoformat(self.effective_date)
        except ValueError as exc:
            raise ValueError("effective_date must use YYYY-MM-DD") from exc


@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class IngestionResult:
    status: str
    document_id: str
    version: str
    checksum: str
    source_file: str
    page_count: int
    chunk_count: int
    chunks_path: str
    chunks: tuple[Chunk, ...] = ()
