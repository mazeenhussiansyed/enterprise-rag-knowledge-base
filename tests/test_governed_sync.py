from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from enterprise_rag import (
    DocumentMetadata,
    GovernedSyncService,
    IngestionService,
)
from enterprise_rag.errors import UnsafeDocumentError


class FakeVectorStore:
    def __init__(self) -> None:
        self.versions: dict[tuple[str, str], dict[str, object]] = {}
        self.upsert_calls = 0

    def ensure_collection(self) -> bool:
        return False

    def count_document_version(
        self,
        document_id: str,
        version: str,
    ) -> int:
        state = self.versions.get((document_id, version))
        return int(state["count"]) if state else 0

    def upsert_chunks(
        self,
        chunks,
        embedding_provider,
        *,
        status: str,
        active: bool,
        sync_run_id: str,
    ) -> int:
        self.upsert_calls += 1

        if not chunks:
            return 0

        key = (chunks[0].document_id, chunks[0].version)
        self.versions[key] = {
            "count": len(chunks),
            "status": status,
            "active": active,
            "sync_run_id": sync_run_id,
        }
        return len(chunks)

    def set_document_version_state(
        self,
        document_id: str,
        version: str,
        *,
        active: bool,
        status: str | None = None,
        sync_run_id: str | None = None,
    ) -> int:
        state = self.versions.get((document_id, version))

        if state is None:
            return 0

        state["active"] = active

        if status is not None:
            state["status"] = status
        if sync_run_id is not None:
            state["sync_run_id"] = sync_run_id

        return int(state["count"])

    def deactivate_other_versions(
        self,
        document_id: str,
        keep_version: str,
        *,
        sync_run_id: str | None = None,
    ) -> int:
        deactivated = 0

        for (
            stored_document_id,
            stored_version,
        ), state in self.versions.items():
            if (
                stored_document_id != document_id
                or stored_version == keep_version
            ):
                continue

            if state["active"] is True:
                state["active"] = False

                if sync_run_id is not None:
                    state["sync_run_id"] = sync_run_id

                deactivated += int(state["count"])

        return deactivated


class GovernedSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

        self.document = self.root / "security_policy.md"
        self.document.write_text(
            "# Security Policy\n\n"
            "Employees must use multi-factor authentication for remote "
            "access. Managers review privileged access every quarter.\n",
            encoding="utf-8",
        )

        self.ingestion_service = IngestionService(
            ledger_path=self.root / "ingestion" / "ledger.json",
            output_root=self.root / "ingested",
            chunk_size=500,
            overlap=50,
        )
        self.vector_store = FakeVectorStore()
        self.audit_path = self.root / "audit" / "runs.jsonl"
        self.quarantine_root = self.root / "quarantine"

        self.service = GovernedSyncService(
            ingestion_service=self.ingestion_service,
            vector_store=self.vector_store,
            embedding_provider=object(),
            audit_path=self.audit_path,
            quarantine_root=self.quarantine_root,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def metadata(version: str) -> DocumentMetadata:
        return DocumentMetadata(
            document_id="SEC-POLICY",
            title="Information Security Policy",
            version=version,
            effective_date="2026-09-01",
            department="Information Security",
            roles=("all",),
            status="active",
        )

    def test_duplicate_run_skips_reembedding(self) -> None:
        first = self.service.ingest_and_sync(
            self.document,
            self.metadata("1.0"),
        )
        second = self.service.ingest_and_sync(
            self.document,
            self.metadata("1.0"),
        )

        self.assertEqual(first.status, "synchronized")
        self.assertEqual(second.status, "duplicate_skipped")
        self.assertEqual(second.indexed_chunks, 0)
        self.assertEqual(self.vector_store.upsert_calls, 1)

        audit_rows = [
            json.loads(line)
            for line in self.audit_path.read_text(
                encoding="utf-8"
            ).splitlines()
        ]

        self.assertEqual(len(audit_rows), 2)
        self.assertTrue(
            all(row["outcome"] == "success" for row in audit_rows)
        )

    def test_missing_vector_state_is_repaired(self) -> None:
        ingestion = self.ingestion_service.ingest(
            self.document,
            self.metadata("1.0"),
        )

        result = self.service.ingest_and_sync(
            self.document,
            self.metadata("1.0"),
        )

        self.assertEqual(result.status, "repaired")
        self.assertEqual(result.ingestion_status, "duplicate")
        self.assertEqual(
            result.indexed_chunks,
            ingestion.chunk_count,
        )
        self.assertEqual(
            result.stored_version_chunks,
            ingestion.chunk_count,
        )

    def test_new_version_deactivates_previous_chunks(self) -> None:
        first = self.service.ingest_and_sync(
            self.document,
            self.metadata("1.0"),
        )

        version_two = self.root / "security_policy_v1_1.md"
        version_two.write_text(
            self.document.read_text(encoding="utf-8")
            + "\nPrivileged access overdue reviews are escalated.\n",
            encoding="utf-8",
        )

        second = self.service.ingest_and_sync(
            version_two,
            self.metadata("1.1"),
        )

        self.assertEqual(
            second.ingestion_status,
            "new_version",
        )
        self.assertEqual(
            second.deactivated_chunks,
            first.chunk_count,
        )
        self.assertFalse(
            self.vector_store.versions[
                ("SEC-POLICY", "1.0")
            ]["active"]
        )
        self.assertTrue(
            self.vector_store.versions[
                ("SEC-POLICY", "1.1")
            ]["active"]
        )

    def test_failure_writes_audit_and_quarantine_records(
        self,
    ) -> None:
        missing = self.root / "missing.md"

        with self.assertRaises(UnsafeDocumentError):
            self.service.ingest_and_sync(
                missing,
                self.metadata("1.0"),
            )

        audit_rows = [
            json.loads(line)
            for line in self.audit_path.read_text(
                encoding="utf-8"
            ).splitlines()
        ]
        quarantine_files = list(
            self.quarantine_root.glob("sync-*.json")
        )

        self.assertEqual(len(audit_rows), 1)
        self.assertEqual(audit_rows[0]["outcome"], "failed")
        self.assertEqual(
            audit_rows[0]["error_type"],
            "UnsafeDocumentError",
        )
        self.assertEqual(len(quarantine_files), 1)


if __name__ == "__main__":
    unittest.main()