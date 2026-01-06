"""
Image Region Extraction Module

Extracts images from PDF files:
- Extracts embedded images via /XObject resources
- Filters out small artifacts (< 100x100px)
- Generates image metadata (page, dimensions, format)
- Provides placeholder injection for text streams

Story: 2.2 - Image Region Extraction
"""

import io
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from uuid import uuid4

from PIL import Image
from pypdf import PdfReader
from pydantic import BaseModel, Field


class ImageMetadata(BaseModel):
    """Metadata for an extracted image from a PDF."""
    
    id: str = Field(
        ...,
        description="Unique identifier for this image (e.g., img_001)",
        examples=["img_001", "img_002"]
    )
    page: int = Field(
        ...,
        description="1-indexed page number where the image appears",
        ge=1
    )
    width: int = Field(
        ...,
        description="Image width in pixels",
        ge=1
    )
    height: int = Field(
        ...,
        description="Image height in pixels",
        ge=1
    )
    format: str = Field(
        ...,
        description="Image format (PNG, JPEG, etc.)",
        examples=["PNG", "JPEG"]
    )
    file_path: str = Field(
        ...,
        description="Path to the extracted image file"
    )
    original_name: Optional[str] = Field(
        default=None,
        description="Original XObject name in the PDF"
    )
    
    model_config = {"extra": "forbid"}


@dataclass
class ImageExtractionResult:
    """Result of image extraction from a PDF."""
    
    images: list[ImageMetadata] = field(default_factory=list)
    total_extracted: int = 0
    total_filtered: int = 0  # Count of images filtered due to size
    output_directory: str = ""
    source_file: str = ""
    
    @property
    def image_ids(self) -> list[str]:
        """Return list of all image IDs."""
        return [img.id for img in self.images]


class ImageExtractor:
    """
    Extracts images from PDF documents.
    
    Features:
    - Extracts embedded images via /XObject resources
    - Filters small artifacts (< 100x100px by default)
    - Saves images to configurable output directory
    - Generates sequential IDs (img_001, img_002, etc.)
    """
    
    # Default minimum dimensions for image filtering
    MIN_WIDTH = 100
    MIN_HEIGHT = 100
    
    # Default output directory template
    DEFAULT_OUTPUT_DIR = "/tmp/p2k-images"
    
    def __init__(
        self,
        min_width: int = MIN_WIDTH,
        min_height: int = MIN_HEIGHT,
        output_dir: Optional[str] = None,
    ):
        """
        Initialize the image extractor.
        
        Args:
            min_width: Minimum image width in pixels (default: 100)
            min_height: Minimum image height in pixels (default: 100)
            output_dir: Base directory for extracted images (default: /tmp/p2k-images)
        """
        self.min_width = min_width
        self.min_height = min_height
        self.output_dir = output_dir or self.DEFAULT_OUTPUT_DIR
    
    def extract(
        self,
        pdf_path: str | Path,
        job_id: Optional[str] = None,
    ) -> ImageExtractionResult:
        """
        Extract images from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            job_id: Optional job ID for organizing output (generates UUID if not provided)
            
        Returns:
            ImageExtractionResult containing extracted image metadata
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If file is not a valid PDF
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_path.suffix.lower() == ".pdf":
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        # Generate job ID if not provided
        if job_id is None:
            job_id = str(uuid4())[:8]
        
        # Create output directory
        job_output_dir = Path(self.output_dir) / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract images
        reader = PdfReader(str(pdf_path))
        images: list[ImageMetadata] = []
        filtered_count = 0
        image_counter = 0
        
        for page_num, page in enumerate(reader.pages, start=1):
            page_images, page_filtered = self._extract_page_images(
                page,
                page_num,
                job_output_dir,
                image_counter,
            )
            images.extend(page_images)
            filtered_count += page_filtered
            image_counter += len(page_images)
        
        return ImageExtractionResult(
            images=images,
            total_extracted=len(images),
            total_filtered=filtered_count,
            output_directory=str(job_output_dir),
            source_file=str(pdf_path),
        )
    
    def _extract_page_images(
        self,
        page,
        page_num: int,
        output_dir: Path,
        start_index: int,
    ) -> tuple[list[ImageMetadata], int]:
        """
        Extract images from a single page.
        
        Args:
            page: pypdf Page object
            page_num: 1-indexed page number
            output_dir: Directory to save images
            start_index: Starting index for image numbering
            
        Returns:
            Tuple of (list of ImageMetadata, count of filtered images)
        """
        images = []
        filtered_count = 0
        current_index = start_index
        
        # Check if page has XObject resources
        if "/Resources" not in page:
            return images, filtered_count
        
        resources = page["/Resources"]
        if "/XObject" not in resources:
            return images, filtered_count
        
        xobjects = resources["/XObject"].get_object()
        
        for obj_name in xobjects:
            try:
                xobj = xobjects[obj_name]
                
                # Check if this is an image
                if xobj.get("/Subtype") != "/Image":
                    continue
                
                # Extract image data
                image_data = self._extract_image_data(xobj)
                if image_data is None:
                    continue
                
                # Check dimensions
                width = xobj.get("/Width", 0)
                height = xobj.get("/Height", 0)
                
                if width < self.min_width or height < self.min_height:
                    filtered_count += 1
                    continue
                
                # Generate image ID
                current_index += 1
                image_id = f"img_{current_index:03d}"
                
                # Determine format and save
                img_format, file_ext = self._determine_format(xobj, image_data)
                file_path = output_dir / f"{image_id}.{file_ext}"
                
                # Save image
                self._save_image(image_data, file_path, img_format)
                
                # Create metadata
                metadata = ImageMetadata(
                    id=image_id,
                    page=page_num,
                    width=width,
                    height=height,
                    format=img_format,
                    file_path=str(file_path),
                    original_name=str(obj_name),
                )
                images.append(metadata)
                
            except Exception:
                # Skip images that can't be processed
                continue
        
        return images, filtered_count
    
    def _extract_image_data(self, xobj) -> Optional[bytes]:
        """
        Extract raw image data from an XObject.
        
        Args:
            xobj: pypdf XObject
            
        Returns:
            Image data as bytes, or None if extraction fails
        """
        try:
            # Get the raw data
            data = xobj.get_data()
            return data
        except Exception:
            return None
    
    def _determine_format(
        self,
        xobj,
        image_data: bytes,
    ) -> tuple[str, str]:
        """
        Determine the image format from XObject metadata or data inspection.
        
        Args:
            xobj: pypdf XObject
            image_data: Raw image bytes
            
        Returns:
            Tuple of (format name, file extension)
        """
        # Check filter type
        filter_type = xobj.get("/Filter", "")
        
        if isinstance(filter_type, list):
            filter_type = filter_type[0] if filter_type else ""
        
        filter_str = str(filter_type)
        
        if "DCTDecode" in filter_str:
            return "JPEG", "jpg"
        elif "JPXDecode" in filter_str:
            return "JPEG2000", "jp2"
        elif "FlateDecode" in filter_str or "LZWDecode" in filter_str:
            # Could be PNG-like data
            return "PNG", "png"
        
        # Default to PNG
        return "PNG", "png"
    
    def _save_image(
        self,
        image_data: bytes,
        file_path: Path,
        img_format: str,
    ) -> None:
        """
        Save image data to file.
        
        Args:
            image_data: Raw image bytes
            file_path: Path to save the image
            img_format: Image format (PNG, JPEG, etc.)
        """
        if img_format == "JPEG":
            # JPEG data can be written directly
            file_path.write_bytes(image_data)
        else:
            # Try to open with PIL and save as PNG
            try:
                with Image.open(io.BytesIO(image_data)) as img:
                    img.save(str(file_path), format="PNG")
            except Exception:
                # If PIL can't open it, write raw data
                file_path.write_bytes(image_data)


def inject_image_placeholders(
    text: str,
    images: list[ImageMetadata],
) -> str:
    """
    Inject image placeholders into text based on page positions.
    
    This is a simple implementation that appends placeholders at the end
    of the text for each page's images. For more sophisticated positioning,
    the text extraction would need to track image positions relative to text.
    
    Args:
        text: The extracted text content
        images: List of ImageMetadata from extraction
        
    Returns:
        Text with [IMAGE: img_XXX] placeholders inserted
    """
    if not images:
        return text
    
    # Group images by page
    images_by_page: dict[int, list[ImageMetadata]] = {}
    for img in images:
        if img.page not in images_by_page:
            images_by_page[img.page] = []
        images_by_page[img.page].append(img)
    
    # Create placeholder text for each page
    placeholder_sections = []
    for page_num in sorted(images_by_page.keys()):
        page_images = images_by_page[page_num]
        page_placeholders = [f"[IMAGE: {img.id}]" for img in page_images]
        placeholder_sections.append(
            f"\n\n--- Images from page {page_num} ---\n" + "\n".join(page_placeholders)
        )
    
    return text + "".join(placeholder_sections)


def extract_pdf_images(
    pdf_path: str | Path,
    job_id: Optional[str] = None,
    min_width: int = 100,
    min_height: int = 100,
    output_dir: Optional[str] = None,
) -> ImageExtractionResult:
    """
    Convenience function to extract images from a PDF.
    
    Args:
        pdf_path: Path to the PDF file
        job_id: Optional job ID for organizing output
        min_width: Minimum image width (default: 100px)
        min_height: Minimum image height (default: 100px)
        output_dir: Base directory for extracted images
        
    Returns:
        ImageExtractionResult containing extracted image metadata
    """
    extractor = ImageExtractor(
        min_width=min_width,
        min_height=min_height,
        output_dir=output_dir,
    )
    return extractor.extract(pdf_path, job_id)
