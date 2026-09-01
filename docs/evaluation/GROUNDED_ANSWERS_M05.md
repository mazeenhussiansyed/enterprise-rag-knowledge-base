# M05 Evaluation: Grounded Answers, Citations and Safe Refusals

**Evaluation date:** 2026-09-01
**Evaluation name:** `m05_grounded_answer_evaluation_v1`

## Objective

Evaluate the answer layer after retrieval. The system must answer only from authorized evidence, attach citations to supported answers, and refuse requests that are unsupported by the enterprise-policy corpus.

## Configuration

| Component | Configuration |
|---|---|
| Corpus | 26 synthetic enterprise-policy chunks |
| Answerable benchmark | 20 questions with expected evidence chunks |
| Refusal benchmark | 3 unsupported questions |
| Retrieval | Qdrant MiniLM vector search plus BM25 |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector database | Qdrant v1.19.0 |
| Ranking | 70% vector / 30% BM25 |
| Retrieval depth | Top 3 chunks |
| Answer provider | `extractive-grounded-baseline` |
| Vector-score threshold | 0.49 |
| Hybrid-score threshold | 0.35 |
| Topic grounding | At least 2 matched content terms and 40% query-term coverage |

## Verified Results

| Metric | Result |
|---|---:|
| Answerable questions | 20 |
| Answered with citations | 20 / 20 |
| Answer rate | 100% |
| Citation presence rate | 100% |
| Expected-citation recall | 100% |
| Unsupported questions | 3 |
| Safe refusals | 3 / 3 |
| Safe-refusal rate | 100% |
| Unsafe answers | 0 |
| Total evaluated questions | 23 |
| Median local latency | 16.620 ms |
| P95 local latency | 31.312 ms |
| Automated test suite | 22 / 22 passed |

## What Was Evaluated

For each answerable question, the evaluator verified that:

1. The system returned an `answered` status.
2. At least one citation was returned.
3. The citation list contained the expected ground-truth chunk ID.

For each unsupported question, the evaluator verified that:

1. The system returned a `refused` status.
2. No citations were exposed.
3. No unsupported answer was generated.

The unsupported cafeteria question is an important safety example. It shares the word “meals” with a travel-expense policy, but does not ask about travel reimbursement. The answerability gate correctly refused it instead of returning a misleading policy answer.

## Evidence Commands

Run the complete automated test suite:

```bash
RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v