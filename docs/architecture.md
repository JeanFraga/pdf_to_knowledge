# Architecture

## Executive Summary

The **pdf_to_knowledge** system is a cloud-native, agentic pipeline built on **Google Cloud Platform (GCP)** using the **Google Agent Development Kit (ADK)**. The architecture employs a multi-agent system where two specialized agents—an **Ingestion Agent** and a **Database Agent**—collaborate via the **Agent-to-Agent (A2A) Protocol**. Infrastructure is fully managed as code using **Terraform**, with CI/CD pipelines orchestrated by **GitHub Actions** and **Cloud Build**. This design ensures scalability, strict separation of concerns, and a robust foundation for downstream knowledge retrieval.

## Project Initialization

The project will be initialized using a custom Terraform and ADK structure.

First implementation story should execute:
```bash
# Initialize Terraform
terraform init

# Initialize ADK Agents
adk init ingestion-agent
adk init database-agent
```

## Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
| -------- | -------- | ------- | ------------- | --------- |
| **Framework** | Google ADK (Agent Development Kit) | Latest | All | User constraint; provides standardized agentic patterns. |
| **Communication** | A2A Protocol (Agent-to-Agent) | ADK Std | All | User constraint; enables structured inter-agent collaboration. |
| **Ingestion Agent** | Python-based ADK Agent | 3.11+ | Ingestion, Chunking | Handles PDF parsing, semantic segmentation, and context injection. |
| **Database Agent** | Python-based ADK Agent with MCP | 3.11+ | Storage, Retrieval | Encapsulates database logic via Model Context Protocol (MCP). |
| **Graph Database** | Neo4j (Self-hosted on GKE or Aura) | 5.x | Storage | Stores relationships between concepts and chunks. |
| **NoSQL Database** | Google Cloud Firestore | Native | Storage | Stores raw chunks, metadata, and processing status. |
| **Infrastructure** | Terraform | 1.5+ | DevOps | User constraint; Infrastructure as Code (IaC). |
| **CI/CD** | GitHub Actions + Cloud Build | Latest | DevOps | User constraint; automated testing and deployment. |
| **Containerization** | Docker / Google Kubernetes Engine (GKE) | Latest | Deployment | Scalable runtime for agents. |

## Project Structure

```
pdf_to_knowledge/
├── .github/
│   └── workflows/          # GitHub Actions for CI
├── infrastructure/
│   ├── terraform/          # Terraform definitions
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── modules/
│   └── cloudbuild/         # Cloud Build configurations
├── agents/
│   ├── ingestion-agent/    # Agent 1: Parsing & Chunking
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── agent.yaml      # ADK Config
│   └── database-agent/     # Agent 2: Storage & MCP
│       ├── src/
│       ├── tests/
│       ├── Dockerfile
│       └── agent.yaml      # ADK Config
├── shared/
│   ├── schemas/            # Shared JSON schemas (A2A contracts)
│   └── utils/
└── docs/
    ├── architecture.md
    └── prd.md
```

## Epic to Architecture Mapping

| Epic | Primary Component | Supporting Components |
| :--- | :--- | :--- |
| **E1: PDF Ingestion** | `ingestion-agent` | `infrastructure` (Storage Buckets) |
| **E2: Agentic Chunking** | `ingestion-agent` | `shared/schemas` |
| **E3: Visual Extraction** | `ingestion-agent` | `database-agent` (Storage) |
| **E4: Structured Storage** | `database-agent` | `infrastructure` (Firestore/Neo4j) |
| **E5: Infrastructure Setup** | `infrastructure` | `terraform` |
| **E6: CLI Interface** | `ingestion-agent` | `infrastructure` (Cloud Run/GKE) |

## Technology Stack Details

### Core Technologies

*   **Language:** Python 3.11+ (Standard for AI/ADK)
*   **Agent Framework:** Google ADK
*   **Protocol:** A2A (Agent-to-Agent)
*   **Databases:**
    *   **Firestore:** Document store for chunks and metadata.
    *   **Neo4j:** Graph store for concept relationships.
*   **Infrastructure:**
    *   **Terraform:** State stored in GCS bucket.
    *   **GKE (Google Kubernetes Engine):** Hosting for agents.
    *   **Cloud Build:** Container building and deployment.

### Integration Points

*   **CLI to Ingestion Agent:** via gRPC or REST (ADK exposed endpoint).
*   **Ingestion Agent to Database Agent:** via A2A Protocol (likely over gRPC/HTTP internal mesh).
*   **Database Agent to Databases:** Direct TCP/HTTP connection using native drivers (Neo4j Driver, Firestore SDK).

## Novel Pattern Designs

### A2A Chunking Pipeline

**Pattern Name:** Agentic Handoff for Knowledge Persistence
**Purpose:** Decouple processing logic from storage logic to allow independent scaling and schema evolution.

**Components:**
1.  **Ingestion Agent:** Producer. Parses PDF, identifies chunks, injects context.
2.  **Database Agent:** Consumer. Validates schema, manages transactions, writes to Graph/NoSQL.

**Data Flow:**
1.  `Ingestion Agent` processes a chapter.
2.  `Ingestion Agent` constructs a `KnowledgePayload` (JSON).
3.  `Ingestion Agent` sends `StoreKnowledge` message via A2A to `Database Agent`.
4.  `Database Agent` validates payload against Schema.
5.  `Database Agent` writes nodes/edges to Neo4j and documents to Firestore.
6.  `Database Agent` returns `Success(ids)` or `Error`.

## Implementation Patterns

These patterns ensure consistent implementation across all AI agents:

### Naming Conventions

*   **Agents:** `kebab-case` (e.g., `ingestion-agent`, `database-agent`).
*   **Terraform Resources:** `snake_case` with provider prefix (e.g., `google_storage_bucket.raw_pdfs`).
*   **A2A Messages:** `PascalCase` (e.g., `StoreKnowledgeRequest`, `ChunkProcessedEvent`).
*   **Database Collections:** `snake_case` (e.g., `knowledge_chunks`, `processing_jobs`).

### Code Organization

*   **ADK Standard:** Follow strict ADK folder structure.
*   **Shared Schemas:** All A2A message schemas must reside in `shared/schemas` and be referenced by both agents.

### Error Handling

*   **A2A Errors:** Must return structured error objects: `{ "code": "INVALID_SCHEMA", "message": "...", "retryable": false }`.
*   **Retry Logic:** Ingestion Agent must implement exponential backoff for `retryable` errors from Database Agent.

### Logging Strategy

*   **Format:** JSON structured logging.
*   **Trace ID:** All logs must include a `trace_id` that persists across the A2A boundary (passed in message metadata).
*   **Destination:** Cloud Logging (Stackdriver).

## Data Architecture

### Firestore (NoSQL)
*   **Collection:** `jobs` - Status of ingestion tasks.
*   **Collection:** `chunks` - The actual text content, vectors, and metadata.
    *   `id`: UUID
    *   `text`: String
    *   `global_context`: String
    *   `visual_descriptions`: Array

### Neo4j (Graph)
*   **Nodes:** `Concept`, `Chunk`, `Chapter`, `Book`.
*   **Edges:** `DEFINED_IN`, `MENTIONED_IN`, `PRECEDES`, `RELATED_TO`.

## API Contracts

### A2A Interface: Database Agent

```protobuf
service DatabaseService {
  rpc StoreKnowledge (StoreKnowledgeRequest) returns (StoreKnowledgeResponse);
  rpc GetGraphContext (GetGraphContextRequest) returns (GetGraphContextResponse);
}
```

## Security Architecture

*   **Service Accounts:** Each agent runs with a dedicated Google Service Account (GSA) with least-privilege IAM roles.
*   **Workload Identity:** GKE Workload Identity to map K8s Service Accounts to GSAs.
*   **Secrets:** All API keys (e.g., Neo4j credentials, LLM keys) stored in **Google Secret Manager**, mounted as volumes or env vars.

## Performance Considerations

*   **Async Processing:** Ingestion should be asynchronous. The CLI triggers a job and polls for status.
*   **Batching:** Database Agent should support batched writes to Firestore/Neo4j to reduce network overhead.

## Deployment Architecture

*   **Environment:** GKE Autopilot for low operational overhead.
*   **Registry:** Google Artifact Registry (GAR) for Docker images.
*   **IaC:** Terraform applies infrastructure changes; Cloud Build applies application deployments (Helm/Manifests).

## Development Environment

### Prerequisites

*   Google Cloud SDK (`gcloud`)
*   Terraform `1.5+`
*   Python `3.11`
*   Docker
*   `adk` CLI tool

### Local Testing Strategy

*   **Containerization:** All agents provided with `Dockerfile` and `docker-compose.yml` for full local orchestration.
*   **Model Access:** Local agents configured to access Gemini models (Flash/Pro) via API keys for functional testing.

### Setup Commands

```bash
# Local dev setup
gcloud auth login
gcloud config set project <project-id>
cd infrastructure/terraform && terraform apply
```

## Architecture Decision Records (ADRs)

*   **ADR-001: Use of Google ADK:** Chosen to align with user constraints and leverage standardized agentic patterns.
*   **ADR-002: Separation of Ingestion and Storage:** Split into two agents to allow the storage layer to evolve (e.g., changing DBs) without affecting the complex ingestion logic.
*   **ADR-003: Dual Database Strategy:** Using Firestore for content and Neo4j for relationships provides the best of both worlds (retrieval speed vs. relational depth).

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-11-26_
_For: Jean_
