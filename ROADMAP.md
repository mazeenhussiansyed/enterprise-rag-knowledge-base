# P02-RAG Roadmap

## M00 - Scope and evidence contract - Complete

- Define the enterprise-policy search problem, users, non-goals and security boundary.
- Freeze the evaluation protocol before tuning retrieval.
- Record measured claims in `METRICS.md`.

## M01 - Controlled corpus and offline baseline - Complete

- Build 26 synthetic policy chunks with versions, departments and roles.
- Write 20 ground-truth questions with expected chunks.
- Implement deterministic 384-dimensional hashing embeddings and BM25.
- Measure vector, BM25 and 70/30 hybrid retrieval.
- Test that unauthorized chunks never enter the candidate set.

## M02 - Production ingestion - Complete

- Parse PDF, DOCX, TXT and Markdown.
- Add file sanitization, checksums, version lineage and duplicate-safe ingestion.
- Implement 500-character chunks with 50-character overlap.
- Preserve document, page, version, department and role metadata.

## M03 - MiniLM and Qdrant retrieval - Complete

- Generate 384-dimensional `all-MiniLM-L6-v2` embeddings.
- Store deterministic vector points in Qdrant.
- Apply role filters before semantic ranking.
- Combine Qdrant vector retrieval with BM25 using 70/30 weights.
- Evaluate vector, BM25 and hybrid retrieval on the frozen benchmark.
- Verify persistence through Docker Compose and automated integration tests.

## M04 - Governed incremental synchronization - Complete

- Synchronize successful ingestion results directly with Qdrant.
- Add active, status, department, version and run-ID governance metadata.
- Skip complete duplicate runs without regenerating embeddings.
- Repair ledger and vector-store inconsistencies automatically.
- Deactivate previous versions while retaining historical vectors.
- Record JSONL pipeline audit metrics and failure quarantine manifests.
- Verify point counts after each synchronization.
- Test recovery, idempotency, version transitions and failure handling.

## M05 - Retrieval quality, answers and citations

- Add answerability thresholds and refusal questions.
- Evaluate optional reranking without changing frozen answers.
- Build grounded prompts using only retrieved evidence.
- Return source title, section, page, version and relevance score.
- Measure citation completeness and unsupported claims.
- Integrate a local generation provider and bounded hosted fallback.

## M06 - API, streaming and cache

- Expose ingestion, synchronization, query, health and statistics endpoints.
- Stream citations and answer tokens with Server-Sent Events.
- Add Redis caching, request validation and rate limiting.
- Benchmark cold, warm and cache-hit latency.

## M07 - Interface and deployment

- Build document upload, governed search and source-viewer screens.
- Display evaluation and pipeline-run metrics.
- Containerize the application services.
- Add CI, deployment configuration and a reproducible demonstration.

## Definition of done

- Fresh-machine quick start works.
- All automated tests pass.
- Frozen retrieval benchmarks remain reproducible.
- Access-control leakage is zero on the security test set.
- Historical document versions remain auditable.
- Every synchronization run succeeds or produces a quarantine record.
- Every generated answer shows evidence or safely refuses.
- Resume claims use only metrics verified in `METRICS.md`.