from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from .models import SearchResult


_STOP_WORDS = {
    "a",
    "about",
    "all",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "can",
    "cannot",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "many",
    "me",
    "of",
    "on",
    "or",
    "say",
    "the",
    "to",
    "use",
    "used",
    "using",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "would",
    "you",
    "your",
    "apply",
}


_TERM_ALIASES = {
    "accounts": "account",
    "agreements": "agreement",
    "agreement": "agreement",
    "approvals": "approval",
    "applications": "application",
    "character": "length",
    "characters": "length",
    "controls": "control",
    "employee": "employee",
    "employees": "employee",
    "externally": "external",
    "least": "minimum",
    "length": "length",
    "method": "method",
    "methods": "method",
    "minimum": "minimum",
    "password": "password",
    "passwords": "password",
    "require": "required",
    "required": "required",
    "requires": "required",
    "reuse": "reuse",
    "reused": "reuse",
    "reuses": "reuse",
    "share": "share",
    "shared": "share",
    "shares": "share",
    "sharing": "share",
    "window": "window",
    "windows": "window",
}


@dataclass(frozen=True)
class Citation:
    citation_id: int
    chunk_id: str
    document_id: str
    title: str
    section: str
    version: str
    effective_date: str
    page_number: int | None
    relevance_score: float
    excerpt: str


@dataclass(frozen=True)
class AnswerabilityDecision:
    accepted: bool
    confidence: float
    reason: str
    matched_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundedAnswer:
    query: str
    role: str
    status: str
    answer: str
    confidence: float
    reason: str
    citations: tuple[Citation, ...]
    provider: str


class AnswerabilityGate:
    """Reject answers that lack strong, topically grounded evidence."""

    def __init__(
        self,
        *,
        minimum_vector_score: float = 0.49,
        minimum_hybrid_score: float = 0.35,
        minimum_query_term_matches: int = 2,
        minimum_query_coverage: float = 0.40,
    ) -> None:
        if not 0.0 <= minimum_vector_score <= 1.0:
            raise ValueError("minimum_vector_score must be between 0 and 1")
        if not 0.0 <= minimum_hybrid_score <= 1.0:
            raise ValueError("minimum_hybrid_score must be between 0 and 1")
        if minimum_query_term_matches <= 0:
            raise ValueError("minimum_query_term_matches must be positive")
        if not 0.0 <= minimum_query_coverage <= 1.0:
            raise ValueError(
                "minimum_query_coverage must be between 0 and 1"
            )

        self.minimum_vector_score = minimum_vector_score
        self.minimum_hybrid_score = minimum_hybrid_score
        self.minimum_query_term_matches = minimum_query_term_matches
        self.minimum_query_coverage = minimum_query_coverage

    def evaluate(
        self,
        query: str,
        results: Sequence[SearchResult],
    ) -> AnswerabilityDecision:
        if not results:
            return AnswerabilityDecision(
                accepted=False,
                confidence=0.0,
                reason="no_authorized_evidence",
            )

        top_result = results[0]
        confidence = round(
            (0.65 * top_result.vector_score)
            + (0.35 * top_result.hybrid_score),
            4,
        )

        if top_result.vector_score < self.minimum_vector_score:
            return AnswerabilityDecision(
                accepted=False,
                confidence=confidence,
                reason="below_vector_score_threshold",
            )

        if top_result.hybrid_score < self.minimum_hybrid_score:
            return AnswerabilityDecision(
                accepted=False,
                confidence=confidence,
                reason="below_hybrid_score_threshold",
            )

        matched_terms, coverage = self._query_grounding(
            query,
            top_result,
        )
        query_terms = self._content_terms(query)
        required_matches = min(
            self.minimum_query_term_matches,
            len(query_terms),
        )

        if (
            len(matched_terms) < required_matches
            or coverage < self.minimum_query_coverage
        ):
            return AnswerabilityDecision(
                accepted=False,
                confidence=confidence,
                reason="insufficient_query_grounding",
                matched_terms=matched_terms,
            )

        return AnswerabilityDecision(
            accepted=True,
            confidence=confidence,
            reason="sufficient_authorized_evidence",
            matched_terms=matched_terms,
        )

    def _query_grounding(
        self,
        query: str,
        result: SearchResult,
    ) -> tuple[tuple[str, ...], float]:
        query_terms = self._content_terms(query)

        if not query_terms:
            return (), 0.0

        evidence_text = " ".join(
            [
                result.chunk.title,
                result.chunk.section,
                result.chunk.department,
                result.chunk.text,
            ]
        )
        evidence_terms = self._content_terms(evidence_text)

        matched_terms = tuple(sorted(query_terms & evidence_terms))
        coverage = len(matched_terms) / len(query_terms)

        return matched_terms, coverage

    @staticmethod
    def _content_terms(text: str) -> set[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())

        return {
            AnswerabilityGate._normalize_term(token)
            for token in tokens
            if len(token) > 2 and token not in _STOP_WORDS
        }

    @staticmethod
    def _normalize_term(token: str) -> str:
        alias = _TERM_ALIASES.get(token)

        if alias is not None:
            return alias

        if token.endswith("ies") and len(token) > 4:
            token = f"{token[:-3]}y"
        elif (
            token.endswith("s")
            and len(token) > 4
            and not token.endswith("ss")
        ):
            token = token[:-1]

        return _TERM_ALIASES.get(token, token)


class ExtractiveAnswerGenerator:
    """Creates citation-backed answers without unsupported facts."""

    PROVIDER_NAME = "extractive-grounded-baseline"

    def __init__(
        self,
        gate: AnswerabilityGate | None = None,
        *,
        max_citations: int = 3,
        max_sentences_per_citation: int = 2,
        relative_citation_threshold: float = 0.55,
    ) -> None:
        if max_citations <= 0:
            raise ValueError("max_citations must be positive")
        if max_sentences_per_citation <= 0:
            raise ValueError(
                "max_sentences_per_citation must be positive"
            )
        if not 0.0 <= relative_citation_threshold <= 1.0:
            raise ValueError(
                "relative_citation_threshold must be between 0 and 1"
            )

        self.gate = gate or AnswerabilityGate()
        self.max_citations = max_citations
        self.max_sentences_per_citation = max_sentences_per_citation
        self.relative_citation_threshold = relative_citation_threshold

    def generate(
        self,
        query: str,
        role: str,
        results: Sequence[SearchResult],
    ) -> GroundedAnswer:
        decision = self.gate.evaluate(query, results)

        if not decision.accepted:
            return GroundedAnswer(
                query=query,
                role=role,
                status="refused",
                answer=(
                    "I cannot answer this from the authorized policy "
                    "evidence available."
                ),
                confidence=decision.confidence,
                reason=decision.reason,
                citations=(),
                provider=self.PROVIDER_NAME,
            )

        top_relevance_score = results[0].hybrid_score
        minimum_citation_score = (
            top_relevance_score * self.relative_citation_threshold
        )

        answer_parts: list[str] = []
        citations: list[Citation] = []

        for result in results:
            if len(citations) >= self.max_citations:
                break

            if result.hybrid_score < minimum_citation_score:
                continue

            selected_sentences = self._select_supported_sentences(
                query,
                result.chunk.text,
            )

            if not selected_sentences:
                continue

            citation_id = len(citations) + 1
            answer_parts.append(
                f"{' '.join(selected_sentences)} [{citation_id}]"
            )
            citations.append(
                Citation(
                    citation_id=citation_id,
                    chunk_id=result.chunk.chunk_id,
                    document_id=result.chunk.document_id,
                    title=result.chunk.title,
                    section=result.chunk.section,
                    version=result.chunk.version,
                    effective_date=result.chunk.effective_date,
                    page_number=result.chunk.page_number,
                    relevance_score=round(result.hybrid_score, 4),
                    excerpt=result.chunk.text,
                )
            )

        if not citations:
            return GroundedAnswer(
                query=query,
                role=role,
                status="refused",
                answer=(
                    "I cannot answer this from the authorized policy "
                    "evidence available."
                ),
                confidence=decision.confidence,
                reason="no_sentence_level_grounding",
                citations=(),
                provider=self.PROVIDER_NAME,
            )

        return GroundedAnswer(
            query=query,
            role=role,
            status="answered",
            answer=" ".join(answer_parts),
            confidence=decision.confidence,
            reason=decision.reason,
            citations=tuple(citations),
            provider=self.PROVIDER_NAME,
        )

    def _select_supported_sentences(
        self,
        query: str,
        text: str,
    ) -> list[str]:
        query_terms = self.gate._content_terms(query)
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
            if sentence.strip()
        ]

        selected: list[str] = []

        for sentence in sentences:
            sentence_terms = self.gate._content_terms(sentence)

            if query_terms & sentence_terms:
                selected.append(sentence)

            if len(selected) >= self.max_sentences_per_citation:
                break

        return selected