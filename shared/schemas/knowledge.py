"""
Knowledge Schemas for A2A Protocol

Defines the data structures for storing and retrieving knowledge chunks
between Ingestion Agent and Database Agent.

Schema Version: 1.0.0
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ProcessingStatus(str, Enum):
    """Status of a knowledge storage operation."""
    
    SUCCESS = "success"
    PARTIAL = "partial"  # Some chunks failed
    FAILED = "failed"
    VALIDATION_ERROR = "validation_error"


class VisualDescription(BaseModel):
    """Description of a visual element (chart, diagram, image) in the document."""
    
    visual_id: str = Field(
        ...,
        description="Unique identifier for this visual within the chunk",
        examples=["fig-1", "chart-2.3"]
    )
    visual_type: str = Field(
        ...,
        description="Type of visual: chart, diagram, table, image, formula",
        examples=["chart", "diagram", "table"]
    )
    description: str = Field(
        ...,
        description="Detailed text description of the visual for downstream agents",
        min_length=10
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Page number where the visual appears",
        ge=1
    )
    
    model_config = {"extra": "forbid"}


class ChunkMetadata(BaseModel):
    """Metadata associated with a knowledge chunk."""
    
    source_document: str = Field(
        ...,
        description="Original PDF filename or document identifier",
        examples=["deep_learning_book.pdf"]
    )
    chapter: Optional[str] = Field(
        default=None,
        description="Chapter title or number",
        examples=["Chapter 3: Probability"]
    )
    section: Optional[str] = Field(
        default=None,
        description="Section or subsection title",
        examples=["3.2 Conditional Probability"]
    )
    page_start: Optional[int] = Field(
        default=None,
        description="Starting page number",
        ge=1
    )
    page_end: Optional[int] = Field(
        default=None,
        description="Ending page number",
        ge=1
    )
    chunk_index: int = Field(
        ...,
        description="Sequential index of this chunk within the document",
        ge=0
    )
    total_chunks: Optional[int] = Field(
        default=None,
        description="Total number of chunks in the document",
        ge=1
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Extracted keywords for this chunk",
        examples=[["neural network", "backpropagation", "gradient descent"]]
    )
    tone: Optional[str] = Field(
        default=None,
        description="Detected tone/style of the content",
        examples=["technical", "conversational", "formal"]
    )
    trace_id: Optional[str] = Field(
        default=None,
        description="Trace ID for cross-agent logging and debugging"
    )
    
    model_config = {"extra": "allow"}  # Allow additional metadata fields


class KnowledgeChunk(BaseModel):
    """
    A single knowledge chunk extracted from a PDF document.
    
    This is the core unit of knowledge that flows between agents.
    """
    
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this chunk"
    )
    text: str = Field(
        ...,
        description="The main text content of the chunk",
        min_length=1
    )
    global_context: str = Field(
        ...,
        description="Injected global context from the document summary",
        min_length=1
    )
    context_injection: Optional[str] = Field(
        default=None,
        description="Additional context specific to this chunk's position in the document"
    )
    visuals: list[VisualDescription] = Field(
        default_factory=list,
        description="Visual elements associated with this chunk"
    )
    metadata: ChunkMetadata = Field(
        ...,
        description="Metadata about this chunk"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when this chunk was created"
    )
    
    model_config = {"extra": "forbid"}
    
    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        """Ensure text is not just whitespace."""
        if not v.strip():
            raise ValueError("text cannot be empty or whitespace only")
        return v


class StoreKnowledgeRequest(BaseModel):
    """
    Request to store knowledge chunks in the Database Agent.
    
    Sent by: Ingestion Agent
    Received by: Database Agent
    
    This is the primary A2A message for the knowledge pipeline.
    """
    
    request_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this request"
    )
    job_id: str = Field(
        ...,
        description="Parent job identifier for tracking the ingestion pipeline",
        examples=["job-2025-01-02-abc123"]
    )
    chunks: list[KnowledgeChunk] = Field(
        ...,
        description="List of knowledge chunks to store",
        min_length=1
    )
    document_global_context: str = Field(
        ...,
        description="The full global context/summary for the source document"
    )
    is_final_batch: bool = Field(
        default=False,
        description="True if this is the last batch for the job"
    )
    trace_id: Optional[str] = Field(
        default=None,
        description="Trace ID for cross-agent logging"
    )
    
    model_config = {"extra": "forbid"}
    
    @property
    def chunk_count(self) -> int:
        """Return the number of chunks in this request."""
        return len(self.chunks)


class StoredChunkResult(BaseModel):
    """Result of storing a single chunk."""
    
    chunk_id: UUID = Field(..., description="ID of the chunk")
    firestore_id: Optional[str] = Field(
        default=None, 
        description="Firestore document ID if stored"
    )
    neo4j_node_id: Optional[str] = Field(
        default=None,
        description="Neo4j node ID if stored"
    )
    success: bool = Field(..., description="Whether storage succeeded")
    error: Optional[str] = Field(
        default=None,
        description="Error message if storage failed"
    )


class StoreKnowledgeResponse(BaseModel):
    """
    Response from the Database Agent after storing knowledge.
    
    Sent by: Database Agent
    Received by: Ingestion Agent
    """
    
    request_id: UUID = Field(
        ...,
        description="ID of the original request"
    )
    job_id: str = Field(
        ...,
        description="Parent job identifier"
    )
    status: ProcessingStatus = Field(
        ...,
        description="Overall status of the storage operation"
    )
    chunks_received: int = Field(
        ...,
        description="Number of chunks received in the request",
        ge=0
    )
    chunks_stored: int = Field(
        ...,
        description="Number of chunks successfully stored",
        ge=0
    )
    results: list[StoredChunkResult] = Field(
        default_factory=list,
        description="Per-chunk storage results"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if status is FAILED"
    )
    trace_id: Optional[str] = Field(
        default=None,
        description="Trace ID for cross-agent logging"
    )
    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when processing completed"
    )
    
    model_config = {"extra": "forbid"}
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of chunk storage."""
        if self.chunks_received == 0:
            return 0.0
        return self.chunks_stored / self.chunks_received
