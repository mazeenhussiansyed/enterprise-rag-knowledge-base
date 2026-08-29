from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from enterprise_rag import DocumentMetadata, IngestionService  # noqa: E402
from enterprise_rag.errors import IngestionError  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a versioned enterprise document")
    parser.add_argument("file", type=Path)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--effective-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--department", required=True)
    parser.add_argument("--roles", required=True, help="Comma-separated role names or all")
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
    args = parser.parse_args()

    roles = tuple(role.strip() for role in args.roles.split(",") if role.strip())
    metadata = DocumentMetadata(
        document_id=args.document_id,
        title=args.title,
        version=args.version,
        effective_date=args.effective_date,
        department=args.department,
        roles=roles,
    )
    service = IngestionService(
        ledger_path=args.ledger,
        output_root=args.output_root,
        chunk_size=500,
        overlap=50,
    )
    try:
        result = service.ingest(args.file, metadata)
    except (IngestionError, ValueError) as exc:
        parser.exit(2, f"ingestion failed: {exc}\n")

    payload = asdict(result)
    payload.pop("chunks")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
