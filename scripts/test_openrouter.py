"""
Test script for OpenRouter integration.
"""
import sys
import asyncio
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from services.gemini_service import get_gemini_service

# Setup simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_openrouter():
    """Test OpenRouter connection and generation."""
    logger.info("testing OpenRouter configuration...")
    logger.info(f"OpenRouter Key configured: {'Yes' if settings.openrouter_api_key else 'No'}")
    logger.info(f"Base URL: {settings.openrouter_base_url}")
    
    # Initialize service
    gemini = get_gemini_service()
    
    # Check if using OpenRouter
    if hasattr(gemini, 'use_openrouter') and gemini.use_openrouter:
        logger.info("✓ Service is using OpenRouter backend")
    else:
        logger.error("✗ Service is NOT using OpenRouter backend (check configuration)")
        return

    # Test connection
    logger.info("Testing connection...")
    is_connected = await gemini.test_connection_async()
    if is_connected:
        logger.info("✓ Connection test successful")
    else:
        logger.error("✗ Connection test failed")
        return

    # Test generation
    logger.info("Testing generation...")
    response = await gemini.generate_response(
        user_question="สวัสดีครับ แนะนำตัวหน่อย",
        context="นี่คือการทดสอบระบบ",
        max_retries=1
    )
    
    logger.info(f"Response: {response}")
    logger.info("✓ Test completed")

if __name__ == "__main__":
    asyncio.run(test_openrouter())
