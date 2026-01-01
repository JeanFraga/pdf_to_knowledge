# Story 2.1: PDF Text Extraction Service

**Status:** Ready for Dev  
**Sprint:** 2  
**Epic:** PDF Ingestion & Parsing  
**Estimate:** 2-3 days  

---

## Story

**As a** User,  
**I want** the system to extract raw text from a PDF file,  
**So that** the content can be processed by the chunking engine.

---

## Acceptance Criteria

- [ ] **AC1:** Given a valid PDF file path, the Ingestion Agent can process it
- [ ] **AC2:** Paragraph structure is preserved in extracted text
- [ ] **AC3:** Page numbers are stripped (heuristic: "Page X of Y", "- X -")
- [ ] **AC4:** Repeated headers/footers are detected and removed
- [ ] **AC5:** Text stream is returned for downstream processing

---

## Tasks/Subtasks

- [ ] **2.1.1** Add `pypdf` to ingestion-agent requirements
- [ ] **2.1.2** Create `pdf_extractor.py` module in `agents/ingestion-agent/src/`
- [ ] **2.1.3** Implement raw text extraction with page iteration
- [ ] **2.1.4** Implement header/footer detection heuristics
- [ ] **2.1.5** Implement page number removal regex patterns
- [ ] **2.1.6** Add unit tests with sample PDF files
- [ ] **2.1.7** Integrate extractor into agent main flow

---

## Dev Notes

- Use `pypdf` (modern fork of PyPDF2) for better maintenance and active development
- Header/footer detection strategy:
  - Track first 3 lines and last 3 lines of each page
  - If >70% of pages share the same lines, flag as header/footer
  - Strip flagged lines from all pages
- Page number patterns to detect:
  - `Page X of Y`
  - `- X -`
  - Standalone numbers at page boundaries
  - `X | Chapter Title` or `Chapter Title | X`
- Consider `pdfplumber` as fallback for complex multi-column layouts
- Output format: List of `PageText` objects with page number and cleaned text

---

## Dev Agent Record

### Context Reference
- [PRD FR2](../prd.md): System can identify and remove page headers, footers, and page numbers
- [PRD FR3](../prd.md): System can extract raw text while preserving paragraph structure
- [Architecture](../architecture.md): Ingestion Agent responsibilities

### Debug Log
- 

### Completion Notes
- 

---

## File List

### Created
- 

### Modified
- 

---

## Change Log

| Date | Change |
|:-----|:-------|
| 2025-12-31 | Story file created from sprint-2.md |
