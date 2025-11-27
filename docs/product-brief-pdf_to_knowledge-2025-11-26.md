# Product Brief: pdf_to_knowledge

**Date:** 2025-11-26
**Author:** Jean
**Context:** Greenfield Project

---

## Executive Summary

**pdf_to_knowledge** is a specialized ingestion and processing pipeline designed to transform dense, technical PDF books (300+ pages) into structured, multi-modal knowledge assets. Unlike simple "chat with PDF" tools, this system uses **agentic chunking with context continuity** and **semantic segmentation** to preserve the logical flow of complex technical concepts.

The primary goal is to **pre-compute downstream needs** for both human learners and AI agents. It produces a dual-layer output:
1.  **Structured Data for AI Agents:** A rigorous schema containing semantic chunks, visual descriptions for infographics, and tone-preserved scripts for podcast generation.
2.  **Enhanced Summaries for Humans:** High-fidelity narratives that retain technical depth without the "dryness" of standard summaries.

Targeting professional learners and AI researchers, the system leverages **Agentic RAG**, **Knowledge Graphs**, and **GCP infrastructure** to serve as a robust foundation for complex, private-data agentic systems.

---

## Core Vision

### Problem Statement

Technical books are valuable but "dead" data formats. They are difficult for AI agents to consume effectively due to context window limits, "lost in the middle" issues, and the lack of semantic structure. Standard RAG approaches often fragment complex concepts, leading to hallucinations or shallow retrieval. Furthermore, converting this dense text into engaging formats (podcasts, infographics) requires significant manual effort or complex, error-prone prompting chains.

### Proposed Solution

A sophisticated ingestion pipeline that treats the PDF not as text strings, but as a **knowledge graph source**.
*   **Ingestion:** Automated cleaning and noise reduction.
*   **Processing:** Agentic chunking that injects "Global Context" into every segment to ensure continuity.
*   **Enrichment:** Explicit extraction of visual descriptions (for infographics) and tonal elements (for podcasts).
*   **Storage:** Structured output stored in a private GCP database, ready for high-fidelity retrieval.

### Key Differentiators

1.  **Context Continuity:** Solves the "fragmented concept" problem by injecting global context into local chunks.
2.  **Pre-computation:** Moves the cognitive load upstream, creating "ready-to-use" assets for downstream agents (Podcast/Infographic) rather than requiring them to process raw text.
3.  **Dual-Layer Output:** Serves both machine consumers (strict schema) and human consumers (narrative flow).
4.  **Infrastructure-Ready:** Built for GCP, supporting private, secure, and scalable agentic workflows.

---

## Target Users

### Primary Users

*   **Professional Learners:** Individuals needing to rapidly absorb complex technical material without losing depth.
*   **AI Agent Researchers:** Developers building advanced agentic systems who need high-quality, structured context from DRM-free technical books that were not in the LLM's training set.

### Secondary Users

*   **Content Creators:** Users looking to automate the creation of educational content (podcasts, infographics) from technical sources.

---

## Success Metrics

### Primary Metric

*   **Data Structure Validity:** The output JSON/Schema must be 100% valid and semantically complete, ensuring downstream agents (Podcast/Infographic) can consume it without error or hallucination.

### Secondary Metrics

*   **Context Retention:** Downstream agents should correctly reference concepts defined in earlier chapters (measured by lack of "undefined concept" hallucinations).
*   **Retrieval Accuracy:** RAG systems using this data should show improved precision/recall compared to standard chunking.

---

## MVP Scope

### Core Features

1.  **PDF Ingestion & Cleaning:** Automated removal of headers, footers, and artifacts.
2.  **Agentic Chunking Engine:** Semantic segmentation with "Global Context" injection.
3.  **Visual Description Extractor:** Agent specialized in converting charts/diagrams into descriptive text prompts.
4.  **Structured Output Generator:** JSON export conforming to the strict schema for Podcast/Infographic agents.
5.  **GCP Integration:** Basic pipeline deployment to Google Cloud Platform.

### Out of Scope (for MVP)

*   The actual *generation* of the audio podcast (this is a downstream agent's job).
*   The actual *rendering* of the infographic image (this is a downstream agent's job).
*   User Interface (CLI or API-first for MVP).
