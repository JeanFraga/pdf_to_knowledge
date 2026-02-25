"""Main entry point for Ingestion Agent."""

import asyncio
import logging
import os
from pathlib import Path

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.pdf_extractor import ExtractionResult
from src.image_extractor import (
    ImageExtractionResult,
    ImageMetadata,
    inject_image_placeholders,
)
from src.context_generator import (
    ContextGenerator,
    GlobalContext,
    generate_global_context,
)
from src.extraction_backend import get_extraction_backend, ExtractionBackend

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Model configuration (centralized via env var)
INGESTION_AGENT_MODEL = os.getenv("INGESTION_AGENT_MODEL", "gemini-2.0-flash")

# Agent definition
root_agent = Agent(
    model=INGESTION_AGENT_MODEL,
    name="ingestion_agent",
    description="PDF ingestion and agentic chunking agent for the pdf_to_knowledge pipeline.",
    instruction="""You are the Ingestion Agent for the pdf_to_knowledge system.
Your role is to:
1. Parse and process PDF documents
2. Perform semantic segmentation of content
3. Inject global context into chunks
4. Communicate with the Database Agent via A2A protocol

For now, respond to greetings and basic queries about your capabilities.""",
)


async def hello_gemini() -> str:
    """Test endpoint to verify Gemini connectivity."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="ingestion_agent_app",
        session_service=session_service,
    )
    
    user_id = "test-user"
    session_id = "test-session"
    
    # Create session
    session = await session_service.create_session(
        app_name="ingestion_agent_app",
        user_id=user_id,
        session_id=session_id,
    )
    
    # Send test message
    content = types.Content(
        role="user",
        parts=[types.Part(text="Hello! What are you and what can you do?")]
    )
    
    response_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_text += part.text
    
    return response_text


def main():
    """Start the Ingestion Agent."""
    logger.info("Ingestion Agent starting...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Model: {INGESTION_AGENT_MODEL}")
    
    # Verify API key is set
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set!")
        return
    
    # Set GOOGLE_API_KEY if only GEMINI_API_KEY is set (ADK expects GOOGLE_API_KEY)
    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
    
    logger.info("API key configured ✓")
    
    # Run hello test
    logger.info("Testing Gemini connectivity...")
    try:
        response = asyncio.run(hello_gemini())
        logger.info(f"Gemini response: {response[:200]}..." if len(response) > 200 else f"Gemini response: {response}")
        logger.info("Gemini connectivity test passed ✓")
    except Exception as e:
        logger.error(f"Gemini connectivity test failed: {e}")
        raise
    
    logger.info("Ingestion Agent ready")


def process_pdf(pdf_path: str | Path, backend: ExtractionBackend | None = None) -> ExtractionResult:
    """
    Process a PDF file and extract cleaned text.
    
    This is the main entry point for PDF processing in the ingestion pipeline.
    Uses the configured extraction backend (PDF_EXTRACTOR_BACKEND env var).
    
    Args:
        pdf_path: Path to the PDF file to process
        backend: Optional extraction backend override. If None, uses
                 the backend configured via PDF_EXTRACTOR_BACKEND env var.
        
    Returns:
        ExtractionResult containing cleaned text, page info, and detected headers/footers
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If file is not a valid PDF
    """
    logger.info(f"Processing PDF: {pdf_path}")
    
    if backend is None:
        backend = get_extraction_backend()
    
    result = backend.extract_text(pdf_path)
    
    logger.info(f"Extracted {result.total_pages} pages from {result.source_file} (backend: {backend.name})")
    
    if result.detected_headers:
        logger.info(f"Detected {len(result.detected_headers)} repeated headers")
    if result.detected_footers:
        logger.info(f"Detected {len(result.detected_footers)} repeated footers")
    
    return result


def process_pdf_with_images(
    pdf_path: str | Path,
    job_id: str | None = None,
    image_output_dir: str | None = None,
    backend: ExtractionBackend | None = None,
) -> tuple[ExtractionResult, ImageExtractionResult]:
    """
    Process a PDF file, extracting both text and images.
    
    This is the comprehensive entry point that:
    1. Extracts text with header/footer removal
    2. Extracts images with size filtering
    3. Injects image placeholders into the text stream
    
    Uses the configured extraction backend (PDF_EXTRACTOR_BACKEND env var).
    
    Args:
        pdf_path: Path to the PDF file to process
        job_id: Optional job ID for organizing image output
        image_output_dir: Optional base directory for extracted images
        backend: Optional extraction backend override. If None, uses
                 the backend configured via PDF_EXTRACTOR_BACKEND env var.
        
    Returns:
        Tuple of (ExtractionResult, ImageExtractionResult)
        The ExtractionResult's full_text will have image placeholders injected
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If file is not a valid PDF
    """
    logger.info(f"Processing PDF with images: {pdf_path}")
    
    if backend is None:
        backend = get_extraction_backend()
    
    # Step 1: Extract text
    text_result = backend.extract_text(pdf_path)
    
    logger.info(f"Extracted {text_result.total_pages} pages of text (backend: {backend.name})")
    
    # Step 2: Extract images
    image_result = backend.extract_images(pdf_path, job_id=job_id, output_dir=image_output_dir)
    
    logger.info(f"Extracted {image_result.total_extracted} images, filtered {image_result.total_filtered} small artifacts")
    
    # Step 3: Inject placeholders into text (modifies pages in-place)
    if image_result.images:
        for page in text_result.pages:
            # Get images for this page
            page_images = [img for img in image_result.images if img.page == page.page_number]
            if page_images:
                placeholders = "\n".join(f"[IMAGE: {img.id}]" for img in page_images)
                page.cleaned_text = f"{page.cleaned_text}\n\n{placeholders}"
        
        logger.info(f"Injected placeholders for {len(image_result.images)} images")
    
    return text_result, image_result


def process_pdf_full(
    pdf_path: str | Path,
    job_id: str | None = None,
    image_output_dir: str | None = None,
    generate_context: bool = True,
    backend: ExtractionBackend | None = None,
) -> tuple[ExtractionResult, ImageExtractionResult, GlobalContext | None]:
    """
    Full PDF processing pipeline: text, images, and global context.
    
    This is the complete ingestion pipeline that:
    1. Extracts text with header/footer removal
    2. Extracts images with size filtering
    3. Injects image placeholders into the text stream
    4. Generates global context summary via Gemini
    
    Uses the configured extraction backend (PDF_EXTRACTOR_BACKEND env var).
    
    Args:
        pdf_path: Path to the PDF file to process
        job_id: Optional job ID for organizing image output
        image_output_dir: Optional base directory for extracted images
        generate_context: Whether to generate global context (default: True)
        backend: Optional extraction backend override. If None, uses
                 the backend configured via PDF_EXTRACTOR_BACKEND env var.
        
    Returns:
        Tuple of (ExtractionResult, ImageExtractionResult, GlobalContext or None)
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If file is not a valid PDF
    """
    pdf_path = Path(pdf_path)
    logger.info(f"Full PDF processing pipeline: {pdf_path}")
    
    if backend is None:
        backend = get_extraction_backend()
    
    # Steps 1-3: Extract text and images
    text_result, image_result = process_pdf_with_images(
        pdf_path,
        job_id=job_id,
        image_output_dir=image_output_dir,
        backend=backend,
    )
    
    # Step 4: Generate global context
    global_context = None
    if generate_context:
        try:
            logger.info("Generating global context via Gemini...")
            context_generator = ContextGenerator()
            global_context = context_generator.generate(
                full_text=text_result.full_text,
                source_document=str(pdf_path.name),
            )
            logger.info(f"Global context generated: {global_context.document_type}, {len(global_context.key_terms)} key terms")
        except Exception as e:
            logger.warning(f"Failed to generate global context: {e}")
            # Continue without context - don't fail the entire pipeline
    
    return text_result, image_result, global_context


if __name__ == "__main__":
    main()
