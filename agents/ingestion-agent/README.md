# Ingestion Agent

PDF ingestion and agentic chunking agent for pdf_to_knowledge.

## Responsibilities
- PDF text extraction
- Header/footer cleaning
- Semantic segmentation
- Global context generation
- Context injection into chunks
- Visual extraction coordination

## Local Development

```bash
# From project root
docker-compose up ingestion-agent
```

## A2A Communication

Sends `StoreKnowledgeRequest` messages to Database Agent.
