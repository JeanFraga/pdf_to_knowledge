# Database Agent

Storage and retrieval agent with MCP for pdf_to_knowledge.

## Responsibilities
- Validate incoming knowledge payloads
- Store chunks in Firestore
- Store concept relationships in Neo4j
- Provide retrieval endpoints

## Local Development

```bash
# From project root
docker-compose up database-agent
```

## A2A Communication

Receives `StoreKnowledgeRequest` messages from Ingestion Agent.
Returns `StoreKnowledgeResponse` with storage confirmation.
