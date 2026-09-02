# Enterprise Policy RAG Knowledge Base

An evidence-first enterprise policy RAG system with governed ingestion, MiniLM embeddings, Qdrant vector storage, BM25 hybrid retrieval, role-aware filtering, grounded answers, citations, safe refusals, FastAPI, Gradio, Docker and GitHub Actions CI.

## Verified results

| Capability | Result |
|---|---:|
| Corpus size | 26 policy chunks |
| Retrieval benchmark | 20 questions |
| Production hybrid hit@1 | 100% |
| Expected citation recall | 100% (20/20) |
| Safe refusal rate | 100% (3/3) |
| Unauthorized retrievals | 0 |
| Automated tests | 27/27 passed |
| Containerized vectors | 26 |

## Architecture

    Documents -> validation and version lineage -> chunking
                                                |
                        +-----------------------+----------------------+
                        |                                              |
                        v                                              v
                 MiniLM embeddings                                  BM25
                        |                                              |
                        +------------------ Qdrant hybrid retrieval ---+
                                                       |
                                                       v
                             Grounded answer with citations or safe refusal
                                                       |
                                                       v
                               FastAPI -> Gradio -> Docker Compose -> CI

## Run the complete application

    docker compose up --build -d --wait --wait-timeout 180

Open:

- Demo: http://127.0.0.1:7860
- API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health
- Qdrant dashboard: http://127.0.0.1:6333/dashboard

Verify:

    docker compose ps
    curl -sS http://127.0.0.1:8000/health

Run all tests:

    source .venv/bin/activate
    RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v

## Scope

This is a controlled synthetic benchmark demonstrating reproducible ingestion, retrieval, governance, grounded answers and local deployment. It is not a production-scale accuracy or authenticated enterprise authorization claim.