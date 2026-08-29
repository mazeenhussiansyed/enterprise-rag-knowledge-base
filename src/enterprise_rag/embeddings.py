from __future__ import annotations

import hashlib
import math
from collections import Counter

from .tokenize import tokens_with_bigrams


class HashingEmbeddingProvider:
    """Deterministic 384-dimension baseline used only for local tests.

    The production milestone replaces this provider with
    sentence-transformers/all-MiniLM-L6-v2 while keeping the same interface.
    """

    def __init__(self, dimensions: int = 384) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        counts = Counter(tokens_with_bigrams(text))
        vector = [0.0] * self.dimensions

        for token, count in counts.items():
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:8], "big") % self.dimensions
            sign = 1.0 if digest[8] % 2 == 0 else -1.0
            weight = 1.0 + math.log(count)
            if "_" in token:
                weight *= 1.35
            vector[index] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have equal dimensions")
    return sum(a * b for a, b in zip(left, right))
