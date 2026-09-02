# M07 Evaluation: Containerized Deployment and Continuous Integration

**Evaluation date:** 2026-09-01  
**Deployment mode:** Local Docker Compose  
**Command:** `docker compose up --build -d --wait --wait-timeout 180`

## Verified deployment

| Check | Result |
|---|---:|
| Qdrant vector database | Healthy |
| Corpus indexing | 26 stored points |
| FastAPI service | Healthy |
| Gradio demo | Running |
| Local automated tests | 27/27 passed |
| Test duration | 3.873 seconds |

Verified API health response:

```json
{
  "status": "ok",
  "collection": "enterprise_policy_chunks_v1",
  "stored_points": 26,
  "corpus_chunks": 26,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

## Reproduce locally

```bash
docker compose down --remove-orphans
docker compose up --build -d --wait --wait-timeout 180
docker compose ps
curl -sS http://127.0.0.1:8000/health
```

## Continuous integration

`.github/workflows/verify.yml` automatically builds the Docker stack, waits for the API health check, and runs the complete unit, API and live Qdrant integration test suite on pushes and pull requests.

## Scope

The Docker deployment is verified locally. GitHub Actions is configured and will be independently verified once its first workflow run completes successfully.