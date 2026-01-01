# Story 2.2: Image Region Extraction

**Status:** Ready for Dev  
**Sprint:** 2  
**Epic:** PDF Ingestion & Parsing  
**Estimate:** 2-3 days  

---

## Story

**As a** User,  
**I want** the system to identify and extract charts and diagrams as separate image files,  
**So that** they can be described by the vision model later.

---

## Acceptance Criteria

- [ ] **AC1:** Given a PDF with embedded images, images are extracted to temp directory
- [ ] **AC2:** Small artifacts (< 100x100px) are filtered out
- [ ] **AC3:** Image locations in text are replaced with `[IMAGE: <id>]` placeholders
- [ ] **AC4:** Image metadata (page, position, size) is captured
- [ ] **AC5:** Extracted images are accessible for downstream visual processing

---

## Tasks/Subtasks

- [ ] **2.2.1** Add `Pillow` to ingestion-agent requirements
- [ ] **2.2.2** Create `image_extractor.py` module in `agents/ingestion-agent/src/`
- [ ] **2.2.3** Implement PDF image object extraction via `/XObject` resources
- [ ] **2.2.4** Implement size filtering (min 100x100px)
- [ ] **2.2.5** Implement placeholder injection in text stream
- [ ] **2.2.6** Create image metadata schema (page, bbox, dimensions)
- [ ] **2.2.7** Add unit tests with image-containing PDFs
- [ ] **2.2.8** Integrate with text extraction flow from Story 2.1

---

## Dev Notes

- `pypdf` can extract images via `/XObject` resources on each page
- Image extraction approach:
  ```python
  for page in reader.pages:
      if '/XObject' in page['/Resources']:
          xobjects = page['/Resources']['/XObject'].get_object()
          for obj_name in xobjects:
              obj = xobjects[obj_name]
              if obj['/Subtype'] == '/Image':
                  # Extract image data
  ```
- Storage location: `/tmp/p2k-images/<job_id>/` (configurable via env)
- Placeholder format: `[IMAGE: img_001]` with sequential ID per document
- Image metadata Pydantic model:
  ```python
  class ImageMetadata(BaseModel):
      id: str           # img_001
      page: int         # 1-indexed
      width: int        # pixels
      height: int       # pixels
      format: str       # PNG, JPEG
      file_path: str    # /tmp/p2k-images/<job_id>/img_001.png
  ```
- Filter threshold: 100x100px minimum (catches icons, bullets, decorative elements)
- Consider detecting image position relative to text for better placeholder insertion

---

## Dev Agent Record

### Context Reference
- [PRD FR4](../prd.md): System can identify and extract image regions (charts, diagrams)
- [Epic 2](../epics.md): PDF Ingestion & Parsing
- [Story 2.1](./2-1-pdf-text-extraction.md): Depends on text extraction module

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
