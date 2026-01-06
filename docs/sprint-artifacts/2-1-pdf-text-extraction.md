# Story 2.1: PDF Text Extraction Service

**Status:** Done  
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

- [x] **AC1:** Given a valid PDF file path, the Ingestion Agent can process it
- [x] **AC2:** Paragraph structure is preserved in extracted text
- [x] **AC3:** Page numbers are stripped (heuristic: "Page X of Y", "- X -")
- [x] **AC4:** Repeated headers/footers are detected and removed
- [x] **AC5:** Text stream is returned for downstream processing

---

## Tasks/Subtasks

- [x] **2.1.1** Add `pypdf` to ingestion-agent requirements
- [x] **2.1.2** Create `pdf_extractor.py` module in `agents/ingestion-agent/src/`
- [x] **2.1.3** Implement raw text extraction with page iteration
- [x] **2.1.4** Implement header/footer detection heuristics
- [x] **2.1.5** Implement page number removal regex patterns
- [x] **2.1.6** Add unit tests with sample PDF files
- [x] **2.1.7** Integrate extractor into agent main flow

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
- 2026-01-01: Implemented PDFExtractor class with pypdf for text extraction
- 2026-01-01: Added 10 page number regex patterns (Page X of Y, - X -, standalone, etc.)
- 2026-01-01: Header/footer detection uses 70% threshold across first/last 3 lines per page
- 2026-01-01: All 39 unit tests passing in container

### Completion Notes
- PDFExtractor class provides complete text extraction with cleaning
- ExtractionResult dataclass returns pages, detected headers/footers, and full_text stream
- Integrated into main.py via process_pdf() function
- Paragraph structure preserved by maintaining double-newlines between paragraphs

---

## File List

### Created
- agents/ingestion-agent/src/pdf_extractor.py
- agents/ingestion-agent/tests/test_pdf_extractor.py

### Modified
- agents/ingestion-agent/requirements.txt (added pypdf>=4.0.0)
- agents/ingestion-agent/src/main.py (added process_pdf integration)

---

## Change Log

| Date | Change |
|:-----|:-------|
| 2025-12-31 | Story file created from sprint-2.md |
| 2026-01-01 | All tasks completed, 39 tests passing, ready for review |
| 2026-01-01 | Senior Developer Review: APPROVED |

---

## Senior Developer Review (AI)

**Reviewer:** Jean  
**Date:** 2026-01-01  
**Outcome:** ✅ APPROVE

All acceptance criteria implemented with evidence. All tasks verified complete. Code follows architecture standards.

### Acceptance Criteria Coverage

| AC | Description | Status | Evidence |
|:---|:------------|:-------|:---------|
| AC1 | Given valid PDF path, agent can process it | ✅ IMPLEMENTED | pdf_extractor.py#L88-L112 - `extract()` validates path |
| AC2 | Paragraph structure preserved | ✅ IMPLEMENTED | pdf_extractor.py#L278-L282 - preserves `\n\n` |
| AC3 | Page numbers stripped | ✅ IMPLEMENTED | pdf_extractor.py#L62-L75 - 10 regex patterns |
| AC4 | Repeated headers/footers detected/removed | ✅ IMPLEMENTED | pdf_extractor.py#L131-L186 - 70% threshold |
| AC5 | Text stream returned for downstream | ✅ IMPLEMENTED | pdf_extractor.py#L42-L47 - `full_text` property |

**Summary:** 5 of 5 acceptance criteria fully implemented

### Task Completion Validation

| Task | Description | Verified | Evidence |
|:-----|:------------|:---------|:---------|
| 2.1.1 | Add pypdf to requirements | ✅ | requirements.txt#L8 |
| 2.1.2 | Create pdf_extractor.py module | ✅ | 309 lines |
| 2.1.3 | Raw text extraction with page iteration | ✅ | `_extract_raw_pages()` |
| 2.1.4 | Header/footer detection heuristics | ✅ | frequency-based, 70% threshold |
| 2.1.5 | Page number removal regex | ✅ | 10 patterns |
| 2.1.6 | Unit tests with sample PDFs | ✅ | 39 tests, all passing |
| 2.1.7 | Integrate into agent main flow | ✅ | `process_pdf()` in main.py |

**Summary:** 7 of 7 tasks verified, 0 false completions

### Test Coverage

- 39 tests passing
- Covers: dataclasses, page number patterns (17 parametrized), header/footer detection, page cleaning, error handling, edge cases
- Uses mocks for PdfReader, good test isolation

### Architectural Alignment

- ✅ Python 3.12 (Docker container)
- ✅ JSON structured logging
- ✅ Correct project structure (`agents/ingestion-agent/src/`)
- ✅ pypdf (modern fork per Dev Notes)

### Action Items

**Code Changes Required:**
- None

**Advisory Notes:**
- Note: Consider pdfplumber fallback for multi-column layouts (future iteration)
- Note: Header/footer threshold could be configurable (future iteration)
