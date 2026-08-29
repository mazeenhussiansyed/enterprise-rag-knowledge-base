from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .errors import VersionConflictError
from .models import DocumentMetadata


@dataclass(frozen=True)
class LedgerRegistration:
    status: str
    document_id: str
    version: str
    chunks_path: str
    page_count: int
    chunk_count: int


class IngestionLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _empty(self) -> dict:
        return {"schema_version": 1, "documents": {}}

    def load(self) -> dict:
        if not self.path.exists():
            return self._empty()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid ingestion ledger: {self.path}") from exc
        if data.get("schema_version") != 1 or not isinstance(data.get("documents"), dict):
            raise ValueError(f"unsupported ingestion ledger schema: {self.path}")
        return data

    def _write_atomic(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, self.path)

    @staticmethod
    def _all_versions(data: dict):
        for document_id, document in data["documents"].items():
            for entry in document.get("versions", []):
                yield document_id, entry

    def find_checksum(self, checksum: str) -> tuple[str, dict] | None:
        for document_id, entry in self._all_versions(self.load()):
            if entry["checksum"] == checksum:
                return document_id, entry
        return None

    def ensure_version_available(
        self, metadata: DocumentMetadata, checksum: str
    ) -> tuple[str, dict] | None:
        data = self.load()
        for document_id, entry in self._all_versions(data):
            if entry["checksum"] == checksum:
                return document_id, entry

        versions = data["documents"].get(metadata.document_id, {}).get("versions", [])
        for entry in versions:
            if entry["version"] == metadata.version and entry["checksum"] != checksum:
                raise VersionConflictError(
                    f"{metadata.document_id} version {metadata.version} already exists with different content; use a new version"
                )
        return None

    def register(
        self,
        metadata: DocumentMetadata,
        *,
        checksum: str,
        source_file: str,
        page_count: int,
        chunk_count: int,
        chunks_path: str,
    ) -> LedgerRegistration:
        data = self.load()
        for document_id, entry in self._all_versions(data):
            if entry["checksum"] == checksum:
                return LedgerRegistration(
                    status="duplicate",
                    document_id=document_id,
                    version=entry["version"],
                    chunks_path=entry["chunks_path"],
                    page_count=entry["page_count"],
                    chunk_count=entry["chunk_count"],
                )

        document = data["documents"].setdefault(
            metadata.document_id,
            {"title": metadata.title, "versions": []},
        )
        versions = document["versions"]
        for entry in versions:
            if entry["version"] == metadata.version:
                raise VersionConflictError(
                    f"{metadata.document_id} version {metadata.version} already exists with different content; use a new version"
                )

        status = "created" if not versions else "new_version"
        for entry in versions:
            entry["active"] = False

        versions.append(
            {
                "version": metadata.version,
                "effective_date": metadata.effective_date,
                "department": metadata.department,
                "roles": list(metadata.roles),
                "status": metadata.status,
                "checksum": checksum,
                "source_file": source_file,
                "page_count": page_count,
                "chunk_count": chunk_count,
                "chunks_path": chunks_path,
                "active": metadata.status == "active",
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        document["title"] = metadata.title
        self._write_atomic(data)
        return LedgerRegistration(
            status=status,
            document_id=metadata.document_id,
            version=metadata.version,
            chunks_path=chunks_path,
            page_count=page_count,
            chunk_count=chunk_count,
        )

    def active_version(self, document_id: str) -> dict | None:
        versions = self.load()["documents"].get(document_id, {}).get("versions", [])
        return next((entry for entry in versions if entry.get("active")), None)
