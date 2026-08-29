# Architecture: Enterprise Policy RAG

## Design goal

Return an answer only when the requesting role is allowed to see the supporting policy text and the retrieved evidence is strong enough to cite. The system is split into an ingestion path and a question-answering path so that each stage can be tested independently.

## Ingestion path

1. Accept PDF, DOCX, TXT or Markdown files.
2. Extract normalized text and document metadata.
3. Calculate a source checksum and compare it with the ingestion ledger.
4. Mark a changed source as a new document version instead of silently overwriting it.
5. Split text into 500-character chunks with 50-character overlap while preserving section boundaries where possible.
6. Attach document ID, version, effective date, department, roles and source location to every chunk.
7. Generate 384-dimensional MiniLM embeddings and upsert the chunks into Qdrant.
8. Build or refresh the BM25 index from the same authorized chunk set.

## Question-answering path

1. Authenticate the user and resolve their role.
2. Apply the role filter before vector or keyword scoring.
3. Retrieve candidates with semantic search and BM25.
4. Normalize scores and combine them using 70% vector and 30% BM25 weights.
5. Pass the top evidence through an answerability gate.
6. Ask the configured LLM to answer only from the accepted evidence.
7. Validate that factual statements contain citations to document, section and version.
8. Stream the answer through Server-Sent Events and cache safe repeated work in Redis.

## Provider strategy

- Offline development: deterministic 384-dimensional hashing vectors and extractive answers, requiring no key or model download.
- Local production option: `all-MiniLM-L6-v2` plus Ollama.
- Hosted fallback: the same retrieval path with Groq for generation.

The offline provider is a test double, not a claim that hashing vectors are equivalent to MiniLM. Both providers use the same retrieval interface so measurements remain comparable.

## Security boundary

Authorization happens before ranking. A restricted chunk is never included in the candidate list for an unauthorized role, even if it would have the highest semantic score. Tests also verify that the restricted vendor-contract chunk cannot leak to the general employee role.
