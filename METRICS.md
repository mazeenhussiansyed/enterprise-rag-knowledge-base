# P02-RAG Verified Metrics

Only rows marked **Yes** may be used as measured project evidence.

## M01 baseline retrieval

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Corpus chunks | Synthetic policy pack v1 | 26 | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Evaluation questions | Frozen benchmark v1 | 20 | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Hashing-vector hit@1 | Deterministic, 384 dimensions | 85% | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Hashing-vector hit@3 | Deterministic, 384 dimensions | 95% | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| BM25 hit@1 | k1=1.5, b=0.75 | 100% | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Baseline hybrid hit@1 | 70% vector / 30% BM25 | 95% | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Baseline hybrid hit@3 | 70% vector / 30% BM25 | 100% | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Baseline hybrid MRR | 70% vector / 30% BM25 | 0.975 | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Baseline hybrid median latency | Local warm in-memory index | 0.460 ms | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |

## M02 ingestion verification

| Check | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Supported format parsers | PDF, DOCX, TXT, Markdown | 4/4 | `python -m unittest discover -s tests -v` | Yes, 2026-08-20 |
| Automated baseline suite | Corpus, retrieval, security, ingestion | 9/9 passed | `python -m unittest discover -s tests -v` | Yes, 2026-08-20 |
| Sample policy chunking | 500 characters / 50 overlap | 6 chunks | `python scripts/ingest_document.py ...` | Yes, 2026-08-20 |
| Identical-file handling | SHA-256 comparison | Duplicate detected | Rerun the sample ingestion command | Yes, 2026-08-20 |
| Unauthorized filename case | Traversal input | Rejected | Ingestion unit tests | Yes, 2026-08-20 |
| Same-version changed content | Immutable version label | Rejected | Ingestion unit tests | Yes, 2026-08-20 |

## M03 MiniLM and Qdrant verification

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Embedding dimensions | `all-MiniLM-L6-v2`, ONNX/FastEmbed | 384 | MiniLM provider verification command | Yes, 2026-08-29 |
| Embedding normalization | L2 norm | 1.0 | MiniLM provider verification command | Yes, 2026-08-29 |
| Persistent vector points | Qdrant v1.19.0 | 26 | `python scripts/index_corpus_qdrant.py` | Yes, 2026-08-29 |
| Initial indexing throughput | Collection creation plus 26 chunks | 18.50 chunks/s | `python scripts/index_corpus_qdrant.py` | Yes, 2026-08-29 |
| Warm idempotent upsert throughput | Existing collection and cached model | 89.49 chunks/s | Rerun `python scripts/index_corpus_qdrant.py` | Yes, 2026-08-29 |
| Duplicate points after re-indexing | Deterministic UUID upserts | 0 | Rerun `python scripts/index_corpus_qdrant.py` | Yes, 2026-08-29 |
| MiniLM/Qdrant hit@1 | 20-question benchmark v1 | 100% | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| MiniLM/Qdrant hit@3 | 20-question benchmark v1 | 100% | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| MiniLM/Qdrant MRR | 20-question benchmark v1 | 1.000 | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| MiniLM/Qdrant median latency | Local warm model and Qdrant | 25.614 ms | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| MiniLM/Qdrant p95 latency | Local warm model and Qdrant | 42.301 ms | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| Production hybrid hit@1 | 70% MiniLM/Qdrant, 30% BM25 | 100% | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| Production hybrid hit@3 | 70% MiniLM/Qdrant, 30% BM25 | 100% | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| Production hybrid MRR | 70% MiniLM/Qdrant, 30% BM25 | 1.000 | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| Production hybrid median latency | Local warm model and Qdrant | 15.940 ms | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| Production hybrid p95 latency | Local warm model and Qdrant | 24.991 ms | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| Unauthorized restricted retrievals | Employee attempt to retrieve `VM-02` | 0 | Qdrant integration tests | Yes, 2026-08-29 |
| Complete automated suite | Unit and live integration tests | 13/13 passed | `RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v` | Yes, 2026-08-29 |
| Container persistence | Restart through Docker Compose | 26/26 points retained | Qdrant count verification command | Yes, 2026-08-29 |

## M04 governed incremental synchronization

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Duplicate synchronization | Identical `SEC-POLICY` v1.0 source | 0 re-embedded; 6 existing vectors retained | Rerun `python scripts/sync_document.py ...` | Yes, 2026-09-01 |
| New-version synchronization | `SEC-POLICY` v1.1 | 7 indexed; 6 earlier-version chunks deactivated | `python scripts/sync_document.py ...` | Yes, 2026-09-01 |
| Historical version retention | `SEC-POLICY` v1.0 to v1.1 | 13 total vectors; 7 active v1.1 vectors | Qdrant payload verification command | Yes, 2026-09-01 |
| Failure audit and quarantine | Missing source-file simulation | Audit record and quarantine record created | Invalid-source synchronization command | Yes, 2026-09-01 |
| Governed sync test suite | Unit plus live Qdrant integration | 17/17 passed | `RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v` | Yes, 2026-09-01 |

## M05 grounded answers, citations and refusals

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Answerable questions | Controlled policy benchmark | 20 | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Answered with citations | MiniLM/Qdrant + BM25, top 3 | 20/20 | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Answer rate | Controlled 20-question benchmark | 100% | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Citation presence rate | Cited answers / answerable questions | 100% | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Expected-citation recall | Expected chunk present in citation list | 100% | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Unsupported questions | Controlled refusal set | 3 | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Safe-refusal rate | Unsupported questions refused | 100% (3/3) | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Unsafe answers | Unsupported answers with generated evidence | 0 | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| End-to-end median latency | 23 local warm questions | 16.620 ms | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| End-to-end p95 latency | 23 local warm questions | 31.312 ms | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Complete automated suite | Answer, ingestion, sync and live Qdrant tests | 22/22 passed | `RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v` | Yes, 2026-09-01 |

## M06 API and interactive demo

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| FastAPI endpoint contract | Root, health, stats, search and ask | 5 endpoints | `uvicorn enterprise_rag.api:app --host 127.0.0.1 --port 8000` | Yes, 2026-09-01 |
| API endpoint tests | FastAPI `TestClient` with deterministic fakes | 5/5 passed | `python -m unittest tests/test_api.py -v` | Yes, 2026-09-01 |
| Complete automated suite | Unit, API and live Qdrant integration tests | 27/27 passed | `RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v` | Yes, 2026-09-01 |
| Interactive demo answered scenarios | MFA, privileged access and vendor-contract examples | 3/3 role-matched answers | `python scripts/run_demo.py` | Yes, 2026-09-01 |
| Interactive demo refusal scenario | Unsupported cafeteria question | 1/1 safe refusal | `python scripts/run_demo.py` | Yes, 2026-09-01 |
| Local service exposure | FastAPI and Gradio loopback services | `127.0.0.1:8000`, `127.0.0.1:7860` | Launch commands in README | Yes, 2026-09-01 |
## M07 containerized deployment and continuous integration

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Containerized services | Qdrant, indexer, API and Gradio demo | 4 services | `docker compose up --build -d --wait --wait-timeout 180` | Yes, 2026-09-01 |
| Corpus indexing in Compose | MiniLM plus Qdrant | 26 stored points | `curl -sS http://127.0.0.1:8000/health` | Yes, 2026-09-01 |
| Containerized API health | FastAPI `/health` | `status: ok` | `curl -sS http://127.0.0.1:8000/health` | Yes, 2026-09-01 |
| Persistent model cache | Docker named volume | Warm rebuild completed successfully | `docker compose up --build -d --wait --wait-timeout 180` | Yes, 2026-09-01 |
| Complete local test suite | Unit, API and live Qdrant tests | 27/27 passed | `RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v` | Yes, 2026-09-01 |
| GitHub Actions workflow | Docker build, health validation and tests | Configured | `.github/workflows/verify.yml` | No — pending first green run |

## Benchmark integrity

- Do not change expected chunk IDs after examining failures without creating a new benchmark version.
- Report corpus size and evaluation-question count with every quality metric.
- Report latency as local-machine evidence, not universal production performance.
- Role filtering succeeds only when unauthorized evidence is excluded before ranking.
- A refusal succeeds only when no unsupported answer or citation is returned.
- The M05 answerability thresholds were calibrated on the controlled benchmark; evaluate a held-out corpus before making broad quality claims.

## Scope warning

These results measure a deliberately small synthetic enterprise-policy corpus. They verify ingestion, semantic indexing, hybrid ranking, persistent vector storage, governed synchronization, citation-backed answers, safe refusals, API behavior and an interactive local demonstration.

They do not prove production-scale accuracy, authenticated authorization, cloud-scale latency or production operational readiness. A production deployment still requires identity-derived roles, secrets management, rate limiting, observability, larger held-out datasets and human answer review.