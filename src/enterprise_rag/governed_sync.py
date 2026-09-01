from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .corpus import load_chunks
from .embeddings import MiniLMEmbeddingProvider
from .ingestion import IngestionService
from .models import DocumentMetadata
from .qdrant_store import QdrantVectorStore


@dataclass(frozen=True)
class GovernedSyncResult:
    run_id: str
    status: str
    ingestion_status: str
    document_id: str
    version: str
    checksum: str
    chunk_count: int
    indexed_chunks: int
    deactivated_chunks: int
    stored_version_chunks: int
    duration_ms: float


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)

    os.replace(temporary, path)


class GovernedSyncService:
    """Synchronize versioned ingestion output with governed Qdrant state."""

    def __init__(
        self,
        *,
        ingestion_service: IngestionService,
        vector_store: QdrantVectorStore,
        embedding_provider: MiniLMEmbeddingProvider,
        audit_path: str | Path,
        quarantine_root: str | Path,
    ) -> None:
        self.ingestion_service = ingestion_service
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.audit_path = Path(audit_path)
        self.quarantine_root = Path(quarantine_root)

    def ingest_and_sync(
        self,
        path: str | Path,
        metadata: DocumentMetadata,
    ) -> GovernedSyncResult:
        run_id = self._new_run_id()
        started_at = _utc_now()
        started = time.perf_counter()
        source = Path(path)

        try:
            ingestion_result = self.ingestion_service.ingest(source, metadata)
            ledger_entry = self._ledger_entry(
                ingestion_result.document_id,
                ingestion_result.version,
            )

            status = str(ledger_entry.get("status", "active"))
            active = bool(ledger_entry.get("active", False))

            self.vector_store.ensure_collection()
            existing_points = self.vector_store.count_document_version(
                ingestion_result.document_id,
                ingestion_result.version,
            )

            indexed_chunks = 0
            sync_status = "synchronized"

            if existing_points != ingestion_result.chunk_count:
                chunks = list(ingestion_result.chunks)

                if not chunks:
                    chunks = load_chunks(ingestion_result.chunks_path)

                indexed_chunks = self.vector_store.upsert_chunks(
                    chunks,
                    self.embedding_provider,
                    status=status,
                    active=active,
                    sync_run_id=run_id,
                )

                if ingestion_result.status == "duplicate":
                    sync_status = "repaired"
            else:
                self.vector_store.set_document_version_state(
                    ingestion_result.document_id,
                    ingestion_result.version,
                    active=active,
                    status=status,
                    sync_run_id=run_id,
                )

                if ingestion_result.status == "duplicate":
                    sync_status = "duplicate_skipped"

            deactivated_chunks = 0

            if ingestion_result.status != "duplicate" or active:
                deactivated_chunks = self.vector_store.deactivate_other_versions(
                    ingestion_result.document_id,
                    ingestion_result.version,
                    sync_run_id=run_id,
                )

            stored_version_chunks = self.vector_store.count_document_version(
                ingestion_result.document_id,
                ingestion_result.version,
            )

            if stored_version_chunks != ingestion_result.chunk_count:
                raise RuntimeError(
                    "Qdrant verification failed: expected "
                    f"{ingestion_result.chunk_count} chunks for "
                    f"{ingestion_result.document_id} version "
                    f"{ingestion_result.version}, found {stored_version_chunks}"
                )

            duration_ms = round(
                (time.perf_counter() - started) * 1000.0,
                3,
            )

            result = GovernedSyncResult(
                run_id=run_id,
                status=sync_status,
                ingestion_status=ingestion_result.status,
                document_id=ingestion_result.document_id,
                version=ingestion_result.version,
                checksum=ingestion_result.checksum,
                chunk_count=ingestion_result.chunk_count,
                indexed_chunks=indexed_chunks,
                deactivated_chunks=deactivated_chunks,
                stored_version_chunks=stored_version_chunks,
                duration_ms=duration_ms,
            )

            self._append_audit(
                {
                    **asdict(result),
                    "started_at": started_at,
                    "completed_at": _utc_now(),
                    "outcome": "success",
                    "source_file": ingestion_result.source_file,
                    "chunks_path": ingestion_result.chunks_path,
                }
            )

            return result

        except Exception as exc:
            duration_ms = round(
                (time.perf_counter() - started) * 1000.0,
                3,
            )

            failure = {
                "run_id": run_id,
                "outcome": "failed",
                "started_at": started_at,
                "failed_at": _utc_now(),
                "duration_ms": duration_ms,
                "source_path": str(source),
                "metadata": asdict(metadata),
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

            self._append_audit(failure)

            _write_json_atomic(
                self.quarantine_root / f"{run_id}.json",
                failure,
            )

            raise

    def _ledger_entry(self, document_id: str, version: str) -> dict:
        data = self.ingestion_service.ledger.load()
        versions = (
            data["documents"]
            .get(document_id, {})
            .get("versions", [])
        )

        for entry in versions:
            if entry.get("version") == version:
                return entry

        raise RuntimeError(
            f"ledger entry not found for {document_id} version {version}"
        )

    def _append_audit(self, payload: dict[str, object]) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    @staticmethod
    def _new_run_id() -> str:
        timestamp = datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        return f"sync-{timestamp}-{uuid4().hex[:8]}"