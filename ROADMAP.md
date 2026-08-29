# P02-RAG Roadmap

## M00 - Scope and evidence contract - Complete

- Define the employee-search problem, users, non-goals and security boundary.
- Freeze the evaluation protocol before tuning retrieval.
- Record every measured claim in `METRICS.md`.

## M01 - Controlled corpus and offline baseline - Complete

- Build 26 synthetic policy chunks with versions, departments and access roles.
- Write 20 answerable benchmark questions with expected chunks.
- Implement deterministic 384-dimensional hashing embeddings and BM25.
- Measure vector, BM25 and 70/30 hybrid retrieval.
- Test that unauthorized chunks never enter the candidate set.

## M02 - Production ingestion - Complete

- Parse PDF, DOCX, TXT and Markdown.
- Add file sanitization, checksums, version lineage and duplicate-safe ingestion.
- Implement 500-character chunks with 50-character overlap and page metadata.
- Preserve document title, version, effective date, department and access roles.

## M03 - MiniLM and Qdrant

- Replace the hashing baseline with `all-MiniLM-L6-v2` embeddings.
- Create the Qdrant collection with 384-dimensional cosine vectors.
- Apply role, department, status and version filters inside Qdrant.
- Compare vector-only, BM25-only and hybrid retrieval on the frozen benchmark.

## M04 - Retrieval quality

- Tune the vector/BM25 weighting without changing the test answers.
- Add optional cross-encoder reranking.
- Measure hit@1, hit@3, MRR, latency and access leakage.
- Add an answerability threshold and test refusal questions.

## M05 - Generation and citations

- Build grounded prompts using only retrieved chunks.
- Return source title, section, page, version and relevance score.
- Add citation-completeness checks and unsupported-claim detection.
- Integrate Ollama locally and Groq as a bounded fallback.

## M06 - API, streaming and cache

- Expose ingestion, query, streaming, health, stats and document endpoints.
- Stream citations before answer tokens using SSE.
- Add Redis answer caching, BM25-index caching and rate limiting.
- Benchmark cold, warm and cache-hit latency.

## M07 - Interface and deployment

- Build the Next.js upload, search, source viewer and evaluation dashboard.
- Containerize backend, frontend, Qdrant and Redis.
- Add CI, deployment configuration and a two-minute demo.

## Definition of done

- Fresh-machine quick start works.
- All automated tests pass.
- The 20-question benchmark is reproducible.
- Access-control leakage is zero on the security test set.
- Every answer shows evidence or refuses.
- Resume metrics are replaced by this repository's verified results.
