"""
Tests for the Extraction Backend abstraction layer.

Tests:
- ExtractionBackend ABC contract
- PyPDFBackend delegates to PDFExtractor and ImageExtractor
- DoclingBackend raises NotImplementedError
- get_extraction_backend factory (env var driven)
- Backend registry and error handling
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.extraction_backend import (
    DoclingBackend,
    ExtractionBackend,
    PyPDFBackend,
    get_extraction_backend,
    _BACKENDS,
)
from src.pdf_extractor import ExtractionResult, PageText
from src.image_extractor import ImageExtractionResult


# --- ExtractionBackend ABC ---

class TestExtractionBackendABC:
    """Tests for the abstract base class contract."""

    def test_cannot_instantiate_abc(self):
        """ExtractionBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ExtractionBackend()

    def test_subclass_must_implement_extract_text(self):
        """Subclass without extract_text raises TypeError."""

        class Incomplete(ExtractionBackend):
            def extract_images(self, pdf_path, job_id=None, output_dir=None):
                pass

            @property
            def name(self):
                return "incomplete"

        with pytest.raises(TypeError):
            Incomplete()

    def test_subclass_must_implement_extract_images(self):
        """Subclass without extract_images raises TypeError."""

        class Incomplete(ExtractionBackend):
            def extract_text(self, pdf_path):
                pass

            @property
            def name(self):
                return "incomplete"

        with pytest.raises(TypeError):
            Incomplete()

    def test_subclass_must_implement_name(self):
        """Subclass without name property raises TypeError."""

        class Incomplete(ExtractionBackend):
            def extract_text(self, pdf_path):
                pass

            def extract_images(self, pdf_path, job_id=None, output_dir=None):
                pass

        with pytest.raises(TypeError):
            Incomplete()


# --- PyPDFBackend ---

class TestPyPDFBackend:
    """Tests for the pypdf backend implementation."""

    def test_name(self):
        backend = PyPDFBackend()
        assert backend.name == "pypdf"

    @patch("src.pdf_extractor.PDFExtractor")
    def test_extract_text_delegates_to_pdf_extractor(self, mock_cls):
        """extract_text creates a PDFExtractor and calls extract()."""
        mock_result = ExtractionResult(
            pages=[PageText(page_number=1, raw_text="hello")],
            total_pages=1,
            source_file="test.pdf",
        )
        mock_cls.return_value.extract.return_value = mock_result

        backend = PyPDFBackend()
        result = backend.extract_text("/tmp/test.pdf")

        mock_cls.return_value.extract.assert_called_once_with("/tmp/test.pdf")
        assert result.total_pages == 1

    @patch("src.image_extractor.ImageExtractor")
    def test_extract_images_delegates_to_image_extractor(self, mock_cls):
        """extract_images creates an ImageExtractor and calls extract()."""
        mock_result = ImageExtractionResult(
            images=[], total_extracted=0, total_filtered=0
        )
        mock_cls.return_value.extract.return_value = mock_result

        backend = PyPDFBackend()
        result = backend.extract_images("/tmp/test.pdf", job_id="abc")

        mock_cls.return_value.extract.assert_called_once_with(
            "/tmp/test.pdf", job_id="abc"
        )
        assert result.total_extracted == 0

    @patch("src.image_extractor.ImageExtractor")
    def test_extract_images_with_output_dir(self, mock_cls):
        """extract_images passes output_dir to ImageExtractor constructor."""
        mock_result = ImageExtractionResult(
            images=[], total_extracted=0, total_filtered=0
        )
        mock_cls.return_value.extract.return_value = mock_result

        backend = PyPDFBackend()
        backend.extract_images("/tmp/test.pdf", output_dir="/custom/dir")

        mock_cls.assert_called_once_with(output_dir="/custom/dir")

    @patch("src.image_extractor.ImageExtractor")
    def test_extract_images_without_output_dir(self, mock_cls):
        """extract_images uses default ImageExtractor when no output_dir."""
        mock_result = ImageExtractionResult(
            images=[], total_extracted=0, total_filtered=0
        )
        mock_cls.return_value.extract.return_value = mock_result

        backend = PyPDFBackend()
        backend.extract_images("/tmp/test.pdf")

        mock_cls.assert_called_once_with()


# --- DoclingBackend ---

class TestDoclingBackend:
    """Tests for the docling backend stub."""

    def test_name(self):
        backend = DoclingBackend()
        assert backend.name == "docling"

    def test_extract_text_raises_not_implemented(self):
        backend = DoclingBackend()
        with pytest.raises(NotImplementedError, match="Docling backend is not yet implemented"):
            backend.extract_text("/tmp/test.pdf")

    def test_extract_images_raises_not_implemented(self):
        backend = DoclingBackend()
        with pytest.raises(NotImplementedError, match="Docling backend is not yet implemented"):
            backend.extract_images("/tmp/test.pdf")


# --- Factory ---

class TestGetExtractionBackend:
    """Tests for the factory function."""

    def test_default_is_pypdf(self):
        """Default backend is pypdf when no env var set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if present
            os.environ.pop("PDF_EXTRACTOR_BACKEND", None)
            backend = get_extraction_backend()
            assert isinstance(backend, PyPDFBackend)

    def test_explicit_pypdf(self):
        with patch.dict(os.environ, {"PDF_EXTRACTOR_BACKEND": "pypdf"}):
            backend = get_extraction_backend()
            assert isinstance(backend, PyPDFBackend)

    def test_explicit_docling(self):
        with patch.dict(os.environ, {"PDF_EXTRACTOR_BACKEND": "docling"}):
            backend = get_extraction_backend()
            assert isinstance(backend, DoclingBackend)

    def test_case_insensitive(self):
        with patch.dict(os.environ, {"PDF_EXTRACTOR_BACKEND": "PyPDF"}):
            backend = get_extraction_backend()
            assert isinstance(backend, PyPDFBackend)

    def test_strips_whitespace(self):
        with patch.dict(os.environ, {"PDF_EXTRACTOR_BACKEND": "  pypdf  "}):
            backend = get_extraction_backend()
            assert isinstance(backend, PyPDFBackend)

    def test_override_parameter(self):
        """Explicit backend_name parameter overrides env var."""
        with patch.dict(os.environ, {"PDF_EXTRACTOR_BACKEND": "pypdf"}):
            backend = get_extraction_backend("docling")
            assert isinstance(backend, DoclingBackend)

    def test_unknown_backend_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown PDF extractor backend"):
            get_extraction_backend("unknown")

    def test_unknown_backend_lists_available(self):
        with pytest.raises(ValueError, match="docling"):
            get_extraction_backend("nonexistent")


# --- Registry ---

class TestBackendRegistry:
    """Tests for the backend registry."""

    def test_registry_has_pypdf(self):
        assert "pypdf" in _BACKENDS

    def test_registry_has_docling(self):
        assert "docling" in _BACKENDS

    def test_all_registry_entries_are_extraction_backends(self):
        for name, cls in _BACKENDS.items():
            assert issubclass(cls, ExtractionBackend), f"{name} is not an ExtractionBackend"
