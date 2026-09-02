# Enterprise Policy RAG Knowledge Base

An evidence-first enterprise policy RAG system with governed document ingestion, MiniLM embeddings, Qdrant vector storage, BM25 hybrid retrieval, role-aware filtering, grounded answers, citations, safe refusals, a FastAPI service, an interactive web demo, Docker deployment and continuous integration.

## Completed capabilities

- 26 synthetic enterprise-policy chunks with role and version metadata
- 20-question frozen retrieval and answer benchmark
- PDF, DOCX, TXT and Markdown ingestion
- SHA-256 duplicate detection and immutable document-version lineage
- 500-character chunks with 50-character overlap
- MiniLM semantic embeddings using `all-MiniLM-L6-v2`
- Persistent Qdrant vector storage with deterministic point IDs
- Vector-only, BM25 and 70/30 hybrid retrieval
- Role filtering before retrieval ranking
- Governed incremental synchronization, audit records and failure quarantine
- Citation-backed extractive answers and safe refusal behavior
- FastAPI endpoints for health, statistics, search and answers
- Gradio-based interactive local demonstration
- Docker Compose stack with Qdrant, indexer, API and demo services
- GitHub Actions workflow for containerized verification

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
| Complete automated suite | 27/27 passed |
| Containerized API health | 26 stored vectors |

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
Answerability gate -> grounded answer -> citations or safe refusal
                           |
                           v
FastAPI service -> Swagger docs and Gradio demonstration
                           |
                           v
Docker Compose -> GitHub Actions verification