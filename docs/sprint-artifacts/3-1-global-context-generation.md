# Story 3.1: Global Context Generation

**Status:** Done  
**Sprint:** 2  
**Epic:** Agentic Chunking & Context  
**Estimate:** 2-3 days  

---

## Story

**As a** User,  
**I want** the system to generate a "Global Context" summary of the entire document,  
**So that** individual chunks can be understood in relation to the whole.

---

## Acceptance Criteria

- [x] **AC1:** Given the full extracted text, a 1-2 page summary is produced
- [x] **AC2:** Summary captures key themes, terminology, and document purpose
- [x] **AC3:** Key terms and definitions are identified and listed
- [x] **AC4:** Global context is stored for injection into local chunks
- [x] **AC5:** Processing handles documents up to 500 pages (large context window)

---

## Tasks/Subtasks

- [x] **3.1.1** Create `context_generator.py` module in `agents/ingestion-agent/src/`
- [x] **3.1.2** Design global context prompt template
- [x] **3.1.3** Implement Gemini 2.5 Flash call with large context
- [x] **3.1.4** Implement key term extraction from summary
- [x] **3.1.5** Define `GlobalContext` output schema (Pydantic)
- [x] **3.1.6** Add unit tests with mock Gemini responses
- [x] **3.1.7** Integrate into ingestion pipeline after text extraction

---

## Dev Notes

- Model: `gemini-2.5-flash` for large context window (1M tokens)
- Prompt template:
  ```
  You are analyzing a technical document to create a global context summary.
  
  Your task:
  1. Summarize the document in 1-2 pages, focusing on main themes and purpose
  2. Identify key terminology and provide brief definitions
  3. Note the document type (textbook, manual, research paper, etc.)
  4. Highlight any recurring concepts that appear across multiple sections
  
  This summary will be used to provide context to isolated chunks extracted 
  from this document, helping readers understand each chunk in relation to 
  the whole.
  
  Document text:
  {full_text}
  ```
- Output Pydantic model:
  ```python
  class KeyTerm(BaseModel):
      term: str
      definition: str
      frequency: Optional[int] = None  # How often it appears
  
  class GlobalContext(BaseModel):
      summary: str                    # 1-2 page summary
      document_type: str              # textbook, manual, paper, etc.
      key_terms: List[KeyTerm]        # Extracted terminology
      main_themes: List[str]          # 3-5 main themes
      target_audience: Optional[str]  # Inferred audience
      generated_at: datetime
  ```
- Token estimation: ~750 tokens per page, 500 pages = ~375K tokens (well within 1M limit)
- Add retry logic for API rate limits
- Consider chunked summarization for documents exceeding context window

---

## Dev Agent Record

### Context Reference
- [PRD FR6](../prd.md): System can generate a "Global Context" summary for the document
- [PRD FR15](../prd.md): System can handle documents up to 500 pages in length
- [Epic 3](../epics.md): Agentic Chunking & Context
- [Story 2.1](./2-1-pdf-text-extraction.md): Depends on extracted text

### Debug Log
- 2026-01-01: Implemented ContextGenerator class using google-genai SDK
- 2026-01-01: GlobalContext Pydantic model with summary, document_type, key_terms, main_themes
- 2026-01-01: KeyTerm model with term, definition, and optional frequency
- 2026-01-01: JSON prompt template for structured output from Gemini
- 2026-01-01: Retry logic (3 attempts) for API resilience
- 2026-01-01: All 28 context generator tests passing

### Completion Notes
- ContextGenerator class calls Gemini with structured JSON prompt
- Uses gemini-2.0-flash by default (configurable via CONTEXT_GENERATOR_MODEL env var)
- Token estimation: ~4 chars per token, supports 500+ page documents
- process_pdf_full() in main.py combines text + images + global context generation
- Context generation gracefully handles failures (logs warning, continues pipeline)
- Total 93 tests passing (39 PDF + 26 Image + 28 Context)

---

## File List

### Created
- agents/ingestion-agent/src/context_generator.py
- agents/ingestion-agent/tests/test_context_generator.py

### Modified
- agents/ingestion-agent/src/main.py (added process_pdf_full integration)

---

## Change Log

| Date | Change |
|:-----|:-------|
| 2025-12-31 | Story file created from sprint-2.md |
| 2026-01-01 | All tasks completed, 93 tests passing, ready for review |
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
| AC1 | 1-2 page summary produced | ✅ IMPLEMENTED | context_generator.py#L89-L104 - GLOBAL_CONTEXT_PROMPT, GlobalContext.summary |
| AC2 | Key themes/terminology/purpose captured | ✅ IMPLEMENTED | GlobalContext model: summary, document_type, main_themes |
| AC3 | Key terms identified and listed | ✅ IMPLEMENTED | context_generator.py#L23-L41 - KeyTerm model with term/definition |
| AC4 | Context stored for injection | ✅ IMPLEMENTED | GlobalContext Pydantic model, returned by process_pdf_full() |
| AC5 | Handles 500 pages (large context) | ✅ IMPLEMENTED | Uses gemini-2.0-flash (1M tokens), token estimation ~4 chars/token |

**Summary:** 5 of 5 acceptance criteria fully implemented

### Task Completion Validation

| Task | Description | Verified | Evidence |
|:-----|:------------|:---------|:---------|
| 3.1.1 | Create context_generator.py | ✅ | 326 lines |
| 3.1.2 | Design prompt template | ✅ | GLOBAL_CONTEXT_PROMPT constant |
| 3.1.3 | Implement Gemini call | ✅ | `_call_gemini()` with retry logic |
| 3.1.4 | Key term extraction | ✅ | `_parse_response()` extracts key_terms |
| 3.1.5 | GlobalContext schema | ✅ | Pydantic models with Field validators |
| 3.1.6 | Unit tests with mocks | ✅ | 28 tests, all passing |
| 3.1.7 | Integrate into pipeline | ✅ | `process_pdf_full()` in main.py |

**Summary:** 7 of 7 tasks verified, 0 false completions

### Test Coverage

- 28 tests passing
- Covers: KeyTerm/GlobalContext models, API key handling, token estimation, retry logic, JSON parsing, error handling
- Good mocking of genai.Client

### Architectural Alignment

- ✅ google-genai SDK (per architecture)
- ✅ Pydantic models with Field validators
- ✅ JSON structured logging
- ✅ Graceful error handling (pipeline continues if context fails)

### Action Items

**Code Changes Required:**
- None

**Advisory Notes:**
- Note: Dev Notes mention gemini-2.5-flash but implementation uses 2.0-flash (acceptable - both have large context)
- Note: Consider adding chunked summarization for extremely large documents in future
