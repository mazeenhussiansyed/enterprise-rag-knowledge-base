# P02-RAG Verified Metrics

Only rows marked **Yes** may be used as measured project evidence.

## M01 baseline retrieval

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Corpus chunks | synthetic policy pack v1 | 26 | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Evaluation questions | frozen benchmark v1 | 20 | `python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
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
| Unauthorized restricted retrievals | employee attempt to retrieve `VM-02` | 0 | Qdrant integration tests | Yes, 2026-08-29 |
| Complete automated suite | unit and live integration tests | 13/13 passed | `RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v` | Yes, 2026-08-29 |
| Container persistence | restart through Docker Compose | 26/26 points retained | Qdrant count verification command | Yes, 2026-08-29 |

## M04 governed incremental synchronization

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Missing-vector recovery | ledger version present, governed collection empty | 6/6 chunks restored | governed sync command for `SEC-POLICY` v1.0 | Yes, 2026-09-01 |
| Recovery duration | MiniLM embedding and Qdrant upsert | 1,920.320 ms | first governed sync run | Yes, 2026-09-01 |
| Duplicate rerun embeddings | identical checksum and complete vector state | 0 | repeat governed sync command | Yes, 2026-09-01 |
| Duplicate rerun duration | no embedding or upsert work | 61.631 ms | repeat governed sync command | Yes, 2026-09-01 |
| Duplicate rerun speedup | recovery duration divided by skip duration | 31.16x | governed sync audit records | Yes, 2026-09-01 |
| New-version chunks | `SEC-POLICY` v1.1 | 7 | governed sync v1.1 command | Yes, 2026-09-01 |
| Historical chunks deactivated | `SEC-POLICY` v1.0 | 6 | governed sync v1.1 command | Yes, 2026-09-01 |
| Historical lineage retained | versions 1.0 and 1.1 | 13 points | Qdrant governed-state verification | Yes, 2026-09-01 |
| Inactive-version leakage | default active-only retrieval | 0 | active-version semantic query | Yes, 2026-09-01 |
| Active-version top results | quarterly access-review query | 3/3 from v1.1 | active-version semantic query | Yes, 2026-09-01 |
| Best active-version score | MiniLM cosine similarity | 0.7034 | active-version semantic query | Yes, 2026-09-01 |
| Controlled failure records | missing-document test | 1 audit + 1 quarantine | audit and quarantine verification | Yes, 2026-09-01 |
| Complete automated suite | unit and live Qdrant tests | 17/17 passed | `RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v` | Yes, 2026-09-01 |

## Benchmark integrity

- Do not edit expected chunk IDs after examining failures without creating a new benchmark version.
- Tune retrieval only on a separate development subset when the corpus grows.
- Report the 26-chunk corpus and 20-question benchmark with every accuracy result.
- Report latency as a local benchmark; do not present it as universal production performance.
- A restricted query succeeds only when unauthorized evidence is excluded before ranking.
- A refusal question succeeds only when no answer is generated from weak evidence.

## Scope warning

These results measure retrieval on a deliberately small synthetic enterprise-policy benchmark. They verify ingestion, semantic indexing, hybrid ranking, persistent vector storage and access filtering, but they do not prove production-scale accuracy. Larger held-out datasets, answer generation, citations and refusal evaluation remain separate milestones.
