"""
A2A Protocol Schemas for pdf_to_knowledge

This module defines the contract between Ingestion Agent and Database Agent.
All inter-agent communication MUST use these schemas.

Version: 1.0.0
"""

from .knowledge import (
    StoreKnowledgeRequest,
    StoreKnowledgeResponse,
    StoredChunkResult,
    KnowledgeChunk,
    ChunkMetadata,
    VisualDescription,
    ProcessingStatus,
)
from .validation import (
    SchemaValidationError,
    validate_request,
    validate_response,
    validate_json,
)

__all__ = [
    # Core schemas
    "StoreKnowledgeRequest",
    "StoreKnowledgeResponse",
    "StoredChunkResult",
    "KnowledgeChunk",
    "ChunkMetadata",
    "VisualDescription",
    "ProcessingStatus",
    # Validation utilities
    "SchemaValidationError",
    "validate_request",
    "validate_response",
    "validate_json",
]

__version__ = "1.0.0"
