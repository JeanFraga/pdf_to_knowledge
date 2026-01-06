"""
Unit Tests for Image Extraction Module

Tests cover:
- Image extraction from PDF XObjects
- Size filtering (< 100x100px filtered out)
- Placeholder injection into text
- ImageMetadata schema validation
- Edge cases and error handling

Story: 2.2 - Image Region Extraction
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.image_extractor import (
    ImageExtractor,
    ImageExtractionResult,
    ImageMetadata,
    extract_pdf_images,
    inject_image_placeholders,
)


class TestImageMetadata:
    """Tests for ImageMetadata Pydantic model."""
    
    def test_valid_metadata(self):
        """Test creating valid ImageMetadata."""
        meta = ImageMetadata(
            id="img_001",
            page=1,
            width=200,
            height=150,
            format="PNG",
            file_path="/tmp/p2k-images/abc123/img_001.png",
        )
        
        assert meta.id == "img_001"
        assert meta.page == 1
        assert meta.width == 200
        assert meta.height == 150
        assert meta.format == "PNG"
        assert meta.file_path == "/tmp/p2k-images/abc123/img_001.png"
        assert meta.original_name is None
    
    def test_metadata_with_original_name(self):
        """Test ImageMetadata with original XObject name."""
        meta = ImageMetadata(
            id="img_002",
            page=2,
            width=300,
            height=400,
            format="JPEG",
            file_path="/tmp/test.jpg",
            original_name="/Im1",
        )
        
        assert meta.original_name == "/Im1"
    
    def test_invalid_page_number(self):
        """Test that page must be >= 1."""
        with pytest.raises(ValueError):
            ImageMetadata(
                id="img_001",
                page=0,  # Invalid
                width=100,
                height=100,
                format="PNG",
                file_path="/tmp/test.png",
            )
    
    def test_invalid_dimensions(self):
        """Test that dimensions must be >= 1."""
        with pytest.raises(ValueError):
            ImageMetadata(
                id="img_001",
                page=1,
                width=0,  # Invalid
                height=100,
                format="PNG",
                file_path="/tmp/test.png",
            )


class TestImageExtractionResult:
    """Tests for ImageExtractionResult dataclass."""
    
    def test_empty_result(self):
        """Test empty extraction result."""
        result = ImageExtractionResult()
        
        assert result.images == []
        assert result.total_extracted == 0
        assert result.total_filtered == 0
        assert result.image_ids == []
    
    def test_result_with_images(self):
        """Test result with extracted images."""
        images = [
            ImageMetadata(
                id="img_001", page=1, width=200, height=200,
                format="PNG", file_path="/tmp/img_001.png"
            ),
            ImageMetadata(
                id="img_002", page=2, width=300, height=300,
                format="JPEG", file_path="/tmp/img_002.jpg"
            ),
        ]
        
        result = ImageExtractionResult(
            images=images,
            total_extracted=2,
            total_filtered=1,
            output_directory="/tmp/p2k-images/abc",
            source_file="/path/to/doc.pdf",
        )
        
        assert len(result.images) == 2
        assert result.total_extracted == 2
        assert result.total_filtered == 1
        assert result.image_ids == ["img_001", "img_002"]


class TestImageExtractor:
    """Tests for ImageExtractor class."""
    
    @pytest.fixture
    def extractor(self):
        """Create an ImageExtractor instance."""
        return ImageExtractor()
    
    @pytest.fixture
    def custom_extractor(self, tmp_path):
        """Create ImageExtractor with custom settings."""
        return ImageExtractor(
            min_width=50,
            min_height=50,
            output_dir=str(tmp_path),
        )
    
    def test_default_settings(self, extractor):
        """Test default extractor settings."""
        assert extractor.min_width == 100
        assert extractor.min_height == 100
        assert extractor.output_dir == "/tmp/p2k-images"
    
    def test_custom_settings(self, custom_extractor, tmp_path):
        """Test custom extractor settings."""
        assert custom_extractor.min_width == 50
        assert custom_extractor.min_height == 50
        assert custom_extractor.output_dir == str(tmp_path)
    
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
    
    def test_determine_format_jpeg(self, extractor):
        """Test JPEG format detection."""
        mock_xobj = {"/Filter": "/DCTDecode"}
        fmt, ext = extractor._determine_format(mock_xobj, b"")
        
        assert fmt == "JPEG"
        assert ext == "jpg"
    
    def test_determine_format_jpeg2000(self, extractor):
        """Test JPEG2000 format detection."""
        mock_xobj = {"/Filter": "/JPXDecode"}
        fmt, ext = extractor._determine_format(mock_xobj, b"")
        
        assert fmt == "JPEG2000"
        assert ext == "jp2"
    
    def test_determine_format_flate(self, extractor):
        """Test FlateDecode (PNG) format detection."""
        mock_xobj = {"/Filter": "/FlateDecode"}
        fmt, ext = extractor._determine_format(mock_xobj, b"")
        
        assert fmt == "PNG"
        assert ext == "png"
    
    def test_determine_format_default(self, extractor):
        """Test default format when unknown."""
        mock_xobj = {}
        fmt, ext = extractor._determine_format(mock_xobj, b"")
        
        assert fmt == "PNG"
        assert ext == "png"
    
    def test_determine_format_list_filter(self, extractor):
        """Test format detection with list filter."""
        mock_xobj = {"/Filter": ["/DCTDecode", "/FlateDecode"]}
        fmt, ext = extractor._determine_format(mock_xobj, b"")
        
        assert fmt == "JPEG"
        assert ext == "jpg"
    
    @patch('src.image_extractor.PdfReader')
    def test_extract_creates_output_directory(
        self, mock_reader_class, extractor, tmp_path
    ):
        """Test that extraction creates output directory."""
        # Create fake PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        
        # Mock reader with no pages
        mock_reader = MagicMock()
        mock_reader.pages = []
        mock_reader_class.return_value = mock_reader
        
        # Use custom output dir
        extractor.output_dir = str(tmp_path / "output")
        
        result = extractor.extract(pdf_file, job_id="test123")
        
        # Output directory should be created
        expected_dir = tmp_path / "output" / "test123"
        assert expected_dir.exists()
        assert result.output_directory == str(expected_dir)
    
    @patch('src.image_extractor.PdfReader')
    def test_extract_filters_small_images(
        self, mock_reader_class, custom_extractor, tmp_path
    ):
        """Test that small images are filtered out."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        
        # Create mock page with small image
        mock_page = MagicMock()
        mock_resources = MagicMock()
        mock_xobject = MagicMock()
        
        # Small image (30x30, below 50x50 threshold)
        small_img = MagicMock()
        small_img.get.side_effect = lambda k, d=None: {
            "/Subtype": "/Image",
            "/Width": 30,
            "/Height": 30,
            "/Filter": "/FlateDecode",
        }.get(k, d)
        small_img.get_data.return_value = b"fake image data"
        
        mock_xobject.get_object.return_value = {"/Im1": small_img}
        mock_resources.__contains__ = lambda self, k: k in ["/XObject"]
        mock_resources.__getitem__ = lambda self, k: mock_xobject
        
        mock_page.__contains__ = lambda self, k: k == "/Resources"
        mock_page.__getitem__ = lambda self, k: mock_resources
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader
        
        result = custom_extractor.extract(pdf_file, job_id="filter_test")
        
        # Image should be filtered (30x30 < 50x50 threshold)
        assert result.total_extracted == 0
        assert result.total_filtered == 1
    
    @patch('src.image_extractor.PdfReader')
    def test_extract_no_resources(self, mock_reader_class, extractor, tmp_path):
        """Test handling pages without resources."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        
        mock_page = MagicMock()
        mock_page.__contains__ = lambda self, k: False
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader
        
        result = extractor.extract(pdf_file, job_id="no_resources")
        
        assert result.total_extracted == 0
        assert result.total_filtered == 0


class TestPlaceholderInjection:
    """Tests for placeholder injection functionality."""
    
    def test_inject_no_images(self):
        """Test injection with no images."""
        text = "Some document text."
        result = inject_image_placeholders(text, [])
        
        assert result == text
    
    def test_inject_single_image(self):
        """Test injection with single image."""
        text = "Document content."
        images = [
            ImageMetadata(
                id="img_001", page=1, width=200, height=200,
                format="PNG", file_path="/tmp/img_001.png"
            ),
        ]
        
        result = inject_image_placeholders(text, images)
        
        assert "Document content." in result
        assert "[IMAGE: img_001]" in result
        assert "page 1" in result
    
    def test_inject_multiple_images_same_page(self):
        """Test injection with multiple images on same page."""
        text = "Content here."
        images = [
            ImageMetadata(
                id="img_001", page=1, width=200, height=200,
                format="PNG", file_path="/tmp/img_001.png"
            ),
            ImageMetadata(
                id="img_002", page=1, width=300, height=300,
                format="JPEG", file_path="/tmp/img_002.jpg"
            ),
        ]
        
        result = inject_image_placeholders(text, images)
        
        assert "[IMAGE: img_001]" in result
        assert "[IMAGE: img_002]" in result
        # Both should be under page 1 section
        assert result.count("page 1") == 1
    
    def test_inject_images_multiple_pages(self):
        """Test injection with images on different pages."""
        text = "Multi-page document."
        images = [
            ImageMetadata(
                id="img_001", page=1, width=200, height=200,
                format="PNG", file_path="/tmp/img_001.png"
            ),
            ImageMetadata(
                id="img_002", page=3, width=300, height=300,
                format="JPEG", file_path="/tmp/img_002.jpg"
            ),
        ]
        
        result = inject_image_placeholders(text, images)
        
        assert "[IMAGE: img_001]" in result
        assert "[IMAGE: img_002]" in result
        assert "page 1" in result
        assert "page 3" in result


class TestConvenienceFunction:
    """Tests for the extract_pdf_images convenience function."""
    
    def test_convenience_function_invalid_file(self, tmp_path):
        """Test convenience function with invalid file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Not a PDF")
        
        with pytest.raises(ValueError):
            extract_pdf_images(txt_file)
    
    @patch('src.image_extractor.PdfReader')
    def test_convenience_function_with_options(
        self, mock_reader_class, tmp_path
    ):
        """Test convenience function with custom options."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        
        mock_reader = MagicMock()
        mock_reader.pages = []
        mock_reader_class.return_value = mock_reader
        
        result = extract_pdf_images(
            pdf_file,
            job_id="custom_job",
            min_width=50,
            min_height=50,
            output_dir=str(tmp_path / "custom_output"),
        )
        
        assert isinstance(result, ImageExtractionResult)
        assert "custom_job" in result.output_directory


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.fixture
    def extractor(self):
        return ImageExtractor()
    
    def test_extract_generates_job_id(self, extractor, tmp_path):
        """Test that job ID is auto-generated if not provided."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        
        with patch('src.image_extractor.PdfReader') as mock_reader_class:
            mock_reader = MagicMock()
            mock_reader.pages = []
            mock_reader_class.return_value = mock_reader
            
            result = extractor.extract(pdf_file)
            
            # Should have generated a job ID
            assert result.output_directory != ""
            assert Path(result.output_directory).name != ""
    
    def test_image_extraction_handles_corrupt_xobject(self, extractor, tmp_path):
        """Test handling of corrupt XObject that raises exception."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        
        with patch('src.image_extractor.PdfReader') as mock_reader_class:
            mock_page = MagicMock()
            mock_resources = MagicMock()
            mock_xobject = MagicMock()
            
            # Create corrupt image that raises exception
            corrupt_img = MagicMock()
            corrupt_img.get.side_effect = Exception("Corrupt XObject")
            
            mock_xobject.get_object.return_value = {"/Im1": corrupt_img}
            mock_resources.__contains__ = lambda self, k: k in ["/XObject"]
            mock_resources.__getitem__ = lambda self, k: mock_xobject
            
            mock_page.__contains__ = lambda self, k: k == "/Resources"
            mock_page.__getitem__ = lambda self, k: mock_resources
            
            mock_reader = MagicMock()
            mock_reader.pages = [mock_page]
            mock_reader_class.return_value = mock_reader
            
            # Should not raise, just skip corrupt image
            result = extractor.extract(pdf_file, job_id="corrupt_test")
            
            assert result.total_extracted == 0
