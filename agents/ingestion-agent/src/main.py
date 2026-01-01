"""Main entry point for Ingestion Agent."""

import asyncio
import logging
import os

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

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


if __name__ == "__main__":
    main()
