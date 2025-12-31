"""Main entry point for Ingestion Agent."""

import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


def main():
    """Start the Ingestion Agent."""
    logger.info("Ingestion Agent starting...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Placeholder - will be replaced with ADK agent initialization
    logger.info("Ingestion Agent ready")


if __name__ == "__main__":
    main()
