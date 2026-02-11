import asyncio
import sys
import os
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from services.knowledge_base import get_knowledge_base
from services.memory_service import get_memory_service
from services.google_sheet_service import get_google_sheet_service
from services.gemini_service import get_gemini_service
from config.settings import settings

async def run_comprehensive_test():
    logger.info("Starting Comprehensive Service Test...")
    
    # 1. Test Memory Service
    logger.info("--- Testing Memory Service ---")
    memory = get_memory_service()
    test_q = "Test Question " + os.urandom(4).hex()
    test_a = "Test Answer"
    memory.add_memory(test_q, test_a, category="test")
    results = memory.find_similar(test_q, category="test")
    if any(r['question'] == test_q for r in results):
        logger.info("✅ Memory Service: Add/Retrieve successful")
    else:
        logger.error("❌ Memory Service: Failed to retrieve memory")

    # 2. Test Knowledge Base
    logger.info("--- Testing Knowledge Base ---")
    kb = get_knowledge_base(settings.chroma_persist_dir)
    kb_q = "Product Info " + os.urandom(4).hex()
    kb_a = "Product Details Content"
    kb.add_qa_pair(kb_q, kb_a, source="test")
    # Wait a bit for indexing
    await asyncio.sleep(1)
    results = kb.search_products(kb_q, top_k=1)
    logger.info(f"✅ Knowledge Base: Initialized with {kb.get_product_count()} products")

    # 3. Test Google Sheets Service
    logger.info("--- Testing Google Sheets Service ---")
    gs = get_google_sheet_service()
    if gs.connected:
        try:
            gs.log_chat("test_user_123", "Hello Test", "Reply Test")
            logger.info("✅ Google Sheets: log_chat successful")
            
            gs.log_comment(
                post_id="post_123",
                post_caption="Post Context",
                comment_message="Comment Text",
                reply_message="Reply message",
                comment_link="http://link",
                status="Replied",
                reason="Success"
            )
            logger.info("✅ Google Sheets: log_comment (Replied) successful")
            
            gs.log_comment(
                post_id="post_123",
                post_caption="Post Context",
                comment_message="Skip Test",
                reply_message="",
                comment_link="",
                status="Skipped",
                reason="Audit Test"
            )
            logger.info("✅ Google Sheets: log_comment (Skipped) successful")
            
            # Test Batch Logging
            batch_data = [
                {
                    "post_id": "batch_1",
                    "post_caption": "Batch Ctx 1",
                    "comment_message": "Msg 1",
                    "reply_message": "Reply 1",
                    "comment_link": "http://1",
                    "status": "Replied",
                    "reason": "Batch Test"
                },
                {
                    "post_id": "batch_2",
                    "post_caption": "Batch Ctx 2",
                    "comment_message": "Msg 2",
                    "reply_message": "",
                    "comment_link": "",
                    "status": "Skipped",
                    "reason": "Batch Skip"
                }
            ]
            gs.log_comment_batch(batch_data)
            logger.info("✅ Google Sheets: log_comment_batch successful")

        except Exception as e:
            logger.error(f"❌ Google Sheets: Logging failed: {e}")
    else:
        logger.warning("⚠️ Google Sheets: Not connected (skipping write tests)")

    # 4. Test Gemini Service
    logger.info("--- Testing Gemini Service ---")
    gemini = get_gemini_service()
    if gemini.test_connection():
        response = await gemini.generate_response("สวัสดีค่ะ สั่งของหน่อย", "Context test")
        if response:
            logger.info(f"✅ Gemini Service: Generated response: {response[:50]}...")
        else:
            logger.error("❌ Gemini Service: Empty response")
    else:
        logger.warning("⚠️ Gemini Service: Connection failed")

    logger.info("--- Comprehensive Test Finished ---")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
