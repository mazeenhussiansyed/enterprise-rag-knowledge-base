# Ingestion Verification - M02

Run date: 2026-08-20

## Implemented flow

1. Validate file existence, size, extension and PDF/DOCX signature.
2. Sanitize the display filename and normalize extracted Unicode text.
3. Calculate the SHA-256 checksum before parsing or indexing.
4. Stop immediately when the checksum already exists in the ledger.
5. Reject a reused document ID and version when its checksum has changed.
6. Parse PDF pages, DOCX paragraphs/page breaks, UTF-8 TXT or Markdown.
7. Create page-isolated 500-character chunks with 50-character overlap.
8. Add document, version, role, department, checksum, page and character offsets.
9. Write chunk JSONL atomically and register the version in the ledger.
10. Mark the previous version inactive when a valid new version is registered.

## Verified results

- 4/4 supported parsers passed.
- 9/9 complete project tests passed.
- The sample Markdown policy produced 6 chunks.
- Reingesting the same bytes returned `duplicate` with the same checksum.
- Reusing version `1.0` after changing the bytes raised a version conflict.
- Ingesting the changed bytes as version `2.0` created lineage and deactivated version `1.0`.
- A path-traversal filename and a false PDF signature were rejected.

## Reproduce

```bash
python -m pip install -e .
PYTHONPATH=src python -m unittest discover -s tests -v

PYTHONPATH=src python scripts/ingest_document.py \
  data/sample_documents/security_access_policy.md \
  --document-id SEC-POLICY \
  --title "Information Security Access Policy" \
  --version 1.0 \
  --effective-date 2026-08-20 \
  --department "Information Security" \
  --roles all
```

## Boundary of this milestone

This step produces validated chunks and lineage metadata. It does not yet create MiniLM embeddings or Qdrant points. Those outputs and metrics belong to M03 and will be reported separately.
