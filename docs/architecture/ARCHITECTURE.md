# Architecture: Enterprise Policy RAG

## Design goal

Return an answer only when the caller is permitted to access the supporting policy text and the retrieved evidence is strong enough to cite. The design separates ingestion, governed vector synchronization, retrieval, answer generation, API delivery and the interactive demo so each layer can be tested independently.

## System overview

```text
Document sources
      |
      v
Validation, parsing and checksum calculation
      |
      v
Versioned chunks and ingestion ledger
      |
      v
Governed synchronization -----> Qdrant vectors and governance payload
      |                                  |
      +---------------------> BM25 source chunks
                                         |
Browser demo -> FastAPI -> role-aware hybrid retrieval
                                         |
                                         v
                           Answerability gate and extractive answer
                                         |
                                         v
                           Citations, evidence excerpts or safe refusal