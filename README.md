# Enterprise Policy RAG Knowledge Base

An evidence-first enterprise retrieval system with production document ingestion, MiniLM embeddings, Qdrant vector storage, BM25 hybrid ranking, role-based access control and governed incremental synchronization.

The project separates ingestion, storage, retrieval and evaluation so every stage can be tested and measured independently.

## Current project status

Milestones M00 through M04 are complete:

- controlled enterprise-policy corpus and frozen benchmark;
- offline deterministic retrieval baseline;
- PDF, DOCX, TXT and Markdown ingestion;
- checksum-based duplicate and version control;
- MiniLM semantic embeddings and persistent Qdrant storage;
- BM25 and 70/30 hybrid retrieval;
- role-based authorization before ranking;
- governed incremental ingestion-to-Qdrant synchronization;
- active and historical document-version management;
- audit records, quarantine manifests and recovery testing.

## Verified retrieval results

Measured on a controlled 26-chunk corpus and 20-question frozen benchmark:

| Strategy | Hit@1 | Hit@3 | MRR |
|---|---:|---:|---:|
| Hashing-vector baseline | 85% | 95% | 0.8917 |
| Baseline BM25 | 100% | 100% | 1.000 |
| Baseline hybrid | 95% | 100% | 0.975 |
| MiniLM and Qdrant vector | 100% | 100% | 1.000 |
| Production 70/30 hybrid | 100% | 100% | 1.000 |

Local production-hybrid latency:

- Median: 15.940 ms
- P95: 24.991 ms
- Unauthorized restricted retrievals: 0

These results describe a deliberately small synthetic benchmark and are not claims of universal production accuracy.

## Verified synchronization results

| Check | Result |
|---|---:|
| Missing vectors automatically recovered | 6/6 |
| Duplicate rerun embeddings generated | 0 |
| Duplicate rerun duration | 61.631 ms |
| Recovery-to-skip speedup | 31.16x |
| New version chunks indexed | 7 |
| Previous-version chunks deactivated | 6 |
| Historical vectors retained | 13 |
| Inactive-version retrieval leakage | 0 |
| Active-version top results | 3/3 |
| Automated tests with live Qdrant | 17/17 passed |

See `METRICS.md` and `docs/evaluation/GOVERNED_SYNC_M04.md` for evidence and scope.

## Architecture

```text
Enterprise documents
        |
        v
Validation and parsing
        |
        v
SHA-256 duplicate and version checks
        |
        v
500-character chunks with 50-character overlap
        |
        +--------------------+
        |                    |
        v                    v
MiniLM embeddings        BM25 index
        |                    |
        v                    |
Qdrant vector storage       |
        |                    |
        +------ 70/30 hybrid ranking
                         |
                         v
Role, status and active-version evidence