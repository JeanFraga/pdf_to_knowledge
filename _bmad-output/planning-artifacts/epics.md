---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/implementation-artifacts/backlog.md
  - _bmad-output/planning-artifacts/implementation-readiness-report.md
  - _bmad-output/implementation-artifacts/sprint-status.yaml
  - _bmad-output/implementation-artifacts/sprint-1.md
  - _bmad-output/implementation-artifacts/sprint-2.md
---

# pdf_to_knowledge - Epic Breakdown

**Author:** Jean
**Date:** 2026-02-25
**Rebuild:** Full rebuild from BMAD v6 workflow (previously v4)

---

## Overview

This document provides the complete epic and story breakdown for pdf_to_knowledge, decomposing the requirements from the PRD and Architecture into implementable stories.

**Implementation Progress:** Sprints 1–2 completed (6 stories done, 121 tests passing). This is a full rebuild of the epics document to align with BMAD v6 workflow format.

**Epic Structure:**
- **Epic 1: Foundation & Infrastructure** (Setup, Terraform, ADK Init) — DONE
- **Epic 2: PDF Ingestion & Parsing** (Ingestion Agent Core) — DONE
- **Epic 3: Agentic Chunking & Context** (Ingestion Agent Logic) — In Progress
- **Epic 4: Structured Storage & Retrieval** (Database Agent & A2A) — In Progress
- **Epic 5: Visual & Tone Enrichment** (Enrichment)
- **Epic 6: CLI & Orchestration** (User Interface)
- **Epic 7: Advanced PDF Processing with Docling** (ML-based Extraction Enhancement)

---

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

---

### FR Coverage Map

- **Epic 1 (Foundation):** FR13, FR14 — Infrastructure and logging
- **Epic 2 (Ingestion):** FR1, FR2, FR3, FR4 — PDF parsing, text/image extraction
- **Epic 3 (Chunking):** FR5, FR6, FR7, FR15 — Semantic segmentation, context injection, large docs
- **Epic 4 (Storage):** FR10, FR11 — Schema validation, JSON output, database persistence
- **Epic 5 (Enrichment):** FR8, FR9, FR12 — Visual descriptions, tone, human summary
- **Epic 6 (CLI):** FR1, FR14 — CLI interface, job monitoring
- **Epic 7 (Docling):** FR2, FR3, FR4, FR15 — ML-based extraction quality enhancement

---

## Epic 1: Foundation & Infrastructure

**Goal:** Establish the GCP infrastructure, ADK agent scaffolding, and local development environment to enable all subsequent work.
**Status:** DONE (Sprint 1)

### Story 1.1: Project Initialization & Terraform Setup

As a Developer,
I want to initialize the project repository with Terraform and ADK structures,
So that I have a consistent foundation for infrastructure and agent development.

**Acceptance Criteria:**
**Given** a clean git repository
**When** I run the setup commands
**Then** I should see a `infrastructure/terraform` directory with `main.tf`
**And** I should see `agents/ingestion-agent` and `agents/database-agent` directories created via `adk init`
**And** I should see a `docker-compose.yml` for local orchestration

**Technical Notes:**
- Use Terraform 1.5+
- Configure GCS backend for Terraform state
- Define GKE Autopilot cluster resource in Terraform

### Story 1.2: Local Development Environment with Gemini

As a Developer,
I want to run the agents locally using Docker Compose and connect them to Gemini API,
So that I can test agent logic without deploying to GCP.

**Acceptance Criteria:**
**Given** I have a Gemini API key
**When** I run `docker-compose up`
**Then** both agents should start successfully
**And** the Ingestion Agent should be able to make a "Hello World" call to Gemini Flash
**And** logs should appear in the console

**Technical Notes:**
- Mount API keys as environment variables
- Configure `adk` to use local network for A2A discovery in dev mode

---

## Epic 2: PDF Ingestion & Parsing

**Goal:** Enable the Ingestion Agent to read PDF files, clean noise (headers/footers), and extract raw text and images.
**Status:** DONE (Sprint 2)

### Story 2.1: PDF Text Extraction Service

As a User,
I want the system to extract raw text from a PDF file,
So that the content can be processed by the chunking engine.

**Acceptance Criteria:**
**Given** a valid PDF file path
**When** the Ingestion Agent processes it
**Then** it should return a stream of text
**And** paragraph structure should be preserved
**And** page numbers and headers/footers should be stripped (heuristic based)

**Technical Notes:**
- Use `pypdf` for text extraction
- Implement heuristic cleaning (regex for "Page X of Y", repeated headers >70% frequency)
- Extraction backend abstraction via `PDF_EXTRACTOR_BACKEND` env var (strategy pattern)

### Story 2.2: Image Region Extraction

As a User,
I want the system to identify and extract charts and diagrams as separate image files,
So that they can be described by the vision model later.

**Acceptance Criteria:**
**Given** a PDF with images
**When** the Ingestion Agent processes it
**Then** it should save image artifacts to a temporary directory
**And** replace the image location in the text stream with a placeholder `[IMAGE: <id>]`
**And** small artifacts (< 100x100px) should be filtered out

**Technical Notes:**
- Use PDF /XObject resource extraction via pypdf
- Filter by minimum dimensions (100x100px)
- Store to `/tmp/p2k-images/<job_id>/`
- Sequential IDs: `img_001`, `img_002`, etc.

---

## Epic 3: Agentic Chunking & Context

**Goal:** Implement the core logic for semantic segmentation and global context injection using Gemini.
**Status:** In Progress (Story 3.1 done)

### Story 3.1: Global Context Generation

As a User,
I want the system to generate a "Global Context" summary of the entire document,
So that individual chunks can be understood in relation to the whole.

**Acceptance Criteria:**
**Given** the full extracted text of a book
**When** the Chunking Engine runs
**Then** it should produce a 1-2 page high-level summary (Global Context)
**And** identify key terminology and definitions
**And** classify the document type
**And** handle documents up to 500 pages via large context window

**Technical Notes:**
- Uses `gemini-2.0-flash` (large context window)
- Outputs `GlobalContext` model with `summary`, `key_terms[]`, `main_themes[]`, `document_type`, `target_audience`
- Prompt engineering for context provision to isolated chunks
- **Status:** DONE — 28 tests passing

### Story 3.2: Semantic Segmentation

As a User,
I want the text divided into logical sections (semantic chunks) rather than fixed-size windows,
So that concepts are not split in the middle.

**Acceptance Criteria:**
**Given** the raw text stream from PDF extraction
**When** the Chunking Engine runs
**Then** it should output chunks based on topic shifts or document headers
**And** chunks should be between 500–1500 tokens ideally
**And** each chunk should preserve its source page range
**And** chunk boundaries should not split mid-paragraph

**Technical Notes:**
- Use recursive or semantic splitting strategy
- Can use LLM to identify break points or standard NLP libraries
- Output as list of `KnowledgeChunk` objects (from `shared/schemas/knowledge.py`)
- Must integrate with the existing `ExtractionResult` from `process_pdf_full()`

### Story 3.3: Context Injection

As a User,
I want each chunk to be prepended with relevant Global Context,
So that the chunk is self-contained for retrieval.

**Acceptance Criteria:**
**Given** a semantic chunk and the Global Context
**When** the Context Injector runs
**Then** it should prepend a brief "Context: ..." string to the chunk
**And** resolve any ambiguous pronouns (e.g., replace "it" with "the algorithm")
**And** the injected context should be stored in the `context_injection` field of `KnowledgeChunk`

**Technical Notes:**
- Use Gemini Flash for speed/cost on per-chunk processing
- Depends on Story 3.1 (GlobalContext) and 3.2 (chunks to inject into)
- Output populates `KnowledgeChunk.context_injection` and `KnowledgeChunk.global_context`

---

## Epic 4: Structured Storage & Retrieval

**Goal:** Implement the Database Agent to validate data and store it in Firestore and Neo4j via A2A protocol.
**Status:** In Progress (Story 4.1 done)

### Story 4.1: A2A Protocol Definition

As a Developer,
I want to define the JSON schema for `StoreKnowledge` messages,
So that the Ingestion and Database agents communicate with a strict contract.

**Acceptance Criteria:**
**Given** the shared schemas directory
**When** I define the `StoreKnowledgeRequest`
**Then** it should include fields for `chunk_text`, `global_context`, `visuals`, and `metadata`
**And** both agents should be able to import and validate this schema
**And** schema version should be documented

**Technical Notes:**
- Pydantic models in `shared/schemas/knowledge.py`
- Includes `StoreKnowledgeRequest`, `StoreKnowledgeResponse`, `KnowledgeChunk`, `ChunkMetadata`, `VisualDescription`
- Validation utilities in `shared/schemas/validation.py`
- **Status:** DONE

### Story 4.2: Firestore Storage Implementation

As a System,
I want to store raw chunks and metadata in Firestore,
So that I have a durable record of the processed content.

**Acceptance Criteria:**
**Given** a valid `StoreKnowledgeRequest`
**When** the Database Agent receives it
**Then** it should write a document to the `chunks` collection
**And** create/update a document in the `jobs` collection with processing status
**And** return the generated Firestore ID in `StoredChunkResult`
**And** support batch writes for multiple chunks in a single request

**Technical Notes:**
- Use `google-cloud-firestore` library
- Implement batch writes for efficiency
- Collections: `chunks`, `jobs` (per architecture)
- Database Agent currently a skeleton — this story implements the core storage logic

### Story 4.3: Neo4j Graph Storage

As a System,
I want to store relationships between concepts in Neo4j,
So that I can perform graph-based retrieval.

**Acceptance Criteria:**
**Given** a chunk with extracted keywords/concepts
**When** the Database Agent processes it
**Then** it should create `(:Concept)` nodes and `(:Chunk)` nodes
**And** create `(:Chunk)-[:MENTIONS]->(:Concept)` relationships
**And** create `(:Chapter)` and `(:Book)` nodes with `DEFINED_IN`, `PRECEDES`, `RELATED_TO` edges
**And** use MERGE for idempotency (no duplicate nodes on re-processing)

**Technical Notes:**
- Use `neo4j` Python driver
- Node types: `Concept`, `Chunk`, `Chapter`, `Book` (per architecture)
- Edge types: `DEFINED_IN`, `MENTIONED_IN`, `PRECEDES`, `RELATED_TO`
- Ensure idempotency with MERGE instead of CREATE

---

## Epic 5: Visual & Tone Enrichment

**Goal:** Enrich knowledge assets by converting images to text descriptions and preserving author tone/style.

### Story 5.1: Visual Description Generation

As a User,
I want charts and diagrams to be converted into detailed text descriptions,
So that text-only agents can understand the visual information.

**Acceptance Criteria:**
**Given** an extracted image artifact from the image extraction pipeline
**When** the Enrichment Agent processes it
**Then** it should call Gemini with vision capabilities
**And** return a detailed textual description of the visual
**And** populate the `VisualDescription` model with `visual_id`, `visual_type`, `description`, and `page_number`
**And** store this description in the chunk metadata

**Technical Notes:**
- Use Gemini with vision capabilities for image understanding
- Prompt: "Describe this technical diagram in detail for a blind reader..."
- Output maps to existing `VisualDescription` Pydantic model in `shared/schemas/knowledge.py`
- Integrates with `ImageExtractionResult` from Story 2.2

### Story 5.2: Tone Analysis & Preservation

As a User,
I want the system to capture the author's tone and style,
So that downstream podcast agents can mimic the voice.

**Acceptance Criteria:**
**Given** the global context and sample chunks
**When** the tone analysis runs
**Then** it should output a `tone_profile` (e.g., "Academic, Formal, Enthusiastic")
**And** store this in the `ChunkMetadata.tone` field
**And** generate a human-readable summary document for the source PDF

**Technical Notes:**
- Use Gemini Flash for tone classification
- Populates `ChunkMetadata.tone` field (already exists in schema)
- FR12 (human-readable summary) is produced as a by-product alongside the tone profile

---

## Epic 6: CLI & Orchestration

**Goal:** Provide a command-line interface to trigger jobs and monitor progress.

### Story 6.1: CLI Ingest Command

As a User,
I want to run `p2k ingest <file.pdf>`,
So that I can start the processing pipeline.

**Acceptance Criteria:**
**Given** a PDF file path
**When** I run `p2k ingest <file.pdf> --output <dir>`
**Then** it should upload the file to a GCS bucket
**And** trigger the Ingestion Agent via gRPC/REST
**And** return a Job ID
**And** display initial processing status

**Technical Notes:**
- Use `typer` or `click` for CLI framework
- Upload to `gs://<project>-raw-pdfs/`
- Calls `process_pdf_full()` pipeline under the hood
- Async job creation — returns immediately with Job ID

### Story 6.2: Job Status Monitoring

As a User,
I want to check the status of my ingestion job,
So that I know when it's finished.

**Acceptance Criteria:**
**Given** a Job ID
**When** I run `p2k status <job_id>`
**Then** it should query the Database Agent (or Firestore directly)
**And** display the current status (Processing, Completed, Failed)
**And** show progress percentage
**And** display chunk count and error count if applicable

**Technical Notes:**
- Reads from `jobs` collection in Firestore (created by Story 4.2)
- Depends on Epic 4 for job state persistence

---

## Epic 7: Advanced PDF Processing with Docling

**Goal:** Replace pypdf with ML-powered document understanding for superior text extraction, layout analysis, table parsing, and image detection. Enhancement overlay — swappable via `PDF_EXTRACTOR_BACKEND` environment variable.

**Prerequisite:** Extraction backend abstraction (completed in Sprint 2 — `extraction_backend.py` with strategy pattern).

### Story 7.1: Docling Integration & DoclingBackend Implementation

As a Developer,
I want to implement the `DoclingBackend` class using the Docling library,
So that the system can use ML-based layout analysis for PDF text extraction.

**Acceptance Criteria:**
**Given** `PDF_EXTRACTOR_BACKEND=docling` in the environment
**When** the ingestion pipeline processes a PDF
**Then** the `DoclingBackend.extract_text()` should return an `ExtractionResult` with cleaned text
**And** paragraph structure should be preserved using Docling's layout model
**And** headers, footers, and page numbers should be detected via layout analysis (not just regex heuristics)
**And** the result should be compatible with all downstream consumers (`process_pdf_full()`, `ContextGenerator`)

**Technical Notes:**
- Install `docling` package (pulls PyTorch/ONNX for layout models)
- Use `DocumentConverter` as primary entry point
- Map `DoclingDocument` to existing `ExtractionResult` / `PageText` dataclasses
- Layout model classifies headings, paragraphs, tables, figures, page headers/footers
- Use Docling's Markdown export as intermediate format

### Story 7.2: Docling Image & Figure Extraction

As a Developer,
I want the `DoclingBackend` to extract images and figures using Docling's layout analysis,
So that charts, diagrams, and figures are detected by their visual role (not just /XObject resources).

**Acceptance Criteria:**
**Given** a PDF with embedded charts, diagrams, or figures
**When** the `DoclingBackend.extract_images()` processes it
**Then** figures identified by layout analysis should be extracted as image files
**And** small artifacts (< 100x100px) should still be filtered
**And** `ImageMetadata` objects should be created with correct page, dimensions, and format
**And** the result should be compatible with `ImageExtractionResult` and placeholder injection

**Technical Notes:**
- Docling identifies figure regions via layout classification (catches rendered charts pypdf misses)
- For XObject images: direct extraction; for figure regions: render via `pdf2image`
- Same output directory pattern: `/tmp/p2k-images/<job_id>/`

### Story 7.3: Docling Table Extraction

As a Developer,
I want the system to extract tables as structured data using Docling,
So that tabular information is preserved in a machine-readable format instead of mangled text.

**Acceptance Criteria:**
**Given** a PDF containing tables
**When** the `DoclingBackend` processes it
**Then** tables should be extracted as structured Markdown tables in the text stream
**And** the original table structure (rows, columns, headers) should be preserved
**And** table locations in the text should maintain reading order

**Technical Notes:**
- Docling uses TableFormer model for table structure recognition
- Tables exported as Markdown tables by default
- Major quality improvement over pypdf's garbled table output

### Story 7.4: Docker Image & Model Caching for Docling

As a Developer,
I want the Docling ML models to be baked into the Docker image,
So that first-run latency is eliminated and the container works in air-gapped environments.

**Acceptance Criteria:**
**Given** a fresh container start with `PDF_EXTRACTOR_BACKEND=docling`
**When** the first PDF is processed
**Then** no model download should occur at runtime
**And** the container should process PDFs immediately
**And** container size should be documented (expected: 3–5 GB)

**Technical Notes:**
- Pre-download models during Docker build (`~/.cache/docling/`)
- Multi-stage build: `Dockerfile.docling` extends base ingestion-agent image
- Document size trade-off: pypdf (~300 MB) vs docling (~3–5 GB)

### Story 7.5: Docling Backend Tests & Benchmark

As a Developer,
I want comprehensive tests and a performance benchmark comparing pypdf vs Docling,
So that the quality and speed trade-offs are documented.

**Acceptance Criteria:**
**Given** the `DoclingBackend` implementation
**When** the test suite runs
**Then** all existing acceptance criteria for Stories 2.1 and 2.2 should pass with the Docling backend
**And** a benchmark script compares pypdf vs Docling on 3 sample PDFs
**And** results document extraction quality, processing time, and output differences
**And** all integration tests pass with both backends

**Technical Notes:**
- Parametrized tests: `@pytest.mark.parametrize("backend", ["pypdf", "docling"])`
- Benchmark script: `scripts/benchmark_backends.py`
- Document results in `docs/backend-comparison.md`

---

## FR Coverage Matrix

| FR ID | Description | Covered By |
| :--- | :--- | :--- |
| FR1 | Ingest PDF via CLI | Story 6.1, 2.1 |
| FR2 | Remove headers/footers | Story 2.1, 7.1 |
| FR3 | Extract raw text | Story 2.1, 7.1 |
| FR4 | Extract image regions | Story 2.2, 7.2 |
| FR5 | Semantic segmentation | Story 3.2 |
| FR6 | Global Context summary | Story 3.1 |
| FR7 | Inject Global Context | Story 3.3 |
| FR8 | Visual descriptions | Story 5.1 |
| FR9 | Preserve tone/style | Story 5.2 |
| FR10 | Validate JSON schema | Story 4.1 |
| FR11 | Generate JSON output | Story 4.2 |
| FR12 | Human-readable summary | Story 5.2 |
| FR13 | Containerized workload | Story 1.1, 1.2 |
| FR14 | Log processing steps | Story 1.2, 6.2 |
| FR15 | Handle 500+ pages | Story 3.1, 7.1 |

---

## Summary

**Total Epics:** 7
**Total Stories:** 19
**Stories Done:** 6 (Sprints 1–2)
**Stories Remaining:** 13

This breakdown covers all 15 functional requirements and establishes a robust foundation for the pdf_to_knowledge pipeline. The stories are vertically sliced to deliver value incrementally.

---

_For implementation: Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown._
