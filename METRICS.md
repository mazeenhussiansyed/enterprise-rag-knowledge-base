# P02-RAG Verified Metrics

Only rows marked **Yes** may be used as measured project evidence.

| Metric | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Corpus chunks | synthetic policy pack v1 | 26 | `PYTHONPATH=src python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Evaluation questions | benchmark v1 | 20 | `PYTHONPATH=src python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Hashing-vector hit@1 | deterministic, 384 dimensions | 85% | `PYTHONPATH=src python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Hashing-vector hit@3 | deterministic, 384 dimensions | 95% | `PYTHONPATH=src python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| BM25 hit@1 | k1=1.5, b=0.75 | 100% | `PYTHONPATH=src python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Hybrid hit@1 | 70% vector / 30% BM25 | 95% | `PYTHONPATH=src python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Hybrid hit@3 | 70% vector / 30% BM25 | 100% | `PYTHONPATH=src python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Hybrid MRR | 70% vector / 30% BM25 | 0.975 | `PYTHONPATH=src python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Hybrid median latency | local, warm in-memory index | 0.460 ms | `PYTHONPATH=src python scripts/evaluate_retrieval.py` | Yes, 2026-08-20 |
| Unauthorized retrievals | restricted VM-02 role test | 0 | `PYTHONPATH=src python -m unittest discover -s tests -v` | Yes, 2026-08-20 |
| MiniLM hit@1 | `all-MiniLM-L6-v2` + Qdrant | target 90% | future M03 command | No |
| MiniLM hit@3 | `all-MiniLM-L6-v2` + Qdrant | target 100% | future M03 command | No |
| Repeated hybrid latency | cached BM25 | target near 9 ms | future M06 benchmark | No |

## M02 ingestion verification

| Check | Configuration | Result | Evidence command | Verified |
|---|---|---:|---|---|
| Supported format parsers | PDF, DOCX, TXT, Markdown | 4/4 | `PYTHONPATH=src python -m unittest discover -s tests -v` | Yes, 2026-08-20 |
| Complete automated suite | corpus, retrieval, security, ingestion | 9/9 passed | `PYTHONPATH=src python -m unittest discover -s tests -v` | Yes, 2026-08-20 |
| Sample policy chunking | 500 characters / 50 overlap | 6 chunks | `PYTHONPATH=src python scripts/ingest_document.py ...` | Yes, 2026-08-20 |
| Identical-file handling | SHA-256 comparison | duplicate detected | rerun the sample ingestion command | Yes, 2026-08-20 |
| Unauthorized filename case | traversal input | rejected | ingestion unit tests | Yes, 2026-08-20 |
| Same-version changed content | immutable version label | rejected | ingestion unit tests | Yes, 2026-08-20 |

## Benchmark integrity

- Do not edit expected chunk IDs after looking at model failures without recording a benchmark version change.
- Tune retrieval only on a separate development subset once the corpus grows.
- Report the corpus size with every accuracy result.
- A refusal question is successful only when no answer is generated from weak evidence.

## Scope warning

These results measure retrieval on a deliberately small synthetic benchmark. They prove that the evaluation plumbing, access filter and baseline ranking work; they do not yet prove production-scale accuracy. The MiniLM/Qdrant and larger held-out evaluations remain separate milestones.
