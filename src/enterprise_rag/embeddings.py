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


class MiniLMEmbeddingProvider:
    """Production semantic embeddings powered by all-MiniLM-L6-v2."""

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        dimensions: int = 384,
    ) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")

        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise RuntimeError(
                "FastEmbed is required for MiniLM embeddings. "
                "Install the project dependencies with: python -m pip install -e ."
            ) from exc

        self.model_name = model_name
        self.dimensions = dimensions
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        vectors = [
            [float(value) for value in vector]
            for vector in self._model.embed(texts)
        ]

        for vector in vectors:
            if len(vector) != self.dimensions:
                raise RuntimeError(
                    f"Expected {self.dimensions} embedding dimensions, "
                    f"received {len(vector)}"
                )

        return vectors


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have equal dimensions")
    return sum(a * b for a, b in zip(left, right))