# P02-RAG Architecture Decisions

## ADR-001 - Synthetic policy pack before public documents

**Decision:** Start with a controlled synthetic enterprise corpus.

**Reason:** It provides exact ground truth, avoids private data and copyright ambiguity, makes access-control tests possible and allows every metric to be reproduced quickly.

## ADR-002 - Evaluation before LLM generation

**Decision:** Prove retrieval quality before integrating an LLM.

**Reason:** An eloquent model can hide retrieval failures. Hit@k, MRR and access-leakage measurements isolate whether the correct authorized evidence was retrieved.

## ADR-003 - Offline provider plus production provider

**Decision:** Keep a deterministic 384-dimensional hashing provider for offline unit tests and use MiniLM for production retrieval.

**Reason:** Baseline tests should run without network access, API keys or model downloads, while production retrieval requires genuine semantic embeddings.

## ADR-004 - Authorization before ranking

**Decision:** Apply role authorization before vector or BM25 candidates are fused and ranked.

**Reason:** Removing unauthorized results after ranking can leak metadata, consume candidate positions and distort the final ranking.

Qdrant enforces the role filter inside the vector query. BM25 independently limits scoring to locally authorized chunks. Document-status filtering will be added when status is propagated into the chunk model.

## ADR-005 - Preserve the 70/30 baseline

**Decision:** Preserve 70% vector and 30% BM25 weighting for both the baseline and production comparison.

**Reason:** A fixed weighting makes the hashing baseline and MiniLM/Qdrant results comparable without silently tuning against the frozen expected answers.

## ADR-006 - Content identity is separate from filename

**Decision:** Calculate SHA-256 from file bytes and use the checksum, not the filename, to identify duplicate content.

**Reason:** A user can rename the same file, and different files can share a display name. Content hashing prevents repeated ingestion and gives each source a verifiable identity.

## ADR-007 - Version labels are immutable

**Decision:** Reject changed content when its document ID and version already exist. A change must use a new version, and the ledger marks the preceding version inactive.

**Reason:** Silently replacing a policy would make historical citations impossible to audit and could expose obsolete guidance.

## ADR-008 - Chunks do not cross page boundaries

**Decision:** Apply 500-character windows with 50-character overlap independently to each parsed page.

**Reason:** A chunk spanning two pages creates ambiguous citations. Page-isolated chunks preserve exact page numbers while maintaining the 500/50 retrieval configuration.

## ADR-009 - FastEmbed and ONNX for MiniLM inference

**Decision:** Run `sentence-transformers/all-MiniLM-L6-v2` through FastEmbed and ONNX Runtime.

**Reason:** This provides genuine normalized 384-dimensional MiniLM embeddings on CPU without downloading large PyTorch dependencies or requiring a GPU. FastEmbed and its runtime support the project’s Python 3.14 environment.

## ADR-010 - Qdrant for persistent semantic vectors

**Decision:** Store production semantic vectors in Qdrant v1.19.0 using cosine distance.

**Reason:** Qdrant provides persistent vector storage, metadata payloads, server-side role filters, payload indexes and a production-relevant query API while remaining easy to run locally through Docker.

## ADR-011 - Deterministic UUIDs for idempotent upserts

**Decision:** Generate each Qdrant point ID using UUID5 over document ID, version and chunk ID.

**Reason:** The same governed chunk always maps to the same vector point. Re-indexing updates the existing point rather than creating duplicates, while different document versions remain distinct.

## ADR-012 - Index metadata before ingestion

**Decision:** Create keyword payload indexes for roles, chunk IDs, document IDs, departments and versions before uploading vectors.

**Reason:** These fields support authorization, lineage inspection and future metadata filters. Creating indexes before data ingestion follows the intended filtered-search access pattern.

## ADR-013 - Local-only Qdrant networking

**Decision:** Bind Qdrant ports 6333 and 6334 to `127.0.0.1` in local development.

**Reason:** The self-hosted development database does not need to be reachable from other network devices. Local-only binding reduces unintended exposure while still allowing WSL and the browser dashboard to connect.

## ADR-014 - Named-volume persistence

**Decision:** Store Qdrant data in the named Docker volume `enterprise-rag-qdrant-data`.

**Reason:** A named volume avoids Windows/WSL bind-mount complications and preserves vectors when the container is stopped, removed or recreated through Docker Compose.

## ADR-015 - Accuracy claims include benchmark scope

**Decision:** Report every retrieval score with the 26-chunk corpus and 20-question benchmark scope.

**Reason:** Perfect accuracy on a deliberately small synthetic benchmark verifies implementation correctness but must not be presented as production-scale generalization.