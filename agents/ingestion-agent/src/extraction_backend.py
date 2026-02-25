"""
PDF Extraction Backend Abstraction

Provides a strategy pattern for swapping PDF extraction implementations
via the PDF_EXTRACTOR_BACKEND environment variable.

Supported backends:
- "pypdf" (default): Uses pypdf + Pillow for text/image extraction
- "docling": Uses Docling for ML-based document understanding (requires Epic 7)

Configuration:
    Set PDF_EXTRACTOR_BACKEND in .env or environment variables.
"""

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from src.pdf_extractor import ExtractionResult
from src.image_extractor import ImageExtractionResult

logger = logging.getLogger(__name__)


class ExtractionBackend(ABC):
    """
    Abstract base class for PDF extraction backends.

    All backends must produce the same ExtractionResult and
    ImageExtractionResult data structures, regardless of the
    underlying library used.
    """

    @abstractmethod
    def extract_text(self, pdf_path: str | Path) -> ExtractionResult:
        """
        Extract cleaned text from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ExtractionResult with cleaned pages, detected headers/footers
        """
        ...

    @abstractmethod
    def extract_images(
        self,
        pdf_path: str | Path,
        job_id: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> ImageExtractionResult:
        """
        Extract images from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            job_id: Optional job identifier for output organization
            output_dir: Optional base directory for extracted images

        Returns:
            ImageExtractionResult with image metadata and file paths
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the backend name for logging."""
        ...


class PyPDFBackend(ExtractionBackend):
    """
    PDF extraction backend using pypdf + Pillow.

    This is the default backend, implementing text extraction via
    pypdf with heuristic header/footer removal and page number
    stripping, plus image extraction via /XObject resources.
    """

    @property
    def name(self) -> str:
        return "pypdf"

    def extract_text(self, pdf_path: str | Path) -> ExtractionResult:
        from src.pdf_extractor import PDFExtractor

        extractor = PDFExtractor()
        return extractor.extract(pdf_path)

    def extract_images(
        self,
        pdf_path: str | Path,
        job_id: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> ImageExtractionResult:
        from src.image_extractor import ImageExtractor

        extractor = (
            ImageExtractor(output_dir=output_dir)
            if output_dir
            else ImageExtractor()
        )
        return extractor.extract(pdf_path, job_id=job_id)


class DoclingBackend(ExtractionBackend):
    """
    PDF extraction backend using Docling (DS4SD/docling).

    Uses ML-based layout analysis for superior document understanding:
    - Semantic structure detection (headings, paragraphs, lists, tables)
    - Layout-aware image/figure extraction
    - Built-in OCR support for scanned documents
    - Table extraction as structured data

    Requires: pip install docling
    See Epic 7 for implementation details.
    """

    @property
    def name(self) -> str:
        return "docling"

    def extract_text(self, pdf_path: str | Path) -> ExtractionResult:
        raise NotImplementedError(
            "Docling backend is not yet implemented. "
            "See Epic 7: Advanced PDF Processing with Docling. "
            "Set PDF_EXTRACTOR_BACKEND=pypdf to use the default backend."
        )

    def extract_images(
        self,
        pdf_path: str | Path,
        job_id: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> ImageExtractionResult:
        raise NotImplementedError(
            "Docling backend is not yet implemented. "
            "See Epic 7: Advanced PDF Processing with Docling. "
            "Set PDF_EXTRACTOR_BACKEND=pypdf to use the default backend."
        )


# Backend registry
_BACKENDS: dict[str, type[ExtractionBackend]] = {
    "pypdf": PyPDFBackend,
    "docling": DoclingBackend,
}


def get_extraction_backend(backend_name: Optional[str] = None) -> ExtractionBackend:
    """
    Factory function to create the configured extraction backend.

    Reads PDF_EXTRACTOR_BACKEND from environment if backend_name
    is not explicitly provided.

    Args:
        backend_name: Override for the backend name. If None, reads
                      from PDF_EXTRACTOR_BACKEND env var (default: "pypdf").

    Returns:
        An initialized ExtractionBackend instance.

    Raises:
        ValueError: If the requested backend is not registered.
    """
    name = backend_name or os.getenv("PDF_EXTRACTOR_BACKEND", "pypdf")
    name = name.strip().lower()

    backend_class = _BACKENDS.get(name)
    if backend_class is None:
        available = ", ".join(sorted(_BACKENDS.keys()))
        raise ValueError(
            f"Unknown PDF extractor backend: '{name}'. "
            f"Available backends: {available}"
        )

    backend = backend_class()
    logger.info(f"Using PDF extraction backend: {backend.name}")
    return backend
