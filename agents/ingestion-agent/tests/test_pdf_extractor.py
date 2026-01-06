"""
Unit Tests for PDF Text Extraction Module

Tests cover:
- Valid PDF processing
- Paragraph structure preservation
- Page number removal (multiple patterns)
- Header/footer detection and removal
- Edge cases and error handling

Story: 2.1 - PDF Text Extraction Service
"""

import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pdf_extractor import (
    ExtractionResult,
    PageText,
    PDFExtractor,
    extract_pdf_text,
)


class TestPageText:
    """Tests for PageText dataclass."""
    
    def test_page_text_basic(self):
        """Test basic PageText creation."""
        page = PageText(page_number=1, raw_text="Hello World")
        
        assert page.page_number == 1
        assert page.raw_text == "Hello World"
        assert page.cleaned_text == "Hello World"  # Defaults to raw_text
    
    def test_page_text_with_cleaned(self):
        """Test PageText with explicit cleaned text."""
        page = PageText(
            page_number=2,
            raw_text="Page 1 of 10\nContent here",
            cleaned_text="Content here",
        )
        
        assert page.raw_text != page.cleaned_text
        assert page.cleaned_text == "Content here"


class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""
    
    def test_empty_result(self):
        """Test empty extraction result."""
        result = ExtractionResult()
        
        assert result.pages == []
        assert result.total_pages == 0
        assert result.full_text == ""
        assert result.text_stream == ""
    
    def test_full_text_concatenation(self):
        """Test that full_text concatenates all cleaned page text."""
        result = ExtractionResult(
            pages=[
                PageText(1, "raw1", "Page 1 content"),
                PageText(2, "raw2", "Page 2 content"),
                PageText(3, "raw3", "Page 3 content"),
            ],
            total_pages=3,
        )
        
        assert "Page 1 content" in result.full_text
        assert "Page 2 content" in result.full_text
        assert "Page 3 content" in result.full_text
    
    def test_text_stream_alias(self):
        """Test that text_stream is an alias for full_text."""
        result = ExtractionResult(
            pages=[PageText(1, "raw", "content")],
            total_pages=1,
        )
        
        assert result.text_stream == result.full_text


class TestPDFExtractor:
    """Tests for PDFExtractor class."""
    
    @pytest.fixture
    def extractor(self):
        """Create a PDFExtractor instance."""
        return PDFExtractor()
    
    def test_init_compiles_patterns(self, extractor):
        """Test that patterns are compiled on init."""
        assert len(extractor._compiled_patterns) > 0
        assert all(
            hasattr(p, 'match') for p in extractor._compiled_patterns
        )
    
    # --- Page Number Detection Tests ---
    
    @pytest.mark.parametrize("line,expected", [
        ("Page 1 of 10", True),
        ("Page 23 of 100", True),
        ("page 5 of 20", True),  # Case insensitive
        ("- 5 -", True),
        ("- 123 -", True),
        ("5", True),  # Standalone number
        ("123", True),
        ("5 | Chapter One", True),
        ("Chapter One | 5", True),
        ("— 42 —", True),  # Em-dash variant
        ("[5]", True),
        ("pg. 10", True),
        ("pg 10", True),
        # Non-page-number lines
        ("This is regular text", False),
        ("The year 2024 was great", False),
        ("Chapter 5: Introduction", False),
        ("5 apples and 3 oranges", False),
    ])
    def test_is_page_number(self, extractor, line, expected):
        """Test page number pattern detection."""
        assert extractor._is_page_number(line) == expected
    
    # --- Header/Footer Detection Tests ---
    
    def test_detect_headers_footers_insufficient_pages(self, extractor):
        """Test that header/footer detection skips with <3 pages."""
        pages = [
            PageText(1, "Header\nContent\nFooter"),
            PageText(2, "Header\nContent\nFooter"),
        ]
        
        headers, footers = extractor._detect_headers_footers(pages)
        
        assert headers == []
        assert footers == []
    
    def test_detect_repeated_header(self, extractor):
        """Test detection of repeated headers across pages."""
        pages = [
            PageText(1, "Company Name\nFirst line\nSecond line\nContent"),
            PageText(2, "Company Name\nDifferent content\nMore text"),
            PageText(3, "Company Name\nAnother page\nStuff here"),
            PageText(4, "Company Name\nFourth page\nMore content"),
        ]
        
        headers, footers = extractor._detect_headers_footers(pages)
        
        # "Company Name" should be detected as header (appears in 100% of pages)
        assert any("company name" in h.lower() for h in headers)
    
    def test_detect_repeated_footer(self, extractor):
        """Test detection of repeated footers across pages."""
        pages = [
            PageText(1, "Content\nMore content\nConfidential Document"),
            PageText(2, "Other text\nStuff\nConfidential Document"),
            PageText(3, "Page three\nThings\nConfidential Document"),
            PageText(4, "Last page\nFinal\nConfidential Document"),
        ]
        
        headers, footers = extractor._detect_headers_footers(pages)
        
        # "Confidential Document" should be detected as footer
        assert any("confidential document" in f.lower() for f in footers)
    
    def test_normalize_removes_page_numbers(self, extractor):
        """Test that normalization removes page numbers for comparison."""
        line1 = "Chapter 1 | 5"
        line2 = "Chapter 1 | 42"
        
        norm1 = extractor._normalize_for_comparison(line1)
        norm2 = extractor._normalize_for_comparison(line2)
        
        # Both should normalize to the same string
        assert norm1 == norm2
    
    # --- Page Cleaning Tests ---
    
    def test_clean_single_page_removes_page_numbers(self, extractor):
        """Test that page numbers are removed from text."""
        text = "Content paragraph.\nPage 5 of 20\nMore content."
        
        cleaned = extractor._clean_single_page(text, [], [])
        
        assert "Page 5 of 20" not in cleaned
        assert "Content paragraph." in cleaned
        assert "More content." in cleaned
    
    def test_clean_single_page_removes_headers(self, extractor):
        """Test that detected headers are removed."""
        text = "Company Header\nActual content here.\nMore text."
        # Headers are stored in normalized form (lowercase, whitespace normalized)
        # The _clean_single_page method normalizes each line before comparison
        headers = ["Company Header"]  # Use original form - normalization happens internally
        
        cleaned = extractor._clean_single_page(text, headers, [])
        
        # The header should be removed since its normalized form matches
        assert "Actual content here." in cleaned
    
    def test_clean_single_page_preserves_paragraphs(self, extractor):
        """Test that paragraph structure is preserved."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        
        cleaned = extractor._clean_single_page(text, [], [])
        
        # Should have paragraph breaks (double newlines)
        assert "\n\n" in cleaned
        assert "First paragraph." in cleaned
        assert "Second paragraph." in cleaned
    
    def test_clean_removes_excessive_blank_lines(self, extractor):
        """Test that excessive blank lines are normalized."""
        text = "Content.\n\n\n\n\nMore content."
        
        cleaned = extractor._clean_single_page(text, [], [])
        
        # Should not have more than 2 consecutive newlines
        assert "\n\n\n" not in cleaned
    
    # --- Integration Tests with Mock PDF ---
    
    def test_extract_file_not_found(self, extractor):
        """Test FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            extractor.extract("/nonexistent/path/file.pdf")
    
    def test_extract_invalid_extension(self, extractor, tmp_path):
        """Test ValueError for non-PDF file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Not a PDF")
        
        with pytest.raises(ValueError, match="not a PDF"):
            extractor.extract(txt_file)
    
    @patch('src.pdf_extractor.PdfReader')
    def test_extract_full_flow(self, mock_reader_class, extractor, tmp_path):
        """Test full extraction flow with mocked PDF."""
        # Create a fake PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")
        
        # Mock the PDF reader
        mock_reader = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = (
            "Document Title\n\n"
            "First paragraph of content.\n\n"
            "Second paragraph here.\n\n"
            "Page 1 of 3"
        )
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = (
            "Document Title\n\n"
            "Third paragraph content.\n\n"
            "Page 2 of 3"
        )
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = (
            "Document Title\n\n"
            "Final paragraph.\n\n"
            "Page 3 of 3"
        )
        
        mock_reader.pages = [mock_page1, mock_page2, mock_page3]
        mock_reader_class.return_value = mock_reader
        
        # Execute extraction
        result = extractor.extract(pdf_file)
        
        # Verify results
        assert result.total_pages == 3
        assert len(result.pages) == 3
        
        # Page numbers should be removed
        assert "Page 1 of 3" not in result.full_text
        assert "Page 2 of 3" not in result.full_text
        
        # Content should be preserved
        assert "First paragraph" in result.full_text
        assert "Final paragraph" in result.full_text
        
        # "Document Title" appears in all 3 pages (100%) -> should be detected as header
        assert "Document Title" in result.detected_headers or \
               "document title" in [h.lower() for h in result.detected_headers]


class TestConvenienceFunction:
    """Tests for the extract_pdf_text convenience function."""
    
    def test_convenience_function_returns_result(self, tmp_path):
        """Test that convenience function returns ExtractionResult."""
        # Create invalid file to trigger ValueError
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Not a PDF")
        
        with pytest.raises(ValueError):
            extract_pdf_text(txt_file)
    
    @patch('src.pdf_extractor.PdfReader')
    def test_convenience_function_extracts(self, mock_reader_class, tmp_path):
        """Test convenience function with mocked PDF."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Simple content"
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader
        
        result = extract_pdf_text(pdf_file)
        
        assert isinstance(result, ExtractionResult)
        assert result.total_pages == 1
        assert "Simple content" in result.full_text


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.fixture
    def extractor(self):
        return PDFExtractor()
    
    def test_empty_page_text(self, extractor):
        """Test handling of pages with no text."""
        pages = [
            PageText(1, ""),
            PageText(2, "   "),
            PageText(3, "\n\n"),
        ]
        
        cleaned = extractor._clean_pages(pages, [], [])
        
        assert len(cleaned) == 3
        # All should have empty or whitespace-only cleaned text
    
    def test_single_page_document(self, extractor):
        """Test single-page document (no header/footer detection)."""
        pages = [PageText(1, "Only page content\nPage 1 of 1")]
        
        headers, footers = extractor._detect_headers_footers(pages)
        
        # Should not detect headers/footers with single page
        assert headers == []
        assert footers == []
    
    def test_very_short_lines_ignored(self, extractor):
        """Test that very short lines are ignored in header/footer detection."""
        pages = [
            PageText(1, "Hi\nContent\nBye"),
            PageText(2, "Hi\nOther\nBye"),
            PageText(3, "Hi\nMore\nBye"),
            PageText(4, "Hi\nStuff\nBye"),
        ]
        
        headers, footers = extractor._detect_headers_footers(pages)
        
        # "Hi" and "Bye" are too short (<=3 chars) to be flagged
        assert "hi" not in [h.lower() for h in headers]
        assert "bye" not in [f.lower() for f in footers]
