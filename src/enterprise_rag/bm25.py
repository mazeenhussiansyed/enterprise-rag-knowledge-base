from __future__ import annotations

import math
from collections import Counter


class BM25Index:
    def __init__(
        self,
        documents: list[list[str]],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if not documents:
            raise ValueError("documents cannot be empty")
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.term_frequencies = [Counter(document) for document in documents]
        self.document_lengths = [len(document) for document in documents]
        self.average_length = sum(self.document_lengths) / len(self.document_lengths)

        document_frequency: Counter[str] = Counter()
        for document in documents:
            document_frequency.update(set(document))

        count = len(documents)
        self.idf = {
            term: math.log(1.0 + (count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def score(self, query_tokens: list[str]) -> list[float]:
        scores: list[float] = []
        for frequencies, length in zip(self.term_frequencies, self.document_lengths):
            score = 0.0
            length_factor = 1.0 - self.b + self.b * length / self.average_length
            for term in query_tokens:
                frequency = frequencies.get(term, 0)
                if frequency == 0:
                    continue
                numerator = frequency * (self.k1 + 1.0)
                denominator = frequency + self.k1 * length_factor
                score += self.idf.get(term, 0.0) * numerator / denominator
            scores.append(score)
        return scores
