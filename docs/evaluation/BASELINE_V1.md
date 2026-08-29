# Retrieval Baseline v1

Run date: 2026-08-20

## Dataset

- 6 synthetic enterprise policy documents
- 26 versioned, role-tagged chunks
- 20 frozen questions with one expected supporting chunk per question
- Roles evaluated: all employees, IT administrator, manager, security, IT operations, legal, communications, data engineer, procurement and continuity

## Configuration

- Vector baseline: deterministic 384-dimensional hashing vectors with unigram and bigram features
- Keyword baseline: BM25 with `k1=1.5` and `b=0.75`
- Hybrid formula: 70% normalized vector score plus 30% normalized BM25 score
- Authorization: role filter applied before scoring
- Evaluation: hit@1, hit@3, mean reciprocal rank and local retrieval latency

## Results

| Strategy | Hit@1 | Hit@3 | MRR | Median latency | p95 latency |
|---|---:|---:|---:|---:|---:|
| Vector | 85% | 95% | 0.8917 | 0.453 ms | 0.491 ms |
| BM25 | 100% | 100% | 1.0000 | 0.452 ms | 0.483 ms |
| Hybrid | 95% | 100% | 0.9750 | 0.460 ms | 0.477 ms |

All five corpus, embedding, retrieval-quality and authorization tests passed. The explicit restricted-content test returned zero unauthorized instances of chunk `VM-02`.

## Interpretation

The synthetic questions use policy-specific terms, so BM25 is unusually strong on this small benchmark. Hybrid retrieval still provides a useful baseline but must be challenged with paraphrases, ambiguous questions and a larger held-out set before production conclusions are made. MiniLM/Qdrant results will be reported separately rather than replacing these values.

## Reproduce

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/evaluate_retrieval.py
```
