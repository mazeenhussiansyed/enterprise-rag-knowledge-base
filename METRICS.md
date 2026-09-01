# P02-RAG Verified Metrics

Only rows marked **Yes** may be used as measured project evidence.

## M01 baseline retrieval

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Corpus chunks | synthetic policy pack v1 | 26 | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Evaluation questions | benchmark v1 | 20 | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Hashing-vector hit@1 | deterministic, 384 dimensions | 85% | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Hashing-vector hit@3 | deterministic, 384 dimensions | 95% | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| BM25 hit@1 | k1=1.5, b=0.75 | 100% | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Baseline hybrid hit@1 | 70% vector / 30% BM25 | 95% | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Baseline hybrid hit@3 | 70% vector / 30% BM25 | 100% | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Baseline hybrid MRR | 70% vector / 30% BM25 | 0.975 | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Baseline hybrid median latency | local warm in-memory index | 0.460 ms | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |

## M02 ingestion verification

| Check | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Supported format parsers | PDF, DOCX, TXT, Markdown | 4/4 | `python -m unittest discover -s tests -v` | Yes, 2026-08-20 |
| Automated baseline suite | corpus, retrieval, security, ingestion | 9/9 passed | `python -m unittest discover -s tests -v` | Yes, 2026-08-20 |
| Sample policy chunking | 500 characters / 50 overlap | 6 chunks | `python scripts/ingest_document.py ...` | Yes, 2026-08-20 |
| Identical-file handling | SHA-256 comparison | duplicate detected | rerun the sample ingestion command | Yes, 2026-08-20 |
| Unauthorized filename case | traversal input | rejected | ingestion unit tests | Yes, 2026-08-20 |
| Same-version changed content | immutable version label | rejected | ingestion unit tests | Yes, 2026-08-20 |

## M03 MiniLM and Qdrant verification

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Embedding dimensions | `all-MiniLM-L6-v2`, ONNX/FastEmbed | 384 | MiniLM provider verification command | Yes, 2026-08-29 |
| Embedding normalization | L2 norm | 1.0 | MiniLM provider verification command | Yes, 2026-08-29 |
| Persistent vector points | Qdrant v1.19.0 | 26 | `python scripts/index_corpus_qdrant.py` | Yes, 2026-08-29 |
| Initial indexing throughput | collection creation plus 26 chunks | 18.50 chunks/s | `python scripts/index_corpus_qdrant.py` | Yes, 2026-08-29 |
| Warm idempotent upsert throughput | existing collection and cached model | 89.49 chunks/s | rerun `python scripts/index_corpus_qdrant.py` | Yes, 2026-08-29 |
| Duplicate points after re-indexing | deterministic UUID upserts | 0 | rerun `python scripts/index_corpus_qdrant.py` | Yes, 2026-08-29 |
| MiniLM/Qdrant hit@1 | 20-question benchmark v1 | 100% | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| MiniLM/Qdrant hit@3 | 20-question benchmark v1 | 100% | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| MiniLM/Qdrant MRR | 20-question benchmark v1 | 1.000 | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| MiniLM/Qdrant median latency | local warm model and Qdrant | 25.614 ms | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| MiniLM/Qdrant p95 latency | local warm model and Qdrant | 42.301 ms | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| Production hybrid hit@1 | 70% MiniLM/Qdrant, 30% BM25 | 100% | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| Production hybrid hit@3 | 70% MiniLM/Qdrant, 30% BM25 | 100% | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| Production hybrid MRR | 70% MiniLM/Qdrant, 30% BM25 | 1.000 | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| Production hybrid median latency | local warm model and Qdrant | 15.940 ms | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |
| Production hybrid p95 latency | local warm model and Qdrant | 24.991 ms | `python scripts/evaluate_qdrant.py` | Yes, 2026-08-29 |

## M04 governed incremental synchronization

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Duplicate synchronization | identical `SEC-POLICY` v1.0 source | 0 re-embedded; 6 existing vectors retained | rerun `python scripts/sync_document.py ...` | Yes, 2026-09-01 |
| New-version synchronization | `SEC-POLICY` v1.1 | 7 indexed; 6 earlier-version chunks deactivated | `python scripts/sync_document.py ...` | Yes, 2026-09-01 |
| Historical version retention | `SEC-POLICY` v1.0 to v1.1 | 13 total vectors; 7 active v1.1 vectors | Qdrant payload verification command | Yes, 2026-09-01 |
| Failure audit and quarantine | missing source-file simulation | audit record and quarantine record created | invalid-source synchronization command | Yes, 2026-09-01 |
| Governed sync test suite | unit plus live Qdrant integration | 17/17 passed | `RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v` | Yes, 2026-09-01 |

## M05 grounded answers, citations and refusals

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Answerable questions | controlled policy benchmark | 20 | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Answered with citations | MiniLM/Qdrant + BM25, top 3 | 20/20 | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Answer rate | controlled 20-question benchmark | 100% | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Citation presence rate | cited answers / answerable questions | 100% | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Expected-citation recall | expected chunk present in citation list | 100% | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Unsupported questions | controlled refusal set | 3 | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Safe-refusal rate | unsupported questions refused | 100% (3/3) | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Unsafe answers | unsupported answers with generated evidence | 0 | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| End-to-end median latency | 23 local warm questions | 16.620 ms | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| End-to-end p95 latency | 23 local warm questions | 31.312 ms | `python scripts/evaluate_answers.py` | Yes, 2026-09-01 |
| Complete automated suite | answer, ingestion, governed sync and live Qdrant tests | 22/22 passed | `RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v` | Yes, 2026-09-01 |

## Benchmark Integrity

- Do not change expected chunk IDs after examining failures without creating a new benchmark version.
- Report the corpus size and evaluation-question count with every quality metric.
- Report local latency as a local benchmark, not universal production performance.
- Authorization is successful only when unauthorized evidence is excluded before ranking.
- A refusal is successful only when no unsupported answer or citation is returned.
- The M05 answerability thresholds were calibrated on the controlled benchmark; use a held-out evaluation before making production-scale quality claims.

## Scope Warning

These results measure a deliberately small, synthetic enterprise-policy corpus. They verify ingestion, semantic indexing, hybrid ranking, persistent vector storage, access filtering, governed synchronization, citation-backed extractive answers, and refusal behavior.

They do not prove production-scale accuracy, general factual correctness, or cloud-scale latency. Larger held-out datasets, adversarial testing, human answer review, an LLM provider, API observability, and deployment remain separate milestones.