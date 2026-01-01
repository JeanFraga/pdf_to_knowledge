# Sprint 2: PDF Ingestion & Global Context

**Sprint Duration:** 2 weeks  
**Start Date:** 2025-01-16  
**End Date:** 2025-01-29  
**Developer:** Jean (Solo)

---

## Sprint Goal

> Enable the Ingestion Agent to extract text and images from PDFs and generate a global context summary for the document.

---

## Sprint Backlog

| ID | Story | Status | Est. Days | Actual |
|:---|:------|:-------|:----------|:-------|
| 2.1 | PDF Text Extraction Service | 🔲 Not Started | 2-3 | — |
| 2.2 | Image Region Extraction | 🔲 Not Started | 2-3 | — |
| 3.1 | Global Context Generation | 🔲 Not Started | 2-3 | — |

**Status Legend:** 🔲 Not Started | 🔄 In Progress | ✅ Done | ⛔ Blocked

---

## Story Details

### Story 2.1: PDF Text Extraction Service

**As a** User,  
**I want** the system to extract raw text from a PDF file,  
**So that** the content can be processed by the chunking engine.

#### Acceptance Criteria
- [ ] Given a valid PDF file path, the Ingestion Agent can process it
- [ ] Paragraph structure is preserved in extracted text
- [ ] Page numbers are stripped (heuristic: "Page X of Y", "- X -")
- [ ] Repeated headers/footers are detected and removed
- [ ] Text stream is returned for downstream processing

#### Tasks
- [ ] **2.1.1** Add `pypdf` or `pdfminer.six` to ingestion-agent requirements
- [ ] **2.1.2** Create `pdf_extractor.py` module in ingestion-agent
- [ ] **2.1.3** Implement raw text extraction with page iteration
- [ ] **2.1.4** Implement header/footer detection heuristics
- [ ] **2.1.5** Implement page number removal regex patterns
- [ ] **2.1.6** Add unit tests with sample PDF files
- [ ] **2.1.7** Integrate extractor into agent main flow

#### Technical Notes
- Use `pypdf` (modern fork of PyPDF2) for better maintenance
- Header/footer detection: track first/last 3 lines per page, flag if >70% repeat
- Consider `pdfplumber` as fallback for complex layouts

---

### Story 2.2: Image Region Extraction

**As a** User,  
**I want** the system to identify and extract charts and diagrams as separate image files,  
**So that** they can be described by the vision model later.

#### Acceptance Criteria
- [ ] Given a PDF with embedded images, images are extracted to temp directory
- [ ] Small artifacts (< 100x100px) are filtered out
- [ ] Image locations in text are replaced with `[IMAGE: <id>]` placeholders
- [ ] Image metadata (page, position, size) is captured
- [ ] Extracted images are accessible for downstream visual processing

#### Tasks
- [ ] **2.2.1** Add `Pillow` to ingestion-agent requirements
- [ ] **2.2.2** Create `image_extractor.py` module in ingestion-agent
- [ ] **2.2.3** Implement PDF image object extraction
- [ ] **2.2.4** Implement size filtering (min 100x100px)
- [ ] **2.2.5** Implement placeholder injection in text stream
- [ ] **2.2.6** Create image metadata schema (page, bbox, dimensions)
- [ ] **2.2.7** Add unit tests with image-containing PDFs
- [ ] **2.2.8** Integrate with text extraction flow

#### Technical Notes
- `pypdf` can extract images via `/XObject` resources
- Store images as PNG in `/tmp/p2k-images/<job_id>/`
- Placeholder format: `[IMAGE: img_001]` with UUID or sequential ID

---

### Story 3.1: Global Context Generation

**As a** User,  
**I want** the system to generate a "Global Context" summary of the entire document,  
**So that** individual chunks can be understood in relation to the whole.

#### Acceptance Criteria
- [ ] Given the full extracted text, a 1-2 page summary is produced
- [ ] Summary captures key themes, terminology, and document purpose
- [ ] Key terms and definitions are identified and listed
- [ ] Global context is stored for injection into local chunks
- [ ] Processing handles documents up to 500 pages (large context window)

#### Tasks
- [ ] **3.1.1** Create `context_generator.py` module in ingestion-agent
- [ ] **3.1.2** Design global context prompt template
- [ ] **3.1.3** Implement Gemini 2.5 Flash call with large context
- [ ] **3.1.4** Implement key term extraction from summary
- [ ] **3.1.5** Define global context output schema (Pydantic)
- [ ] **3.1.6** Add unit tests with mock Gemini responses
- [ ] **3.1.7** Integrate into ingestion pipeline after text extraction

#### Technical Notes
- Use `gemini-2.5-flash` for large context window (1M tokens)
- Prompt: "Summarize this document for the purpose of providing context to isolated chunks extracted from it. Include key terminology and definitions."
- Output: `GlobalContext` model with `summary`, `key_terms[]`, `document_type`

---

## Definition of Done (Sprint Level)

- [ ] All acceptance criteria for stories 2.1, 2.2, 3.1 met
- [ ] Ingestion Agent can process a sample PDF end-to-end
- [ ] Text extracted with headers/footers removed
- [ ] Images extracted and placeholders inserted
- [ ] Global context generated via Gemini
- [ ] Unit tests passing for all new modules
- [ ] Code committed and pushed to main branch

---

## Dependencies & Blockers

| Item | Type | Status | Notes |
|:-----|:-----|:-------|:------|
| Sprint 1 complete | Dependency | ✅ Done | Foundation in place |
| Sample PDF files | Dependency | 🔲 Needed | Need 2-3 test PDFs (text-only, with images, 100+ pages) |
| Gemini API quota | Dependency | ✅ Done | Verified in Sprint 1 |

---

## Daily Log

### Day 1 (2025-01-16)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

### Day 2 (2025-01-17)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

### Day 3 (2025-01-20)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

---

## Change Log

| Date | Change |
|:-----|:-------|
| 2025-12-31 | Sprint 2 planned, 3 stories scoped |
