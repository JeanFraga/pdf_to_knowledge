# Story 3.1: Global Context Generation

**Status:** Ready for Dev  
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

- [ ] **AC1:** Given the full extracted text, a 1-2 page summary is produced
- [ ] **AC2:** Summary captures key themes, terminology, and document purpose
- [ ] **AC3:** Key terms and definitions are identified and listed
- [ ] **AC4:** Global context is stored for injection into local chunks
- [ ] **AC5:** Processing handles documents up to 500 pages (large context window)

---

## Tasks/Subtasks

- [ ] **3.1.1** Create `context_generator.py` module in `agents/ingestion-agent/src/`
- [ ] **3.1.2** Design global context prompt template
- [ ] **3.1.3** Implement Gemini 2.5 Flash call with large context
- [ ] **3.1.4** Implement key term extraction from summary
- [ ] **3.1.5** Define `GlobalContext` output schema (Pydantic)
- [ ] **3.1.6** Add unit tests with mock Gemini responses
- [ ] **3.1.7** Integrate into ingestion pipeline after text extraction

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
