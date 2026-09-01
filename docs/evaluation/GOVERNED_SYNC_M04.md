# M04 Evaluation: Governed Incremental Document Synchronization

**Evaluation date:** 2026-09-01
**Collection:** `enterprise_policy_governed_v1`
**Embedding model:** `sentence-transformers/all-MiniLM-L6-v2`

## Objective

Build an auditable ingestion-to-Qdrant pipeline that supports incremental synchronization, idempotent reruns, version governance, recovery from missing vectors, active-version retrieval and controlled failure quarantine.

## Implemented capabilities

- Unique synchronization run IDs
- Incremental document ingestion and embedding
- Deterministic Qdrant point identifiers
- Duplicate-safe and idempotent reruns
- Missing-vector detection and automatic recovery
- Active and inactive document-version metadata
- Previous-version deactivation without historical deletion
- Role, department, document, version and status filters
- JSONL pipeline audit records
- Failure quarantine manifests
- Post-synchronization point-count verification
- Offline unit tests and live Qdrant integration tests

## Verified results

| Check | Result |
|---|---:|
| Missing-vector recovery | 6/6 chunks restored |
| Initial recovery duration | 1,920.320 ms |
| Duplicate rerun embeddings generated | 0 |
| Duplicate rerun stored chunks | 6 |
| Duplicate rerun duration | 61.631 ms |
| Duplicate rerun speedup | 31.16x |
| Version 1.1 chunks indexed | 7 |
| Version 1.0 chunks deactivated | 6 |
| Version transition duration | 588.430 ms |
| Historical points retained | 13 |
| Version 1.0 active points | 0 |
| Version 1.1 active points | 7 |
| Active-only retrieval top results | 3/3 from version 1.1 |
| Best active-version semantic score | 0.7034 |
| Controlled failure audit records | 1 |
| Controlled failure quarantine manifests | 1 |
| Complete automated suite | 17/17 passed |

## Recovery test

The ingestion ledger already contained `SEC-POLICY` version 1.0, while the governed Qdrant collection contained no corresponding vectors. The synchronization service detected the mismatch and restored all six stored chunks.

```text
status: repaired
ingestion_status: duplicate
indexed_chunks: 6
stored_version_chunks: 6
duration_ms: 1920.320