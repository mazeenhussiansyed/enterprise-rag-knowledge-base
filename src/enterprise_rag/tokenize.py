from __future__ import annotations

import re


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Return deterministic lowercase word tokens for the offline baseline."""
    return TOKEN_PATTERN.findall(text.lower())


def tokens_with_bigrams(text: str) -> list[str]:
    tokens = tokenize(text)
    bigrams = [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
    return tokens + bigrams
