"""
Integration Tests for PDF Processing Pipeline

Tests the full ingestion pipeline with real PDF files:
- PDF text extraction
- Image extraction  
- Global context generation

Story: Sprint 2 Integration Testing
"""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

# Path to fixtures folder
FIXTURES_DIR = Path(__file__).parent / "fixtures"
OUTPUT_DIR = Path(__file__).parent / "output"


def get_sample_pdf() -> Path | None:
    """Find a sample PDF in the fixtures directory."""
    if not FIXTURES_DIR.exists():
        return None
    
    for pdf_file in FIXTURES_DIR.glob("*.pdf"):
        return pdf_file
    
    return None


def save_extraction_results(results: dict, filename: str = "extraction_results.txt"):
    """Save extraction results to a text file for review."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / filename
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# PDF Extraction Results\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(f"{'=' * 80}\n\n")
        
        for section, content in results.items():
            f.write(f"## {section}\n")
            f.write(f"{'-' * 40}\n")
            if isinstance(content, dict):
                for key, value in content.items():
                    f.write(f"{key}: {value}\n")
            else:
                f.write(f"{content}\n")
            f.write(f"\n")
    
    return output_path


@pytest.fixture
def sample_pdf() -> Path:
    """Fixture that provides a sample PDF path, skipping if none available."""
    pdf_path = get_sample_pdf()
    if pdf_path is None:
        pytest.skip(
            "No PDF file found in tests/integration/fixtures/. "
            "Please add a sample PDF file to run integration tests."
        )
    return pdf_path


class TestPDFExtractionIntegration:
    """Integration tests for PDF text extraction."""
    
    def test_extract_text_from_real_pdf(self, sample_pdf: Path):
        """Test text extraction on a real PDF file."""
        from src.pdf_extractor import PDFExtractor
        
        extractor = PDFExtractor()
        result = extractor.extract(sample_pdf)
        
        # Basic assertions
        assert result.total_pages > 0, "PDF should have at least one page"
        assert len(result.full_text) > 100, "Should extract meaningful text"
        assert result.source_file == str(sample_pdf)
        
        # Save results to file for review
        results = {
            "Extraction Summary": {
                "Source": sample_pdf.name,
                "Total pages": result.total_pages,
                "Text length (chars)": len(result.full_text),
                "Detected headers": len(result.detected_headers),
                "Detected footers": len(result.detected_footers),
            },
            "Detected Headers": "\n".join(result.detected_headers) if result.detected_headers else "(none)",
            "Detected Footers": "\n".join(result.detected_footers) if result.detected_footers else "(none)",
            "Full Extracted Text": result.full_text,
        }
        
        output_path = save_extraction_results(results, "extracted_text.txt")
        
        # Log extraction stats for manual review
        print(f"\n--- PDF Extraction Results ---")
        print(f"Source: {sample_pdf.name}")
        print(f"Total pages: {result.total_pages}")
        print(f"Text length: {len(result.full_text)} chars")
        print(f"Detected headers: {len(result.detected_headers)}")
        print(f"Detected footers: {len(result.detected_footers)}")
        print(f"\n✅ Full results saved to: {output_path}")
    
    def test_paragraph_structure_preserved(self, sample_pdf: Path):
        """Test that paragraph breaks are preserved in extraction."""
        from src.pdf_extractor import PDFExtractor
        
        extractor = PDFExtractor()
        result = extractor.extract(sample_pdf)
        
        # Should have paragraph breaks (double newlines)
        assert "\n\n" in result.full_text, "Should preserve paragraph structure"


class TestImageExtractionIntegration:
    """Integration tests for image extraction."""
    
    def test_extract_images_from_real_pdf(self, sample_pdf: Path, tmp_path: Path):
        """Test image extraction on a real PDF file."""
        from src.image_extractor import ImageExtractor
        
        extractor = ImageExtractor(output_dir=str(tmp_path))
        result = extractor.extract(sample_pdf, job_id="integration_test")
        
        # Log extraction stats
        print(f"\n--- Image Extraction Results ---")
        print(f"Source: {sample_pdf.name}")
        print(f"Images extracted: {result.total_extracted}")
        print(f"Images filtered (too small): {result.total_filtered}")
        print(f"Output directory: {result.output_directory}")
        
        if result.images:
            print(f"Image details:")
            for img in result.images[:5]:  # Show first 5
                print(f"  - {img.id}: {img.width}x{img.height} {img.format} (page {img.page})")
        
        # Basic assertions
        assert result.source_file == str(sample_pdf)
        assert Path(result.output_directory).exists()
        
        # Verify extracted images exist on disk
        for img in result.images:
            assert Path(img.file_path).exists(), f"Image file should exist: {img.file_path}"


class TestFullPipelineIntegration:
    """Integration tests for the complete ingestion pipeline."""
    
    def test_process_pdf_text_and_images(self, sample_pdf: Path, tmp_path: Path):
        """Test combined text and image extraction."""
        from src.main import process_pdf_with_images
        
        text_result, image_result = process_pdf_with_images(
            sample_pdf,
            job_id="full_pipeline_test",
            image_output_dir=str(tmp_path),
        )
        
        # Text assertions
        assert text_result.total_pages > 0
        assert len(text_result.full_text) > 100
        
        # Image placeholders should be injected if images were found
        if image_result.images:
            assert "[IMAGE:" in text_result.full_text, "Image placeholders should be injected"
        
        print(f"\n--- Full Pipeline Results ---")
        print(f"Pages: {text_result.total_pages}")
        print(f"Text length: {len(text_result.full_text)} chars")
        print(f"Images: {image_result.total_extracted}")
    
    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"),
        reason="API key required for context generation"
    )
    def test_full_pipeline_with_context(self, sample_pdf: Path, tmp_path: Path):
        """Test complete pipeline including global context generation."""
        from src.main import process_pdf_full
        
        text_result, image_result, context = process_pdf_full(
            sample_pdf,
            job_id="context_test",
            image_output_dir=str(tmp_path),
            generate_context=True,
        )
        
        # All components should be present
        assert text_result.total_pages > 0
        assert context is not None, "Context should be generated"
        
        print(f"\n--- Full Pipeline with Context ---")
        print(f"Document type: {context.document_type}")
        print(f"Key terms: {len(context.key_terms)}")
        print(f"Main themes: {context.main_themes}")
        print(f"Summary preview: {context.summary[:300]}...")


class TestLargeDocumentHandling:
    """Integration tests for large document handling."""
    
    def test_memory_efficiency(self, sample_pdf: Path):
        """Test that extraction doesn't consume excessive memory."""
        import tracemalloc
        from src.pdf_extractor import PDFExtractor
        
        tracemalloc.start()
        
        extractor = PDFExtractor()
        result = extractor.extract(sample_pdf)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\n--- Memory Usage ---")
        print(f"Current: {current / 1024 / 1024:.2f} MB")
        print(f"Peak: {peak / 1024 / 1024:.2f} MB")
        print(f"Pages processed: {result.total_pages}")
        
        # Peak memory should be reasonable (< 500MB for most documents)
        assert peak < 500 * 1024 * 1024, f"Peak memory too high: {peak / 1024 / 1024:.2f} MB"
