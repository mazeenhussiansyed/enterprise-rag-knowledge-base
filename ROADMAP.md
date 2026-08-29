# P02-RAG Roadmap

## Current checkpoint

Milestones M00–M03 are complete. The project currently provides document ingestion, persistent semantic indexing, role-filtered hybrid retrieval, evidence output and reproducible evaluation.

The next milestone is M04: retrieval robustness, optional metadata filters and refusal evaluation.

## M00 - Scope and evidence contract - Complete

- Defined the employee-policy search problem and security boundary.
- Froze the evaluation protocol before production retrieval changes.
- Required every measured claim to be recorded in `METRICS.md`.
- Separated verified metrics from targets and future claims.

## M01 - Controlled corpus and offline baseline - Complete

- Built 26 synthetic policy chunks with versions, departments and access roles.
- Created 20 answerable benchmark questions with expected chunks.
- Implemented deterministic 384-dimensional hashing embeddings.
- Implemented BM25 keyword retrieval.
- Implemented 70% vector and 30% BM25 score fusion.
- Measured Hit@1, Hit@3, MRR and latency.
- Verified that unauthorized chunks do not enter the baseline candidate set.

## M02 - Production ingestion - Complete

- Parse PDF, DOCX, TXT and Markdown.
- Sanitize filenames and reject path traversal.
- Validate document metadata.
- Calculate SHA-256 file checksums.
- Detect identical duplicate files.
- Reject changed content that reuses an immutable version.
- Preserve document-version lineage.
- Generate page-aware 500-character chunks with 50-character overlap.
- Write chunk output atomically.
- Maintain an ingestion ledger.

## M03 - MiniLM and Qdrant - Complete, 2026-08-29

- Added `all-MiniLM-L6-v2` through FastEmbed and ONNX Runtime.
- Verified normalized 384-dimensional semantic vectors.
- Added Qdrant Python client v1.19.0.
- Deployed Qdrant v1.19.0 through Docker.
- Added persistent named-volume storage.
- Added reproducible `compose.yaml` infrastructure.
- Created a 384-dimensional cosine-distance collection.
- Indexed roles, chunk IDs, document IDs, departments and versions.
- Used deterministic UUIDs for duplicate-safe upserts.
- Indexed and retained all 26 benchmark chunks.
- Enforced role filtering inside Qdrant.
- Combined Qdrant candidates with authorized BM25 results.
- Added a command-line evidence-search interface.
- Compared vector, BM25 and hybrid retrieval on the frozen benchmark.
- Achieved 100% Hit@1, 100% Hit@3 and 1.000 MRR for production hybrid retrieval.
- Verified zero restricted `VM-02` leakage to the employee role.
- Passed 13 unit and live integration tests.
- Recorded all measured results in `METRICS.md`.

## M04 - Retrieval robustness and refusal - Next

- Add optional department and document-version query filters.
- Propagate active/inactive document status into chunk payloads.
- Build separate development and held-out evaluation subsets.
- Add paraphrased, ambiguous, adversarial and unanswerable questions.
- Add an evidence-strength answerability threshold.
- Test refusal behavior when evidence is absent or weak.
- Measure access leakage across every restricted role.
- Repeat latency measurements across multiple benchmark runs.
- Add optional cross-encoder reranking only if larger evaluations show a measurable benefit.
- Avoid tuning against frozen expected answers.

## M05 - Generation and citations - Planned

- Build grounded prompts using only authorized retrieved evidence.
- Generate natural-language answers from accepted evidence.
- Return source title, section, page, version and relevance score.
- Add inline citations.
- Validate citation completeness.
- Detect unsupported factual claims.
- Refuse answers when evidence does not pass the threshold.
- Integrate a local generation provider.
- Evaluate any hosted fallback separately before enabling it.

## M06 - API, streaming and cache - Planned

- Expose ingestion, query, health, statistics and document endpoints.
- Add structured request and response validation.
- Stream citations before answer tokens using Server-Sent Events.
- Add rate limiting and request logging.
- Add Redis caching only after retrieval and generation correctness are stable.
- Benchmark cold, warm and cache-hit latency.

## M07 - Interface, CI and deployment - Planned

- Build document upload and search interfaces.
- Add a source and citation viewer.
- Add an evaluation dashboard.
- Containerize the complete application stack.
- Add automated CI for unit tests and integration tests.
- Add deployment configuration.
- Record a reproducible two-minute demonstration.

## Retrieval milestone definition of done

- MiniLM generates normalized 384-dimensional embeddings.
- Qdrant persists vectors across container replacement.
- Re-indexing does not create duplicate points.
- Vector, BM25 and hybrid strategies are independently measurable.
- Role filtering prevents restricted-vector leakage.
- Search results contain evidence and lineage metadata.
- All 13 retrieval and ingestion tests pass.
- Setup and execution commands are documented.
- Verified metrics are recorded without production-scale overclaims.

## Final project definition of done

- Fresh-machine quick start is independently verified.
- A larger held-out benchmark is reproducible.
- Access-control leakage is zero across the security test set.
- Unsupported questions are refused.
- Every generated answer contains validated evidence citations.
- API and interface tests pass.
- CI executes unit and integration checks.
- Resume metrics are supported by repository evidence.