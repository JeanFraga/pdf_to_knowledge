# Shared Schemas

A2A message contracts shared between agents.

## Contents

- `knowledge.py` - Pydantic models for StoreKnowledgeRequest/Response

## Schema Version

Current: v1

## Usage

```python
from shared.schemas.knowledge import StoreKnowledgeRequest

request = StoreKnowledgeRequest(
    chunk_text="...",
    global_context="...",
    visuals=[],
    metadata={}
)
```
