# M03 Evaluation: MiniLM, Qdrant and Hybrid Retrieval

**Evaluation date:** 2026-08-29  
**Benchmark version:** v1

## Objective

Replace the deterministic hashing baseline with genuine semantic embeddings, persist vectors in Qdrant, enforce role authorization and evaluate vector, BM25 and hybrid retrieval.

## Environment

| Component | Configuration |
|---|---|
| Python | 3.14.4 |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding runtime | FastEmbed 0.8.0 |
| Inference engine | ONNX Runtime 1.29.0 |
| Qdrant server/client | 1.19.0 |
| Vector configuration | 384 dimensions, cosine distance |
| Hybrid weighting | 70% vector, 30% BM25 |
| Benchmark | 26 chunks, 20 questions |

## Embedding verification

The production provider generated two normalized MiniLM vectors:

| Check | Result |
|---|---:|
| Vectors generated | 2 |
| Dimensions per vector | 384 |
| First-vector L2 norm | 1.0 |

## Indexing verification

| Run | Collection created | Indexed chunks | Stored points | Throughput |
|---|---:|---:|---:|---:|
| Initial | Yes | 26 | 26 | 18.50 chunks/s |
| Idempotent rerun | No | 26 | 26 | 89.49 chunks/s |

The second run retained exactly 26 points, proving that deterministic UUID upserts did not create duplicates.

## Retrieval results

| Strategy | Hit@1 | Hit@3 | MRR | Median latency | P95 latency | Failures |
|---|---:|---:|---:|---:|---:|---:|
| MiniLM/Qdrant | 100% | 100% | 1.000 | 25.614 ms | 42.301 ms | 0 |
| BM25 | 100% | 100% | 1.000 | 0.032 ms | 0.052 ms | 0 |
| 70/30 hybrid | 100% | 100% | 1.000 | 15.940 ms | 24.991 ms | 0 |

The MFA benchmark question retrieved expected chunk `SEC-01` at rank one.

## Authorization verification

For the restricted vendor-contract question:

- `all_employees` received zero instances of restricted chunk `VM-02`.
- `legal` received `VM-02` at rank one.
- The authorized raw cosine similarity was 0.7318.

## Persistence verification

Qdrant was migrated from a manually started container to `compose.yaml`. After stopping and removing the original container, Docker Compose recreated it using the same named volume.

The collection still contained all 26 points after the replacement.

## Automated tests

Command: `RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v`

Result: **13 tests passed in 0.802 seconds.**

## Reproduction

1. Run `python -m pip install -e .`.
2. Run `docker compose up -d`.
3. Run `python scripts/index_corpus_qdrant.py`.
4. Run `python scripts/evaluate_qdrant.py`.
5. Run the integration-test command above.

## Conclusion

M03 added genuine MiniLM embeddings, persistent Qdrant storage, idempotent indexing, server-side role filtering, BM25 fusion, evidence output, Docker Compose and live integration tests.

## Limitations

- The benchmark is deliberately small and synthetic.
- Perfect benchmark accuracy does not prove production-scale generalization.
- Latency was measured on one local development machine.
- Department, status and version selectors are not yet exposed.
- Refusal evaluation and answer generation are not implemented.