# pdf_to_knowledge - Epic Breakdown

**Author:** Jean
**Date:** 2025-11-26
**Project Level:** Expert
**Target Scale:** Enterprise

---

## Overview

This document provides the complete epic and story breakdown for pdf_to_knowledge, decomposing the requirements from the [PRD](./PRD.md) into implementable stories.

**Living Document Notice:** This is the initial version. It will be updated after UX Design and Architecture workflows add interaction and technical details to stories.

**Epic Structure:**
- **Epic 1: Foundation & Infrastructure** (Setup, Terraform, ADK Init)
- **Epic 2: PDF Ingestion & Parsing** (Ingestion Agent Core)
- **Epic 3: Agentic Chunking & Context** (Ingestion Agent Logic)
- **Epic 4: Structured Storage & Retrieval** (Database Agent & MCP)
- **Epic 5: Visual & Tone Extraction** (Enrichment)
- **Epic 6: CLI & Orchestration** (User Interface)
- **Epic 7: Advanced PDF Processing with Docling** (ML-based Extraction)

---

## Functional Requirements Inventory

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

---

## FR Coverage Map

- **Epic 1 (Foundation):** FR13, FR14 (Infrastructure setup)
- **Epic 2 (Ingestion):** FR1, FR2, FR3, FR4
- **Epic 3 (Chunking):** FR5, FR6, FR7, FR15
- **Epic 4 (Storage):** FR10, FR11
- **Epic 5 (Enrichment):** FR8, FR9, FR12
- **Epic 6 (CLI):** FR1, FR14 (Interface)
- **Epic 7 (Docling):** FR2, FR3, FR4, FR15 (Enhanced extraction quality)

---

## Epic 1: Foundation & Infrastructure

**Goal:** Establish the GCP infrastructure, ADK agent scaffolding, and local development environment to enable all subsequent work.

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
- Use `pypdf` or `pdfminer.six`
- Implement heuristic cleaning (regex for "Page X of Y", repeated headers)

### Story 2.2: Image Region Extraction

As a User,
I want the system to identify and extract charts and diagrams as separate image files,
So that they can be described by the vision model later.

**Acceptance Criteria:**
**Given** a PDF with images
**When** the Ingestion Agent processes it
**Then** it should save image artifacts to a temporary directory
**And** replace the image location in the text stream with a placeholder `[IMAGE: <id>]`

**Technical Notes:**
- Use PDF object extraction
- Filter out small icons/artifacts (< 100x100px)

---

## Epic 3: Agentic Chunking & Context

**Goal:** Implement the core logic for semantic segmentation and global context injection using Gemini.

### Story 3.1: Global Context Generation

As a User,
I want the system to generate a "Global Context" summary of the entire document,
So that individual chunks can be understood in relation to the whole.

**Acceptance Criteria:**
**Given** the full extracted text of a book
**When** the Chunking Engine runs
**Then** it should produce a 1-2 page high-level summary (Global Context)
**And** identify key terminology and definitions

**Technical Notes:**
- Use gemini-2.5-flash(large context window)
- Prompt engineering: "Summarize for the purpose of providing context to isolated chunks"

### Story 3.2: Semantic Segmentation

As a User,
I want the text divided into logical sections (semantic chunks) rather than fixed-size windows,
So that concepts are not split in the middle.

**Acceptance Criteria:**
**Given** the raw text stream
**When** the Chunking Engine runs
**Then** it should output chunks based on topic shifts or headers
**And** chunks should be between 500-1500 tokens ideally

**Technical Notes:**
- Use a "recursive" or "semantic" splitting strategy (can use LLM to identify break points or standard NLP libraries)

### Story 3.3: Context Injection

As a User,
I want each chunk to be prepended with relevant Global Context,
So that the chunk is self-contained for retrieval.

**Acceptance Criteria:**
**Given** a semantic chunk and the Global Context
**When** the Context Injector runs
**Then** it should prepend a brief "Context: ..." string to the chunk
**And** resolve any ambiguous pronouns (e.g., replace "it" with "the algorithm")

**Technical Notes:**
- Use Gemini Flash for speed/cost on per-chunk processing

---

## Epic 4: Structured Storage & Retrieval

**Goal:** Implement the Database Agent to validate data and store it in Firestore and Neo4j via A2A protocol.

### Story 4.1: A2A Protocol Definition

As a Developer,
I want to define the Protobuf/JSON schema for `StoreKnowledge` messages,
So that the Ingestion and Database agents communicate strictly.

**Acceptance Criteria:**
**Given** the shared schemas directory
**When** I define the `StoreKnowledgeRequest`
**Then** it should include fields for `chunk_text`, `global_context`, `visuals`, and `metadata`
**And** both agents should be able to import and validate this schema

**Technical Notes:**
- Define in `shared/schemas/knowledge.proto` or Pydantic models

### Story 4.2: Firestore Storage Implementation

As a System,
I want to store raw chunks and metadata in Firestore,
So that I have a durable record of the processed content.

**Acceptance Criteria:**
**Given** a valid `StoreKnowledgeRequest`
**When** the Database Agent receives it
**Then** it should write a document to the `chunks` collection
**And** return the generated Firestore ID

**Technical Notes:**
- Use `google-cloud-firestore` library
- Implement batch writes if possible

### Story 4.3: Neo4j Graph Storage

As a System,
I want to store relationships between concepts in Neo4j,
So that I can perform graph-based retrieval.

**Acceptance Criteria:**
**Given** a chunk with extracted keywords/concepts
**When** the Database Agent processes it
**Then** it should create `(:Concept)` nodes and `(:Chunk)` nodes
**And** create `(:Chunk)-[:MENTIONS]->(:Concept)` relationships

**Technical Notes:**
- Use `neo4j` python driver
- Ensure idempotency (MERGE instead of CREATE)

---

## Epic 5: Visual & Tone Extraction

**Goal:** Enrich the knowledge assets by converting images to text descriptions and preserving author tone.

### Story 5.1: Visual Description Agent

As a User,
I want charts and diagrams to be converted into detailed text descriptions,
So that text-only agents can understand the visual information.

**Acceptance Criteria:**
**Given** an extracted image artifact
**When** the Enrichment Agent processes it
**Then** it should call Gemini Pro Vision
**And** return a detailed textual description of the visual
**And** store this description in the chunk metadata

**Technical Notes:**
- Prompt: "Describe this technical diagram in detail for a blind reader..."

### Story 5.2: Tone Analysis & Preservation

As a User,
I want the system to capture the author's tone and style,
So that downstream podcast agents can mimic the voice.

**Acceptance Criteria:**
**Given** the global context and sample chunks
**When** the analysis runs
**Then** it should output a `tone_profile` (e.g., "Academic, Formal, Enthusiastic")
**And** store this in the document metadata

---

## Epic 6: CLI & Orchestration

**Goal:** Provide a user interface to trigger jobs and monitor progress.

### Story 6.1: CLI Ingest Command

As a User,
I want to run `p2k ingest <file.pdf>`,
So that I can start the processing pipeline.

**Acceptance Criteria:**
**Given** a PDF file
**When** I run the command
**Then** it should upload the file to a GCS bucket
**And** trigger the Ingestion Agent via gRPC/REST
**And** return a Job ID

**Technical Notes:**
- Use `typer` or `click` for CLI
- Upload to `gs://<project>-raw-pdfs/`

### Story 6.2: Job Status Monitoring

As a User,
I want to check the status of my ingestion job,
So that I know when it's finished.

**Acceptance Criteria:**
**Given** a Job ID
**When** I run `p2k status <job_id>`
**Then** it should query the Database Agent (or Firestore directly)
**And** display the current status (Processing, Completed, Failed) and progress %

---

## Epic 7: Advanced PDF Processing with Docling

**Goal:** Implement the Docling-based extraction backend to replace pypdf with ML-powered document understanding, providing superior text extraction, layout analysis, table parsing, and image detection. The backend is swappable via `PDF_EXTRACTOR_BACKEND` environment variable.

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
- Use `DocumentConverter` as the primary entry point
- Map Docling's `DoclingDocument` structure to existing `ExtractionResult` / `PageText` dataclasses
- Docling uses DocLayNet-based models for layout classification (headings, paragraphs, tables, figures, page headers/footers)
- Headers/footers are classified by the model rather than frequency heuristics — populate `detected_headers` / `detected_footers` from Docling's classifications
- First-run downloads layout models (~200-500 MB) — handle gracefully or bake into Docker image
- Use Docling's Markdown export as intermediate format for structured text

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
- Docling identifies figure regions via layout classification, not just /XObject parsing
- This catches rendered charts (e.g., matplotlib output) that pypdf misses since they aren't embedded as XObjects
- For images that are XObjects, Docling extracts them directly
- For detected figure regions that aren't XObjects, render the page region to an image (via `pdf2image` or Docling's built-in rendering)
- Map extracted figures to `ImageMetadata` with sequential IDs (img_001, img_002)
- Store to same output directory pattern: `/tmp/p2k-images/<job_id>/`

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
- Tables are exported as Markdown tables by default when using `DocumentConverter.convert()` with Markdown export
- This is a major advantage over pypdf, which typically garbles table content into disconnected strings
- Consider adding a `TableMetadata` model in the future for programmatic table access
- For now, Markdown table format in the text stream is sufficient

### Story 7.4: Docker Image & Model Caching for Docling

As a Developer,
I want the Docling ML models to be baked into the Docker image,
So that first-run latency is eliminated and the container works in air-gapped environments.

**Acceptance Criteria:**
**Given** a fresh container start with `PDF_EXTRACTOR_BACKEND=docling`
**When** the first PDF is processed
**Then** no model download should occur at runtime
**And** the container should be able to process PDFs immediately
**And** container size should be documented (expected: 3-5 GB)

**Technical Notes:**
- Add a Dockerfile stage that pre-downloads Docling models during build
- Models are cached in `~/.cache/docling/` (or configurable via `DOCLING_CACHE_DIR`)
- Run a dummy conversion during Docker build to trigger model download
- Consider a multi-stage build: `docling` image extends the base `ingestion-agent` image
- Document the size trade-off: pypdf image (~300 MB) vs docling image (~3-5 GB)
- The base Dockerfile remains unchanged — only add a `Dockerfile.docling` or build arg

### Story 7.5: Docling Backend Tests & Benchmark

As a Developer,
I want comprehensive tests and a performance benchmark comparing pypdf vs Docling extraction,
So that the quality and speed trade-offs are documented.

**Acceptance Criteria:**
**Given** the `DoclingBackend` implementation
**When** the test suite runs
**Then** all existing acceptance criteria for Stories 2.1 and 2.2 should pass with the Docling backend
**And** a benchmark script compares pypdf vs Docling on 3 sample PDFs (text-only, with images, 100+ pages)
**And** results document: extraction quality, processing time, and output differences
**And** all integration tests pass with both backends

**Technical Notes:**
- Reuse existing test assertions — the backend must produce the same `ExtractionResult` / `ImageExtractionResult` interfaces
- Add parametrized tests that run against both backends: `@pytest.mark.parametrize("backend", ["pypdf", "docling"])`
- Benchmark script: `scripts/benchmark_backends.py` that processes sample PDFs and outputs comparison table
- Expected results: Docling ~10-30x slower, but significantly better quality on complex layouts, tables, and multi-column PDFs
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
| FR12 | Human-readable summary | Story 3.1 (Global Context serves this) |
| FR13 | Containerized workload | Story 1.1, 1.2 |
| FR14 | Log processing steps | Story 1.2, 6.2 |
| FR15 | Handle 500+ pages | Story 3.1 (Large Context Window) |

---

## Summary

**Total Epics:** 7
**Total Stories:** 18

This breakdown covers all functional requirements and establishes a robust foundation for the pdf_to_knowledge pipeline. The stories are vertically sliced to deliver value incrementally, starting with infrastructure and moving through the data processing pipeline.

---

_For implementation: Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown._
