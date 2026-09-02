# M07 Evaluation: Containerized Deployment and Continuous Integration

**Evaluation date:** 2026-09-01  
**Deployment mode:** Local Docker Compose  
**Compose command:** `docker compose up --build -d --wait --wait-timeout 180`

## Objective

Package the Enterprise Policy RAG application as a reproducible local service stack. The deployment must provision persistent Qdrant storage, index the controlled corpus, start the FastAPI service and Gradio demonstration interface, and expose a GitHub Actions workflow for automated verification.

## Containerized architecture

| Service | Responsibility | Result |
|---|---|---|
| Qdrant | Persistent vector database for MiniLM embeddings | Healthy |
| Indexer | Waits for Qdrant, embeds and indexes the 26-chunk corpus | Completed successfully |
| API | FastAPI service exposing health, statistics, search and grounded-answer endpoints | Healthy |
| Demo | Role-aware Gradio interface for interactive policy questions | Running |
| GitHub Actions | Rebuilds the stack and runs automated tests on pushes and pull requests | Configured |

## Verified local deployment

| Check | Result | Evidence |
|---|---:|---|
| Docker image build | Successful | `docker compose up --build -d --wait --wait-timeout 180` |
| Qdrant startup | Healthy | Docker Compose service status |
| Corpus indexing | 26 stored points | Indexer output and `/health` |
| API readiness | Healthy | Docker Compose API health check |
| Demo startup | Healthy | Docker Compose demo health check |
| API collection | `enterprise_policy_chunks_v1` | `GET /health` |
| API corpus chunks | 26 | `GET /health` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | `GET /health` |
| Local automated suite | 27/27 tests passed | `RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v` |
| Test duration | 3.873 seconds | Local automated test run |

The verified API health response was:

```json
{
  "status": "ok",
  "collection": "enterprise_policy_chunks_v1",
  "stored_points": 26,
  "corpus_chunks": 26,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}