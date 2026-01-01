"""Main entry point for Database Agent."""

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
DATABASE_AGENT_MODEL = os.getenv("DATABASE_AGENT_MODEL", "gemini-2.0-flash")

# Agent definition
root_agent = Agent(
    model=DATABASE_AGENT_MODEL,
    name="database_agent",
    description="Storage and retrieval agent with MCP for the pdf_to_knowledge pipeline.",
    instruction="""You are the Database Agent for the pdf_to_knowledge system.
Your role is to:
1. Receive knowledge chunks from the Ingestion Agent via A2A protocol
2. Validate incoming data against schemas
3. Store data in Firestore (documents) and Neo4j (graph relationships)
4. Provide retrieval capabilities for stored knowledge

For now, respond to greetings and basic queries about your capabilities.""",
)


async def hello_gemini() -> str:
    """Test endpoint to verify Gemini connectivity."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="database_agent_app",
        session_service=session_service,
    )
    
    user_id = "test-user"
    session_id = "test-session"
    
    # Create session
    session = await session_service.create_session(
        app_name="database_agent_app",
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
    """Start the Database Agent."""
    logger.info("Database Agent starting...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Model: {DATABASE_AGENT_MODEL}")
    
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
    
    logger.info("Database Agent ready")


if __name__ == "__main__":
    main()
