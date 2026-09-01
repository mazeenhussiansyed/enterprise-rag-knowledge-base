# P02-RAG Roadmap

## M00 - Scope and Evidence Contract - Complete

- Defined the enterprise-policy search problem, users, non-goals, and security boundary.
- Established controlled benchmark data and evidence-recording rules.
- Recorded verified claims in `METRICS.md`.

## M01 - Controlled Corpus and Offline Baseline - Complete

- Built 26 synthetic policy chunks with versions, departments, and access roles.
- Wrote 20 ground-truth questions with expected evidence chunks.
- Implemented deterministic 384-dimensional hashing vectors and BM25.
- Measured vector, BM25, and 70/30 hybrid retrieval.
- Verified that unauthorized chunks do not enter the candidate set.

## M02 - Production Ingestion - Complete

- Parsed PDF, DOCX, TXT, and Markdown documents.
- Added filename validation, SHA-256 checksums, duplicate detection, and immutable version lineage.
- Implemented page-aware 500-character chunks with 50-character overlap.
- Preserved document title, version, effective date, department, role, and source metadata.

## M03 - MiniLM and Qdrant Retrieval - Complete

- Generated 384-dimensional `all-MiniLM-L6-v2` embeddings.
- Stored deterministic vector points in Qdrant.
- Applied role filters before semantic ranking.
- Combined Qdrant vector retrieval and BM25 with 70/30 weights.
- Evaluated vector, BM25, and hybrid retrieval on the controlled benchmark.
- Verified Docker Compose persistence and live Qdrant integration tests.

## M04 - Governed Incremental Synchronization - Complete

- Synchronized successful ingestion results directly with Qdrant.
- Added active, status, department, version, and run-ID governance metadata.
- Skipped complete duplicate runs without regenerating embeddings.
- Repaired ledger and vector-store inconsistencies automatically.
- Deactivated previous versions while retaining historical vectors.
- Recorded JSONL pipeline audit records and failure-quarantine manifests.
- Tested recovery, idempotency, version transitions, and failure handling.

## M05 - Grounded Answers, Citations, and Refusals - Complete

- Added a retrieval answerability gate with vector, hybrid-score, and topic-grounding checks.
- Normalized meaningful policy word variants such as `passwords/password`, `sharing/share`, and `agreements/agreement`.
- Created citation-backed extractive answers from authorized source sentences only.
- Returned source title, section, page, version, effective date, evidence excerpt, and relevance score.
- Refused unsupported questions without returning citations or unrelated policy text.
- Evaluated 20 answerable questions and verified expected-citation recall.
- Evaluated three unsupported questions and verified safe-refusal behavior.
- Verified the complete unit and live Qdrant test suite.

## M06 - API, Streaming, and Local Demonstration

- Build FastAPI endpoints for health, statistics, search, answer, ingestion, and synchronization.
- Expose interactive API documentation through FastAPI Swagger UI.
- Build a chat-style local demonstration interface using Gradio.
- Add request validation, structured error responses, and operational logging.
- Add Redis caching, rate limiting, and Server-Sent Events where useful.
- Benchmark cold, warm, and cache-hit behavior.
- Add an optional local LLM provider behind the existing evidence and citation controls.

## M07 - Interface, CI, and Deployment

- Build document upload, governed search, source-viewer, and evaluation-metrics screens.
- Containerize the API, demonstration interface, Qdrant, and cache services.
- Add continuous integration for unit and integration tests.
- Add deployment configuration and a reproducible two-minute demonstration.
- Expand evaluation with held-out documents, adversarial requests, and human answer-quality review.

## Final Definition of Done

- A fresh-machine quick start succeeds.
- All automated tests pass.
- Controlled retrieval and answer benchmarks remain reproducible.
- Access-control leakage is zero on the security test set.
- Historical document versions remain auditable.
- Every synchronization run succeeds or produces audit and quarantine evidence.
- Every answer provides supporting evidence or safely refuses.
- The API and chat-style demonstration run locally through Docker Compose.
- Resume claims use only metrics verified in `METRICS.md`.