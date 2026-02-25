---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
inputDocuments:
  - _bmad-output/prd.md
  - _bmad-output/architecture.md
  - _bmad-output/epics.md (previous version, reference only)
  - _bmad-output/backlog.md
  - _bmad-output/implementation-readiness-report.md
  - _bmad-output/sprint-status.yaml
  - _bmad-output/sprint-artifacts/sprint-1.md
  - _bmad-output/sprint-artifacts/sprint-2.md
---

# pdf_to_knowledge - Epic Breakdown

**Author:** Jean
**Date:** 2026-02-25
**Rebuild:** Full rebuild from BMAD v6 workflow (previously v4)

---

## Overview

This document provides the complete epic and story breakdown for pdf_to_knowledge, decomposing the requirements from the PRD and Architecture into implementable stories.

**Implementation Progress:** Sprints 1–2 completed (6 stories done, 121 tests passing). This is a full rebuild of the epics document to align with BMAD v6 workflow format.

## Requirements Inventory

### Functional Requirements

- FR1: System can ingest PDF documents via CLI path.
- FR2: System can identify and remove page headers, footers, and page numbers.
- FR3: System can extract raw text while preserving paragraph structure.
- FR4: System can identify and extract image regions (charts, diagrams).
- FR5: System can perform semantic segmentation to divide text into logical sections.
- FR6: System can generate a "Global Context" summary for the document.
- FR7: System can inject relevant Global Context into each local chunk.
- FR8: System can generate visual descriptions for extracted image regions.
- FR9: System can preserve tone and style in a separate metadata field.
- FR10: System can validate processed data against a strict JSON schema.
- FR11: System can generate the final JSON output file.
- FR12: System can generate a human-readable summary document.
- FR13: System can run as a containerized workload on GCP.
- FR14: System can log processing steps and status to stdout/logging service.
- FR15: System can handle documents up to 500 pages in length.

### Non-Functional Requirements

- NFR1: **Performance** — Process a 300-page book in under 30 minutes; support parallel processing.
- NFR2: **Security** — Input/output data must remain within user's GCP project/VPC; secrets via GCP Secret Manager.
- NFR3: **Scalability** — Pipeline steps decoupled for independent scaling or model replacement.
- NFR4: **Reliability** — Pipeline should resume from last successful step on failure.
- NFR5: **Local Development** — All components runnable/testable locally via Docker; Gemini model support.

### Additional Requirements (from Architecture)

- Custom Terraform + ADK structure (`terraform init`, `adk init ingestion-agent`, `adk init database-agent`)
- A2A Protocol for inter-agent communication (gRPC/HTTP)
- Configurable PDF extraction backend via `PDF_EXTRACTOR_BACKEND` env var (pypdf default, Docling optional)
- Neo4j for concept relationship graph storage (MERGE-based idempotency)
- Firestore for chunks, metadata, and job status
- JSON structured logging with `trace_id` across A2A boundary
- Structured A2A error objects with exponential backoff retry logic
- Naming conventions: agents kebab-case, Terraform snake_case, A2A PascalCase, DB collections snake_case
- Shared schemas in `shared/schemas/`, referenced by both agents (Pydantic models)
- Deployment: GKE Autopilot, Artifact Registry, Cloud Build + GitHub Actions CI/CD

### FR Coverage Map

- **Epic 1 (Foundation):** FR13, FR14 — Infrastructure and logging
- **Epic 2 (Ingestion):** FR1, FR2, FR3, FR4 — PDF parsing, text/image extraction
- **Epic 3 (Chunking):** FR5, FR6, FR7, FR15 — Semantic segmentation, context injection, large docs
- **Epic 4 (Storage):** FR10, FR11 — Schema validation, JSON output, database persistence
- **Epic 5 (Enrichment):** FR8, FR9, FR12 — Visual descriptions, tone, human summary
- **Epic 6 (CLI):** FR1, FR14 — CLI interface, job monitoring
- **Epic 7 (Docling):** FR2, FR3, FR4, FR15 — ML-based extraction quality enhancement

## Epic List

### Epic 1: Foundation & Infrastructure
Establish the GCP infrastructure, ADK agent scaffolding, and local development environment to enable all subsequent work.
**FRs covered:** FR13, FR14
**Status:** DONE (Sprint 1)

### Epic 2: PDF Ingestion & Parsing
Enable the Ingestion Agent to read PDF files, clean noise (headers/footers), and extract raw text and images.
**FRs covered:** FR1, FR2, FR3, FR4
**Status:** DONE (Sprint 2)

### Epic 3: Agentic Chunking & Context
Implement the core logic for semantic segmentation and global context injection using Gemini.
**FRs covered:** FR5, FR6, FR7, FR15
**Status:** In Progress (Story 3.1 done)

### Epic 4: Structured Storage & Retrieval
Implement the Database Agent to validate data and store it in Firestore and Neo4j via A2A protocol.
**FRs covered:** FR10, FR11
**Status:** In Progress (Story 4.1 done)

### Epic 5: Visual & Tone Enrichment
Enrich knowledge assets by converting images to text descriptions and preserving author tone/style.
**FRs covered:** FR8, FR9, FR12

### Epic 6: CLI & Orchestration
Provide a command-line interface to trigger jobs and monitor progress.
**FRs covered:** FR1, FR14

### Epic 7: Advanced PDF Processing with Docling
Replace pypdf with ML-powered document understanding for superior text extraction, layout analysis, table parsing, and image detection. Enhancement overlay — swappable via `PDF_EXTRACTOR_BACKEND` environment variable.
**FRs covered:** FR2, FR3, FR4, FR15

