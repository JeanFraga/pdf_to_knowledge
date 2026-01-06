"""
PDF Text Extraction Module

Extracts text from PDF files while:
- Preserving paragraph structure
- Removing page numbers
- Detecting and removing repeated headers/footers

Story: 2.1 - PDF Text Extraction Service
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pypdf import PdfReader


@dataclass
class PageText:
    """Represents extracted text from a single page."""
    
    page_number: int  # 1-indexed
    raw_text: str
    cleaned_text: str = ""
    
    def __post_init__(self):
        if not self.cleaned_text:
            self.cleaned_text = self.raw_text


@dataclass
class ExtractionResult:
    """Result of PDF text extraction."""
    
    pages: list[PageText] = field(default_factory=list)
    total_pages: int = 0
    detected_headers: list[str] = field(default_factory=list)
    detected_footers: list[str] = field(default_factory=list)
    source_file: str = ""
    
    @property
    def full_text(self) -> str:
        """Return all cleaned text concatenated."""
        return "\n\n".join(page.cleaned_text for page in self.pages if page.cleaned_text.strip())
    
    @property
    def text_stream(self) -> str:
        """Alias for full_text - returns cleaned text for downstream processing."""
        return self.full_text


class PDFExtractor:
    """
    Extracts and cleans text from PDF documents.
    
    Features:
    - Raw text extraction with page iteration
    - Header/footer detection and removal (>70% repetition threshold)
    - Page number pattern removal
    - Paragraph structure preservation
    """
    
    # Page number patterns to detect and remove
    PAGE_NUMBER_PATTERNS = [
        r"^Page\s+\d+\s+of\s+\d+\s*$",           # Page X of Y
        r"^-\s*\d+\s*-\s*$",                      # - X -
        r"^\d+\s*$",                               # Standalone number
        r"^\d+\s*\|\s*.+$",                        # X | Chapter Title
        r"^.+\s*\|\s*\d+\s*$",                     # Chapter Title | X
        r"^—\s*\d+\s*—\s*$",                       # — X — (em-dash variant)
        r"^\[\s*\d+\s*\]\s*$",                     # [X]
        r"^pg\.?\s*\d+\s*$",                       # pg. X or pg X
    ]
    
    # Compiled patterns for efficiency
    _compiled_patterns: list[re.Pattern] = []
    
    # Header/footer detection settings
    HEADER_LINES_TO_CHECK = 3  # Check first N lines of each page
    FOOTER_LINES_TO_CHECK = 3  # Check last N lines of each page
    REPETITION_THRESHOLD = 0.70  # 70% threshold for header/footer detection
    
    def __init__(self):
        """Initialize the PDF extractor."""
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.PAGE_NUMBER_PATTERNS
        ]
    
    def extract(self, pdf_path: str | Path) -> ExtractionResult:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractionResult containing cleaned text and metadata
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If file is not a valid PDF
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_path.suffix.lower() == ".pdf":
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        # Step 1: Extract raw text from all pages
        reader = PdfReader(str(pdf_path))
        pages = self._extract_raw_pages(reader)
        
        # Step 2: Detect repeated headers and footers
        headers, footers = self._detect_headers_footers(pages)
        
        # Step 3: Clean each page (remove headers, footers, page numbers)
        cleaned_pages = self._clean_pages(pages, headers, footers)
        
        return ExtractionResult(
            pages=cleaned_pages,
            total_pages=len(cleaned_pages),
            detected_headers=headers,
            detected_footers=footers,
            source_file=str(pdf_path),
        )
    
    def _extract_raw_pages(self, reader: PdfReader) -> list[PageText]:
        """Extract raw text from each page."""
        pages = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            raw_text = page.extract_text() or ""
            pages.append(PageText(
                page_number=page_num,
                raw_text=raw_text,
            ))
        
        return pages
    
    def _detect_headers_footers(
        self, pages: list[PageText]
    ) -> tuple[list[str], list[str]]:
        """
        Detect repeated headers and footers across pages.
        
        Uses a frequency-based approach:
        - Track first N and last N lines of each page
        - If a line appears in >70% of pages, flag as header/footer
        
        Args:
            pages: List of PageText objects with raw text
            
        Returns:
            Tuple of (detected_headers, detected_footers)
        """
        if len(pages) < 3:
            # Not enough pages to reliably detect headers/footers
            return [], []
        
        header_candidates: Counter[str] = Counter()
        footer_candidates: Counter[str] = Counter()
        
        for page in pages:
            lines = page.raw_text.split("\n")
            lines = [line.strip() for line in lines if line.strip()]
            
            if not lines:
                continue
            
            # Check header lines (first N lines)
            for line in lines[:self.HEADER_LINES_TO_CHECK]:
                normalized = self._normalize_for_comparison(line)
                if normalized and len(normalized) > 3:  # Skip very short lines
                    header_candidates[normalized] += 1
            
            # Check footer lines (last N lines)
            for line in lines[-self.FOOTER_LINES_TO_CHECK:]:
                normalized = self._normalize_for_comparison(line)
                if normalized and len(normalized) > 3:
                    footer_candidates[normalized] += 1
        
        total_pages = len(pages)
        threshold = int(total_pages * self.REPETITION_THRESHOLD)
        
        detected_headers = [
            line for line, count in header_candidates.items()
            if count >= threshold
        ]
        
        detected_footers = [
            line for line, count in footer_candidates.items()
            if count >= threshold
        ]
        
        return detected_headers, detected_footers
    
    def _normalize_for_comparison(self, line: str) -> str:
        """
        Normalize a line for header/footer comparison.
        
        Removes page numbers and normalizes whitespace so that
        "Chapter 1 - Introduction  |  5" matches "Chapter 1 - Introduction  |  12"
        """
        # Remove standalone numbers (likely page numbers)
        normalized = re.sub(r"\b\d+\b", "", line)
        # Normalize whitespace
        normalized = " ".join(normalized.split())
        return normalized.strip()
    
    def _clean_pages(
        self,
        pages: list[PageText],
        headers: list[str],
        footers: list[str],
    ) -> list[PageText]:
        """
        Clean pages by removing headers, footers, and page numbers.
        
        Args:
            pages: List of PageText objects
            headers: Detected header patterns to remove
            footers: Detected footer patterns to remove
            
        Returns:
            List of PageText objects with cleaned_text populated
        """
        cleaned_pages = []
        
        for page in pages:
            cleaned_text = self._clean_single_page(
                page.raw_text,
                headers,
                footers,
            )
            
            cleaned_pages.append(PageText(
                page_number=page.page_number,
                raw_text=page.raw_text,
                cleaned_text=cleaned_text,
            ))
        
        return cleaned_pages
    
    def _clean_single_page(
        self,
        text: str,
        headers: list[str],
        footers: list[str],
    ) -> str:
        """Clean a single page's text."""
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines (preserve paragraph breaks)
            if not stripped:
                cleaned_lines.append("")
                continue
            
            # Check if line matches a page number pattern
            if self._is_page_number(stripped):
                continue
            
            # Check if line matches detected header
            normalized = self._normalize_for_comparison(stripped)
            if normalized in headers:
                continue
            
            # Check if line matches detected footer
            if normalized in footers:
                continue
            
            cleaned_lines.append(line)
        
        # Clean up excessive blank lines while preserving paragraph structure
        cleaned_text = "\n".join(cleaned_lines)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
        
        return cleaned_text.strip()
    
    def _is_page_number(self, line: str) -> bool:
        """Check if a line is a page number pattern."""
        for pattern in self._compiled_patterns:
            if pattern.match(line):
                return True
        return False


def extract_pdf_text(pdf_path: str | Path) -> ExtractionResult:
    """
    Convenience function to extract text from a PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        ExtractionResult containing cleaned text and metadata
    """
    extractor = PDFExtractor()
    return extractor.extract(pdf_path)
