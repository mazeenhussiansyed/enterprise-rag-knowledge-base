# Enterprise Policy RAG Knowledge Base

An evidence-first Enterprise Retrieval-Augmented Generation (RAG) project for searching internal policy and operational documents safely. The system validates and versions source documents, indexes semantic embeddings in Qdrant, combines vector search with BM25, enforces role-based access control, and returns citation-backed answers or safe refusals.

The project separates ingestion, storage, retrieval, synchronization, answering, and evaluation so every stage can be tested and measured independently.

## Current Status

Milestones **M00 through M05 are complete**.

- Controlled 26-chunk enterprise-policy corpus and 20-question benchmark
- PDF, DOCX, TXT, and Markdown document ingestion
- SHA-256 duplicate detection and immutable document-version lineage
- 500-character chunks with 50-character overlap and source metadata
- MiniLM semantic embeddings with persistent Qdrant vector storage
- BM25 plus 70/30 vector-keyword hybrid retrieval
- Role-based authorization applied before ranking
- Governed incremental synchronization with audit logs and quarantine records
- Active-version management with historical-vector retention
- Citation-backed extractive answers and evidence-based safe refusals
- Reproducible retrieval, synchronization, answer, and refusal evaluation

## Verified Results

All figures below are from a deliberately small controlled synthetic benchmark. They are reproducible local measurements, not universal production-performance claims.

### Retrieval

| Strategy | Hit@1 | Hit@3 | MRR |
|---|---:|---:|---:|
| Hashing-vector baseline | 85% | 95% | 0.8917 |
| BM25 baseline | 100% | 100% | 1.000 |
| Hashing and BM25 hybrid | 95% | 100% | 0.975 |
| MiniLM and Qdrant vector search | 100% | 100% | 1.000 |
| MiniLM/Qdrant and BM25 hybrid | 100% | 100% | 1.000 |

### Governed Synchronization

| Check | Result |
|---|---:|
| Missing vectors automatically recovered | 6 / 6 |
| Duplicate-rerun embeddings generated | 0 |
| New-version chunks indexed | 7 |
| Previous-version chunks deactivated | 6 |
| Historical vectors retained | 13 |
| Inactive-version retrieval leakage | 0 |
| Live Qdrant tests after M04 | 17 / 17 passed |

### Grounded Answers and Refusals

| Check | Result |
|---|---:|
| Answerable benchmark questions | 20 |
| Answered with citations | 20 / 20 |
| Expected-citation recall | 100% |
| Unsupported questions refused | 3 / 3 |
| Unsafe answers | 0 |
| Full automated suite after M05 | 22 / 22 passed |

See [METRICS.md](METRICS.md), [M04 evaluation](docs/evaluation/GOVERNED_SYNC_M04.md), and [M05 evaluation](docs/evaluation/GROUNDED_ANSWERS_M05.md) for commands, evidence, and scope limitations.

## Architecture

```text
Enterprise documents
        |
        v
Validation, parsing, and SHA-256 checksum
        |
        v
Version ledger and duplicate detection
        |
        v
500-character chunks with metadata and access roles
        |
        +----------------------------+
        |                            |
        v                            v
MiniLM embeddings                 BM25 index
        |                            |
        v                            |
Qdrant vector storage              |
        |                            |
        +------ 70/30 hybrid ranking
                         |
                         v
Role and active-version filtering
                         |
                         v
Answerability gate
                         |
              +----------+----------+
              |                     |
              v                     v
Citation-backed answer        Safe refusal