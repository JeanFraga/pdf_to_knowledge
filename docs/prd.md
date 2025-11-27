# pdf_to_knowledge - Product Requirements Document

**Author:** Jean
**Date:** 2025-11-26
**Version:** 1.0

---

## Executive Summary

**pdf_to_knowledge** is a specialized ingestion and processing pipeline designed to transform dense, technical PDF books (300+ pages) into structured, multi-modal knowledge assets. Unlike simple "chat with PDF" tools, this system uses **agentic chunking with context continuity** and **semantic segmentation** to preserve the logical flow of complex technical concepts.

The primary goal is to **pre-compute downstream needs** for both human learners and AI agents. It produces a dual-layer output:
1.  **Structured Data for AI Agents:** A rigorous schema containing semantic chunks, visual descriptions for infographics, and tone-preserved scripts for podcast generation.
2.  **Enhanced Summaries for Humans:** High-fidelity narratives that retain technical depth without the "dryness" of standard summaries.

Targeting professional learners and AI researchers, the system leverages **Agentic RAG**, **Knowledge Graphs**, and **GCP infrastructure** to serve as a robust foundation for complex, private-data agentic systems.

### What Makes This Special

**Context Continuity:** Solves the "fragmented concept" problem by injecting global context into local chunks.
**Pre-computation:** Moves the cognitive load upstream, creating "ready-to-use" assets for downstream agents (Podcast/Infographic) rather than requiring them to process raw text.
**Dual-Layer Output:** Serves both machine consumers (strict schema) and human consumers (narrative flow).

---

## Project Classification

**Technical Type:** api_backend (with CLI components)
**Domain:** scientific (AI/Knowledge Engineering)
**Complexity:** medium

The project is a backend processing pipeline with a CLI interface, operating in the domain of AI and Knowledge Engineering. It requires high precision and structured data handling.

---

## Success Criteria

**Primary Metric:**
*   **Data Structure Validity:** The output JSON/Schema must be 100% valid and semantically complete, ensuring downstream agents (Podcast/Infographic) can consume it without error or hallucination.

**Secondary Metrics:**
*   **Context Retention:** Downstream agents should correctly reference concepts defined in earlier chapters (measured by lack of "undefined concept" hallucinations).
*   **Retrieval Accuracy:** RAG systems using this data should show improved precision/recall compared to standard chunking.

---

## Product Scope

### MVP - Minimum Viable Product

1.  **PDF Ingestion & Cleaning:** Automated removal of headers, footers, and artifacts.
2.  **Agentic Chunking Engine:** Semantic segmentation with "Global Context" injection.
3.  **Visual Description Extractor:** Agent specialized in converting charts/diagrams into descriptive text prompts.
4.  **Structured Output Generator:** JSON export conforming to the strict schema for Podcast/Infographic agents.
5.  **GCP Integration:** Basic pipeline deployment to Google Cloud Platform.
6.  **CLI Interface:** Basic command-line tool to trigger ingestion and monitor status.

### Growth Features (Post-MVP)

*   **Audio Generation:** Integration with TTS/Audio generation agents.
*   **Infographic Rendering:** Integration with Image generation agents.
*   **API Layer:** REST/GraphQL API for programmatic access.
*   **Web UI:** Dashboard for managing jobs and viewing results.

### Vision (Future)

To become the standard "ETL for Knowledge" pipeline, capable of ingesting any technical document and converting it into a universal knowledge graph format usable by any agentic system.

---

## Domain-Specific Requirements

**Domain:** Scientific / AI Research

**Validation Methodology:**
*   Automated schema validation for all outputs.
*   Semantic consistency checks (using LLM evaluators) to ensure chunks retain meaning.

**Computational Resources:**
*   Pipeline must be optimized for long-running tasks (300+ page processing).
*   Efficient use of context windows during processing to manage costs.

**Accuracy & Precision:**
*   High fidelity in extracting technical terms and formulas.
*   Zero tolerance for "hallucinated" content in the structured output.

---

## Innovation & Novel Patterns

**Agentic Chunking with Context Continuity:**
*   **Pattern:** Instead of blind sliding windows, the system analyzes the document structure and injects a "running summary" or "global context" into each chunk.
*   **Validation:** Compare retrieval performance of these chunks vs. standard chunks on multi-hop reasoning questions.

**Dual-Layer Output:**
*   **Pattern:** Simultaneous generation of machine-readable (JSON) and human-readable (Narrative) formats.

---

## api_backend Specific Requirements

### API/CLI Specification

*   **CLI Command:** `p2k ingest <file_path> --output <dir>`
*   **CLI Command:** `p2k status <job_id>`
*   **Input:** PDF files (text-based, DRM-free).
*   **Output:** JSON file containing the structured knowledge asset.

### Data Schemas

**Output JSON Schema (Draft):**
```json
{
  "metadata": { ... },
  "global_context": "...",
  "chunks": [
    {
      "id": "...",
      "text": "...",
      "context_injection": "...",
      "visuals": [ { "description": "..." } ],
      "keywords": [ ... ]
    }
  ]
}
```

### Error Handling

*   Graceful handling of corrupt PDFs.
*   Logging of processing failures at the chunk level.
*   Retry mechanism for LLM API calls.

---

## Functional Requirements

**Ingestion & Pre-processing**
1.  System can ingest PDF documents via CLI path.
2.  System can identify and remove page headers, footers, and page numbers.
3.  System can extract raw text while preserving paragraph structure.
4.  System can identify and extract image regions (charts, diagrams).

**Core Processing (Agentic Chunking)**
5.  System can perform semantic segmentation to divide text into logical sections.
6.  System can generate a "Global Context" summary for the document.
7.  System can inject relevant Global Context into each local chunk.
8.  System can generate visual descriptions for extracted image regions.
9.  System can preserve tone and style in a separate metadata field.

**Output Generation**
10. System can validate processed data against a strict JSON schema.
11. System can generate the final JSON output file.
12. System can generate a human-readable summary document.

**Infrastructure & Operations**
13. System can run as a containerized workload on GCP.
14. System can log processing steps and status to stdout/logging service.
15. System can handle documents up to 500 pages in length.

---

## Non-Functional Requirements

### Performance
*   **Processing Time:** Should process a 300-page book in under 30 minutes (assuming standard LLM latency).
*   **Concurrency:** Capable of processing multiple books in parallel (dependent on quota).

### Security
*   **Data Privacy:** Input PDFs and output data must remain within the user's GCP project/VPC.
*   **Credential Management:** API keys and secrets managed via GCP Secret Manager.

### Scalability
*   **Modular Design:** Pipeline steps should be decoupled to allow independent scaling or replacement of models.

### Reliability
*   **Fault Tolerance:** Pipeline should resume from the last successful step in case of failure.

### Local Development & Testing
*   **Local Execution:** All components must be runnable and testable locally using Docker containers.
*   **Model Support:** Local testing must support integration with Gemini models.

---

_This PRD captures the essence of pdf_to_knowledge - A robust pipeline for transforming technical PDFs into agent-ready knowledge assets._

_Created through collaborative discovery between Jean and AI facilitator._
