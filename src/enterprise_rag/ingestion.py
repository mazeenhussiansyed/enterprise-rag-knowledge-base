from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from .chunking import build_chunks
from .ledger import IngestionLedger
from .models import DocumentMetadata, IngestionResult
from .parsers import parse_document, validate_document


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_directory_component(value: str) -> str:
    safe = "".join(character if character.isalnum() or character in "._-" else "-" for character in value)
    safe = safe.strip(".-")
    if not safe:
        raise ValueError("document ID and version require safe characters")
    return safe


def _write_chunks_atomic(path: Path, chunks) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        for chunk in chunks:
            row = asdict(chunk)
            row["roles"] = list(chunk.roles)
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


class IngestionService:
    def __init__(
        self,
        *,
        ledger_path: str | Path,
        output_root: str | Path,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> None:
        self.ledger = IngestionLedger(ledger_path)
        self.output_root = Path(output_root)
        self.chunk_size = chunk_size
        self.overlap = overlap

    def ingest(self, path: str | Path, metadata: DocumentMetadata) -> IngestionResult:
        source, _ = validate_document(path)
        checksum = sha256_file(source)
        duplicate = self.ledger.ensure_version_available(metadata, checksum)
        if duplicate:
            document_id, entry = duplicate
            return IngestionResult(
                status="duplicate",
                document_id=document_id,
                version=entry["version"],
                checksum=checksum,
                source_file=entry["source_file"],
                page_count=entry["page_count"],
                chunk_count=entry["chunk_count"],
                chunks_path=entry["chunks_path"],
            )

        source_file, pages = parse_document(source)
        chunks = build_chunks(
            pages,
            metadata,
            checksum=checksum,
            source_file=source_file,
            chunk_size=self.chunk_size,
            overlap=self.overlap,
        )
        document_directory = _safe_directory_component(metadata.document_id)
        version_directory = _safe_directory_component(metadata.version)
        chunks_path = (
            self.output_root / document_directory / f"v{version_directory}" / "chunks.jsonl"
        )
        _write_chunks_atomic(chunks_path, chunks)

        registration = self.ledger.register(
            metadata,
            checksum=checksum,
            source_file=source_file,
            page_count=len(pages),
            chunk_count=len(chunks),
            chunks_path=str(chunks_path),
        )
        return IngestionResult(
            status=registration.status,
            document_id=registration.document_id,
            version=registration.version,
            checksum=checksum,
            source_file=source_file,
            page_count=registration.page_count,
            chunk_count=registration.chunk_count,
            chunks_path=registration.chunks_path,
            chunks=tuple(chunks) if registration.status != "duplicate" else (),
        )
