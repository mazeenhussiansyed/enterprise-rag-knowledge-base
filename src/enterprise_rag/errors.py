class IngestionError(Exception):
    """Base error for controlled ingestion failures."""


class UnsupportedDocumentError(IngestionError):
    """Raised when an input is not an allowed document format."""


class UnsafeDocumentError(IngestionError):
    """Raised when a file fails name, size, signature, or archive checks."""


class DocumentParseError(IngestionError):
    """Raised when an allowed document has no safely extractable text."""


class VersionConflictError(IngestionError):
    """Raised when an existing version label is reused for different content."""
