# P02-RAG Roadmap

## M00 - Scope and evidence contract - Complete

- Defined the enterprise-policy retrieval problem, users, non-goals and security boundary.
- Froze the evaluation protocol before retrieval tuning.
- Recorded measurable claims in `METRICS.md`.

## M01 - Controlled corpus and offline baseline - Complete

- Built 26 synthetic policy chunks with versions, departments and roles.
- Created 20 ground-truth questions with expected chunks.
- Implemented deterministic 384-dimensional hashing embeddings and BM25.
- Measured vector, BM25 and 70/30 hybrid retrieval.
- Tested that unauthorized chunks never enter the candidate set.

## M02 - Production ingestion - Complete

- Parsed PDF, DOCX, TXT and Markdown.
- Added file sanitization, checksums, version lineage and duplicate-safe ingestion.
- Implemented 500-character chunks with 50-character overlap.
- Preserved document, page, version, department and role metadata.

## M03 - MiniLM and Qdrant retrieval - Complete

- Generated 384-dimensional `all-MiniLM-L6-v2` embeddings.
- Stored deterministic vector points in Qdrant.
- Applied role filters before semantic ranking.
- Combined Qdrant vector retrieval with BM25 using 70/30 weights.
- Evaluated vector, BM25 and hybrid retrieval on the frozen benchmark.
- Verified persistence through Docker Compose and integration tests.

## M04 - Governed incremental synchronization - Complete

- Synchronized successful ingestion results directly with Qdrant.
- Added active, status, department, version and run-ID governance metadata.
- Skipped complete duplicate runs without regenerating embeddings.
- Repaired ledger and vector-store inconsistencies automatically.
- Deactivated previous versions while retaining historical vectors.
- Recorded JSONL pipeline audit metrics and failure quarantine manifests.
- Tested recovery, idempotency, version transitions and failure handling.

## M05 - Grounded answers, citations and refusals - Complete

- Added answerability thresholds and a controlled refusal-question set.
- Returned extractive answers only from authorized retrieved evidence.
- Returned source title, section, version, date, relevance score and excerpt.
- Verified expected-citation recall on the 20-question benchmark.
- Verified safe refusal behavior on unsupported questions.
- Kept the implementation local and deterministic without requiring a hosted LLM.

## M06 - API and interactive local demo - Complete for the demo scope

- Added FastAPI endpoints for service description, health, statistics, retrieval and answers.
- Added automatic Swagger and ReDoc API documentation.
- Added request validation and stable JSON response contracts.
- Added FastAPI endpoint tests without requiring a live server.
- Added a Gradio interface that calls the FastAPI `/ask` endpoint.
- Demonstrated role-aware answers, citations and safe refusal behavior locally.
- Verified the complete unit and live Qdrant suite: 27/27 tests passed.

## Future production hardening

- Derive roles from authenticated identity instead of a request field.
- Add API endpoints for governed ingestion and synchronization.
- Stream answer and citation events with Server-Sent Events.
- Add Redis caching, rate limits and structured request telemetry.
- Add API authentication, authorization and secret management.
- Add a larger held-out corpus, adversarial evaluation and human answer review.
- Containerize the API and web application together with reproducible deployment configuration.

## Definition of done

- Fresh-machine quick start works.
- Automated tests pass.
- Frozen retrieval and answer benchmarks remain reproducible.
- Access-control leakage is zero on the controlled security test set.
- Historical document versions remain auditable.
- Every synchronization run succeeds or produces a quarantine record.
- Every returned answer includes authorized evidence or safely refuses.
- Resume claims use only metrics verified in `METRICS.md`.