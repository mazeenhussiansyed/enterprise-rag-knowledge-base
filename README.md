# Enterprise Policy RAG Knowledge Base

An evidence-first enterprise policy RAG system with governed document ingestion, MiniLM embeddings, Qdrant vector storage, BM25 hybrid retrieval, role-aware filtering, grounded answers, citations, safe refusals, a FastAPI service and an interactive local web demo.

The repository separates ingestion, storage, retrieval, answer generation and evaluation so that each layer can be tested and measured independently.

## Current status

Completed capabilities:

- 26 synthetic enterprise-policy chunks with role and version metadata
- 20-question frozen retrieval and answer benchmark
- PDF, DOCX, TXT and Markdown ingestion
- SHA-256 duplicate detection and immutable document-version lineage
- 500-character chunks with 50-character overlap
- MiniLM semantic embeddings using `all-MiniLM-L6-v2`
- persistent Qdrant vector storage with deterministic point IDs
- BM25, vector-only and 70/30 hybrid retrieval
- role filtering before retrieval ranking
- governed incremental synchronization with audit records and quarantine manifests
- citation-backed extractive answers and safe refusal behavior
- FastAPI endpoints for service health, statistics, retrieval and answers
- Gradio-based local web interface for an interactive demonstration

The corpus is deliberately small and synthetic. Results demonstrate reproducible system behavior, not production-scale accuracy.

## Verified quality results

| Capability | Result |
|---|---:|
| Corpus size | 26 policy chunks |
| Frozen answerable benchmark | 20 questions |
| MiniLM/Qdrant hybrid hit@1 | 100% |
| MiniLM/Qdrant hybrid hit@3 | 100% |
| MiniLM/Qdrant hybrid MRR | 1.000 |
| Expected citation recall | 100% (20/20) |
| Safe refusal rate | 100% (3/3) |
| Unauthorized restricted retrievals | 0 |
| Full automated suite | 27/27 passed |

See [METRICS.md](METRICS.md) for reproducible evidence and limitations.

## Architecture

```text
Enterprise documents
        |
        v
Validation, parsing, checksums and version lineage
        |
        v
500-character chunks with 50-character overlap
        |
        +-------------------------+
        |                         |
        v                         v
MiniLM embeddings             BM25 index
        |                         |
        v                         |
Qdrant vector storage          |
        |                         |
        +---- role-aware hybrid retrieval
                           |
                           v
Answerability gate -> grounded extractive answer -> citations or safe refusal
                           |
                           v
FastAPI service -> Swagger API docs and local Gradio demo