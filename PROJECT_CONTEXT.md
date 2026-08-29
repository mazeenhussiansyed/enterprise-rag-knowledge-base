# P02-RAG Project Context

## Identity

- **Project:** Enterprise Policy RAG Knowledge Base
- **Root:** `projects/02-enterprise-rag-knowledge-base/`
- **Status:** Active
- **Current locator:** `P02-RAG / DE / M02-INGESTION / T04-VERIFIED / NONE`
- **Next locator:** `P02-RAG / DE / M03-VECTOR-STORE / T01-MINILM / QDRANT`

## One-sentence outcome

Build an evidence-first enterprise knowledge assistant that retrieves only role-authorized policy content, cites the exact source and version, refuses unsupported questions, and exposes reproducible quality and latency metrics.

## Why this is not a clone

The public reference project supplies a useful production pattern, but this implementation adds:

1. role-based access filtering before ranking;
2. content checksums and document-version lineage;
3. an answerability threshold that can refuse weak evidence;
4. citation-completeness and access-leakage evaluation;
5. an offline deterministic test path that requires no API key or cloud service.

## Resume architecture to reproduce

- 384-dimensional `all-MiniLM-L6-v2` embeddings
- Qdrant vector storage with metadata filtering
- 70% vector plus 30% BM25 hybrid retrieval
- 20-question retrieval evaluation over 26 controlled chunks
- cited answers with relevance scores
- SSE streaming
- local Ollama model with Groq fallback
- Redis answer and BM25-index caching
- FastAPI backend, Next.js frontend and Docker deployment

The numerical resume claims remain measurement targets until the matching MiniLM/Qdrant benchmark is run in this repository and recorded in `METRICS.md`.

## Source policy

The first benchmark uses a synthetic enterprise policy pack written for this project. It contains no employer data, private information or copyrighted policy text. Public standards may be added later as clearly attributed optional sources.

## Current deliverables

- 26 versioned, role-tagged policy chunks
- 20 ground-truth retrieval questions
- deterministic 384-dimensional hashing baseline
- BM25 and configurable 70/30 hybrid retriever
- hit@1, hit@3, MRR, latency and access-control checks
- unit tests and beginner-friendly run commands
- four-format parsing with file validation and UTF-8 normalization
- SHA-256 duplicate detection and immutable version labels
- atomic ingestion ledger with active-version lineage
- 500/50 page-aware chunks persisted as JSONL

## Evidence rule

No retrieval accuracy, latency, cache speedup or reliability claim is final until the command, configuration, corpus version and output are recorded in `METRICS.md`.
