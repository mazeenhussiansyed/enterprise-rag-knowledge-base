from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from enterprise_rag import (  # noqa: E402
    DocumentMetadata,
    GovernedSyncService,
    IngestionService,
    MiniLMEmbeddingProvider,
    QdrantVectorStore,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest, version, embed and synchronize an enterprise "
            "document with governed Qdrant storage"
        )
    )

    parser.add_argument("file", type=Path)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--effective-date",
        required=True,
        help="YYYY-MM-DD",
    )
    parser.add_argument("--department", required=True)
    parser.add_argument(
        "--roles",
        required=True,
        help="Comma-separated role names or all",
    )
    parser.add_argument(
        "--status",
        choices=("active", "inactive", "retired"),
        default="active",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=PROJECT_ROOT / "data" / "ingestion" / "ledger.json",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "data" / "ingested",
    )
    parser.add_argument(
        "--audit",
        type=Path,
        default=(
            PROJECT_ROOT
            / "data"
            / "audit"
            / "governed_sync_runs.jsonl"
        ),
    )
    parser.add_argument(
        "--quarantine-root",
        type=Path,
        default=(
            PROJECT_ROOT
            / "data"
            / "quarantine"
            / "governed_sync"
        ),
    )
    parser.add_argument(
        "--qdrant-url",
        default="http://localhost:6333",
    )
    parser.add_argument(
        "--collection",
        default=QdrantVectorStore.DEFAULT_COLLECTION,
    )

    args = parser.parse_args()

    roles = tuple(
        role.strip()
        for role in args.roles.split(",")
        if role.strip()
    )

    metadata = DocumentMetadata(
        document_id=args.document_id,
        title=args.title,
        version=args.version,
        effective_date=args.effective_date,
        department=args.department,
        roles=roles,
        status=args.status,
    )

    ingestion_service = IngestionService(
        ledger_path=args.ledger,
        output_root=args.output_root,
        chunk_size=500,
        overlap=50,
    )

    try:
        synchronization_service = GovernedSyncService(
            ingestion_service=ingestion_service,
            vector_store=QdrantVectorStore(
                url=args.qdrant_url,
                collection_name=args.collection,
            ),
            embedding_provider=MiniLMEmbeddingProvider(),
            audit_path=args.audit,
            quarantine_root=args.quarantine_root,
        )

        result = synchronization_service.ingest_and_sync(
            args.file,
            metadata,
        )
    except Exception as exc:
        parser.exit(2, f"governed synchronization failed: {exc}\n")

    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()