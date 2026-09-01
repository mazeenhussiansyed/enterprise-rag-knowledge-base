# M06 Evaluation: FastAPI Service and Interactive Local Demo

**Evaluation date:** 2026-09-01
**Scope:** Local API and browser demonstration

## Objective

Expose the verified retrieval-and-answering system through a stable HTTP API and a clean local user interface without bypassing the authorization filter, answerability gate or citation logic.

## Delivered components

| Component | Implementation |
|---|---|
| HTTP API | FastAPI |
| ASGI server | Uvicorn |
| API documentation | Swagger UI at `/docs` and ReDoc at `/redoc` |
| Interactive user interface | Gradio |
| API address | `http://127.0.0.1:8000` |
| Demo address | `http://127.0.0.1:7860` |
| Retrieval backend | MiniLM, Qdrant and BM25 hybrid retrieval |
| Answer backend | Citation-backed extractive grounded baseline |

## API contract

| Method | Endpoint | Verified behavior |
|---|---|---|
| `GET` | `/` | Returns service description and available endpoint paths |
| `GET` | `/health` | Reports local Qdrant-backed runtime health |
| `GET` | `/stats` | Reports corpus, collection and retrieval configuration |
| `POST` | `/search` | Returns role-filtered ranked evidence chunks |
| `POST` | `/ask` | Returns a grounded answer with citations or a safe refusal |

## Automated verification

```bash
python -m py_compile src/enterprise_rag/api.py scripts/run_demo.py
RUN_QDRANT_INTEGRATION=1 python -m unittest discover -s tests -v