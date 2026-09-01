from __future__ import annotations

from typing import Protocol

from .answering import (
    ExtractiveAnswerGenerator,
    GroundedAnswer,
)
from .models import SearchResult


class RetrieverProtocol(Protocol):
    def search(
        self,
        query: str,
        *,
        role: str,
        top_k: int = 3,
        strategy: str = "hybrid",
    ) -> list[SearchResult]:
        ...


class AnswerGeneratorProtocol(Protocol):
    def generate(
        self,
        query: str,
        *,
        role: str,
        results: list[SearchResult],
    ) -> GroundedAnswer:
        ...


class EnterpriseRAGService:
    """Coordinate governed retrieval and grounded answer generation."""

    def __init__(
        self,
        *,
        retriever: RetrieverProtocol,
        answer_generator: (
            AnswerGeneratorProtocol | None
        ) = None,
    ) -> None:
        self.retriever = retriever
        self.answer_generator = (
            answer_generator
            or ExtractiveAnswerGenerator()
        )

    def ask(
        self,
        query: str,
        *,
        role: str,
        top_k: int = 3,
        strategy: str = "hybrid",
    ) -> GroundedAnswer:
        if not query.strip():
            raise ValueError(
                "query cannot be empty"
            )

        if not role.strip():
            raise ValueError(
                "role cannot be empty"
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be positive"
            )

        if strategy not in {
            "vector",
            "bm25",
            "hybrid",
        }:
            raise ValueError(
                "strategy must be vector, "
                "bm25, or hybrid"
            )

        results = self.retriever.search(
            query,
            role=role,
            top_k=top_k,
            strategy=strategy,
        )

        return self.answer_generator.generate(
            query,
            role=role,
            results=results,
        )