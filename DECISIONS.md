# P02-RAG Architecture Decisions

## ADR-001 - Synthetic policy pack before public documents

**Decision:** Start with a controlled synthetic enterprise corpus.

**Reason:** It provides exact ground truth, avoids private data and copyright ambiguity, makes access-control tests possible, and allows every metric to be reproduced quickly.

## ADR-002 - Evaluation before LLM generation

**Decision:** Prove retrieval quality before integrating an LLM.

**Reason:** An eloquent model can hide retrieval failures. Hit@k, MRR and access leakage isolate whether the correct evidence was found.

## ADR-003 - Offline provider plus production provider

**Decision:** Use a deterministic 384-dimensional hashing provider for unit tests and MiniLM for production evaluation.

**Reason:** Tests should run without network access, API keys or model downloads, while the final architecture must still use semantic embeddings.

## ADR-004 - Authorization before ranking

**Decision:** Apply role and document-status filters before vector/BM25 ranking.

**Reason:** Removing unauthorized results after ranking can leak metadata and distort the candidate set.

## ADR-005 - Preserve the 70/30 baseline

**Decision:** Implement 70% vector and 30% BM25 as the frozen baseline, then compare any tuned alternative separately.

**Reason:** This reproduces the resume architecture while allowing an honest improvement experiment.

## ADR-006 - Content identity is separate from filename

**Decision:** Calculate SHA-256 from file bytes and use the checksum, not the filename, to identify duplicate content.

**Reason:** A user can rename the same file, and different files can share a display name. Content hashing prevents repeated vectors and gives every citation a verifiable source identity.

## ADR-007 - Version labels are immutable

**Decision:** Reject changed content when its document ID and version already exist. A change must use a new version, and the ledger marks the preceding version inactive.

**Reason:** Silently replacing a policy would make previous citations impossible to audit and could expose obsolete or incorrect guidance.

## ADR-008 - Chunks do not cross page boundaries

**Decision:** Apply 500-character windows with 50-character overlap independently to each parsed page.

**Reason:** A chunk spanning two pages produces ambiguous citations. Page-isolated chunks preserve an exact page number while keeping the resume's 500/50 retrieval configuration.
