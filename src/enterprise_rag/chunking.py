from __future__ import annotations

import re

from .models import Chunk, DocumentMetadata, ParsedPage


def _safe_identifier(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-.")
    if not normalized:
        raise ValueError("document_id and version require safe characters")
    return normalized


def build_chunks(
    pages: list[ParsedPage],
    metadata: DocumentMetadata,
    *,
    checksum: str,
    source_file: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    document_key = _safe_identifier(metadata.document_id)
    version_key = _safe_identifier(metadata.version)
    chunks: list[Chunk] = []
    sequence = 1

    for page in pages:
        start = 0
        while start < len(page.text):
            end = min(start + chunk_size, len(page.text))
            text = page.text[start:end]
            chunk_id = (
                f"{document_key}-v{version_key}-p{page.page_number:04d}-c{sequence:04d}"
            )
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=metadata.document_id,
                    title=metadata.title,
                    section=f"Page {page.page_number}",
                    department=metadata.department,
                    version=metadata.version,
                    effective_date=metadata.effective_date,
                    roles=metadata.roles,
                    text=text,
                    page_number=page.page_number,
                    source_file=source_file,
                    checksum=checksum,
                    char_start=start,
                    char_end=end,
                )
            )
            sequence += 1
            if end == len(page.text):
                break
            start = end - overlap

    if not chunks:
        raise ValueError("document produced no chunks")
    return chunks
