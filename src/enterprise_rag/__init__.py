"""Offline-first retrieval components for the Enterprise Policy RAG project."""

from .chunking import build_chunks
from .corpus import load_chunks, load_questions
from .embeddings import HashingEmbeddingProvider, MiniLMEmbeddingProvider
from .governed_sync import GovernedSyncResult, GovernedSyncService
from .ingestion import IngestionService, sha256_file
from .ledger import IngestionLedger
from .models import DocumentMetadata, IngestionResult, ParsedPage
from .parsers import parse_document, sanitize_filename
from .qdrant_store import QdrantVectorStore
from .retrieval import HybridRetriever, QdrantHybridRetriever

__all__ = [
    "DocumentMetadata",
    "GovernedSyncResult",
    "GovernedSyncService",
    "HashingEmbeddingProvider",
    "HybridRetriever",
    "IngestionLedger",
    "IngestionResult",
    "IngestionService",
    "MiniLMEmbeddingProvider",
    "ParsedPage",
    "QdrantHybridRetriever",
    "QdrantVectorStore",
    "build_chunks",
    "load_chunks",
    "load_questions",
    "parse_document",
    "sanitize_filename",
    "sha256_file",
]