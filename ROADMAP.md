# P02-RAG Roadmap

## M00 — Scope and evidence contract — Complete

- Defined the enterprise-policy retrieval problem, users, non-goals and security boundary.
- Froze the evaluation protocol before retrieval tuning.
- Recorded measurable claims in `METRICS.md`.

## M01 — Controlled corpus and offline baseline — Complete

- Built 26 synthetic policy chunks with versions, departments and roles.
- Created 20 ground-truth questions with expected chunks.
- Implemented deterministic hashing embeddings, BM25 and hybrid retrieval.
- Measured retrieval quality and verified zero access-control leakage.

## M02 — Production ingestion — Complete

- Parsed PDF, DOCX, TXT and Markdown.
- Added filename validation, checksums, version lineage and duplicate-safe ingestion.
- Implemented page-aware 500-character chunks with 50-character overlap.
- Preserved document, page, version, department and role metadata.

## M03 — MiniLM and Qdrant retrieval — Complete

- Generated 384-dimensional `all-MiniLM-L6-v2` embeddings.
- Stored deterministic vector points in Qdrant.
- Combined semantic Qdrant retrieval with BM25 using 70/30 hybrid ranking.
- Verified 100% hit@1, hit@3 and MRR on the controlled benchmark.

## M04 — Governed incremental synchronization — Complete

- Synchronized ingested documents directly with Qdrant.
- Added active, status, department, version and run-ID governance metadata.
- Skipped duplicate runs and repaired missing vector state.
- Retained historical versions while deactivating superseded chunks.
- Recorded audit records and quarantine manifests for failures.

## M05 — Grounded answers, citations and refusals — Complete

- Added answerability thresholds and refusal questions.
- Returned extractive answers only from authorized retrieved evidence.
- Returned citations with source, section, version, relevance score and excerpt.
- Verified 20/20 expected citations and 3/3 safe refusals.

## M06 — API and interactive demo — Complete

- Added FastAPI endpoints for service health, statistics, search and answers.
- Added Swagger API documentation and request validation.
- Added a role-aware Gradio interface for local demonstrations.
- Verified API behavior with automated endpoint tests.

## M07 — Containerized deployment and CI — Complete

- Containerized Qdrant, corpus indexing, FastAPI and Gradio services.
- Added persistent Qdrant and model-cache volumes.
- Added API health checks and dependency-aware startup ordering.
- Made `docker compose up --build -d --wait --wait-timeout 180` reproducible.
- Added GitHub Actions to build the stack, verify health and run all tests.
- Verified the local containerized stack with 26 stored points and 27 passing tests.

## Future production hardening

- Derive roles from authenticated identity instead of a request field.
- Add governed ingestion and synchronization API endpoints.
- Add streaming responses, Redis caching, rate limiting and request telemetry.
- Add secrets management, monitoring and public cloud deployment.
- Evaluate on a larger held-out corpus with adversarial tests and human review.

## Definition of done

- Fresh-machine Docker quick start works.
- Automated tests and frozen benchmarks remain reproducible.
- Access-control leakage remains zero on the security test set.
- Historical document versions remain auditable.
- Every returned answer includes authorized evidence or safely refuses.
- Resume claims use only metrics verified in `METRICS.md`.