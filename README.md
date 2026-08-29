# Enterprise Policy RAG Knowledge Base

An evidence-first RAG system for enterprise policies and operational playbooks. It combines semantic and keyword retrieval, enforces role-based document access, tracks source versions and evaluates every retrieval change against a frozen benchmark.

## What is complete in Steps 1 and 2

- 26 role-tagged policy chunks
- 20 ground-truth questions
- deterministic 384-dimensional vector baseline
- BM25 and 70/30 hybrid search
- hit@1, hit@3, MRR and latency evaluation
- access-control and corpus-integrity tests
- PDF, DOCX, TXT and Markdown parsing
- SHA-256 content checksums and duplicate prevention
- document-version lineage with one active version
- page-aware 500-character chunks with 50-character overlap
- atomic JSONL chunk output and ingestion ledger

Measured on the frozen v1 benchmark, the offline hybrid baseline currently reaches **95% hit@1, 100% hit@3 and 0.975 MRR**. These are small-corpus baseline results; the production MiniLM/Qdrant evaluation remains a later milestone.

## Run the first measurable baseline

From WSL/Ubuntu:

```bash
cd mazen-portfolio-lab/projects/02-enterprise-rag-knowledge-base
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/evaluate_retrieval.py
```

The current milestones require no API key, Docker container, model download or cloud account.

## Run the document-ingestion step

The repository includes a synthetic Markdown policy for a safe first run:

```bash
PYTHONPATH=src python scripts/ingest_document.py \
  data/sample_documents/security_access_policy.md \
  --document-id SEC-POLICY \
  --title "Information Security Access Policy" \
  --version 1.0 \
  --effective-date 2026-08-20 \
  --department "Information Security" \
  --roles all
```

The first run returns `created` and writes six chunks. Running the identical command again returns `duplicate` with the same SHA-256 checksum. If the content changes while the document ID and version remain `1.0`, ingestion stops with a version-conflict message; provide a new version such as `1.1` to create lineage safely.

Runtime output is written to:

- `data/ingestion/ledger.json`
- `data/ingested/<document-id>/v<version>/chunks.jsonl`

## Final architecture

```text
Documents -> parse/version -> 500/50 chunks -> MiniLM embeddings -> Qdrant
                                      |                         |
                                      +------ BM25 index -------+
                                                                |
Question -> role filter -> 70/30 hybrid ranking -> answerability gate
         -> grounded LLM -> citations -> SSE/API -> Next.js interface
```

## Original features

- role and department filters applied before ranking;
- version-aware citations and checksums;
- weak-evidence refusal instead of forced answers;
- citation-completeness and access-leakage metrics;
- deterministic local tests plus production MiniLM/Qdrant evaluation.

## Next step

Replace the offline hashing provider with `all-MiniLM-L6-v2`, store 384-dimensional vectors in Qdrant and rerun the frozen benchmark. See `ROADMAP.md` milestone M03.
