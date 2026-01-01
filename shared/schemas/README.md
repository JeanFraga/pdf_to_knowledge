# A2A Protocol Schemas

**Version:** 1.0.0

This directory contains the Pydantic schemas that define the contract between the **Ingestion Agent** and **Database Agent** in the pdf_to_knowledge pipeline.

## Overview

```
Ingestion Agent                    Database Agent
     │                                   │
     │  StoreKnowledgeRequest            │
     │ ─────────────────────────────────>│
     │                                   │
     │  StoreKnowledgeResponse           │
     │ <─────────────────────────────────│
     │                                   │
```

## Schema Files

| File | Description |
|:-----|:------------|
| `knowledge.py` | Core schemas: `StoreKnowledgeRequest`, `StoreKnowledgeResponse`, `KnowledgeChunk` |
| `validation.py` | Validation utilities with detailed error messages |
| `__init__.py` | Public API exports |

## Core Types

### StoreKnowledgeRequest

Sent by Ingestion Agent to store processed PDF chunks.

```python
from shared.schemas import StoreKnowledgeRequest, KnowledgeChunk, ChunkMetadata

request = StoreKnowledgeRequest(
    job_id="job-2025-01-02-abc123",
    document_global_context="This book covers deep learning fundamentals...",
    chunks=[
        KnowledgeChunk(
            text="Neural networks are computational models...",
            global_context="Chapter 1 introduces neural network basics.",
            metadata=ChunkMetadata(
                source_document="deep_learning.pdf",
                chapter="Chapter 1",
                chunk_index=0,
                keywords=["neural network", "perceptron"]
            )
        )
    ],
    is_final_batch=False
)
```

### StoreKnowledgeResponse

Returned by Database Agent after storage attempt.

```python
from shared.schemas import StoreKnowledgeResponse, ProcessingStatus

response = StoreKnowledgeResponse(
    request_id=request.request_id,
    job_id="job-2025-01-02-abc123",
    status=ProcessingStatus.SUCCESS,
    chunks_received=5,
    chunks_stored=5
)
```

### KnowledgeChunk

A single unit of knowledge extracted from a PDF.

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `id` | UUID | Auto | Unique identifier |
| `text` | str | ✓ | Main text content |
| `global_context` | str | ✓ | Injected document-level context |
| `context_injection` | str | | Position-specific context |
| `visuals` | list[VisualDescription] | | Associated images/charts |
| `metadata` | ChunkMetadata | ✓ | Source info, keywords, etc. |

### VisualDescription

Description of a visual element (chart, diagram, table).

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `visual_id` | str | ✓ | Unique ID within chunk |
| `visual_type` | str | ✓ | chart, diagram, table, image, formula |
| `description` | str | ✓ | Detailed text description |
| `page_number` | int | | Source page |

## Validation

```python
from shared.schemas import validate_request, SchemaValidationError

try:
    request = validate_request(data_dict)
except SchemaValidationError as e:
    print(f"Validation failed: {e}")
    print(f"Errors: {e.errors}")
```

## Versioning

This schema follows semantic versioning:
- **1.0.0** - Initial release (Sprint 1)

Breaking changes will increment the major version.

## Usage in Agents

Both agents mount the `shared/` directory:

```python
# In ingestion-agent or database-agent
from shared.schemas import (
    StoreKnowledgeRequest,
    StoreKnowledgeResponse,
    validate_request,
)
```
