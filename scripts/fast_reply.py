"""
Fast Reply Bot (The "Fast Loop").
Scans only the most recent posts (3-5) for new comments and replies immediately.
Includes "Smart Sleep" and randomized delays for human-like behavior.
"""

import asyncio
import sys
import os
import random
import time
from pathlib import Path
from datetime import datetime
import pytz
from loguru import logger
import httpx
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from config.settings import settings
from utils.filters import is_relevant_post, is_ignored_user
from services.gemini_service import get_gemini_service
from services.facebook_service import get_facebook_service
from services.rate_limiter import get_rate_limiter
from services.knowledge_base import get_knowledge_base
from services.status_logger import get_status_logger
from services.sheets_logger import log_to_sheet
from config.constants import PURCHASE_INTENT_KEYWORDS

# Load environment variables
load_dotenv()

# Configure logging
log_path = Path("logs/fast_reply.log")
log_path.parent.mkdir(exist_ok=True)

def bangkok_time(record):
    """Patcher to set log time to Asia/Bangkok."""
    tz = pytz.timezone("Asia/Bangkok")
    record["extra"]["timestamp"] = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    return record

logger.configure(patcher=bangkok_time)
logger.add(log_path, rotation="10 MB", level="INFO", format="{extra[timestamp]} | {level: <8} | {message}")
# Also log to monitor.log so dashboard can display our logs
logger.add("logs/monitor.log", rotation="10 MB", level="INFO", format="{extra[timestamp]} | {level: <8} | [FastReply] {message}")

# --- Configuration ---
SCAN_LIMIT = 3               # Only scan last 3 posts
MAX_REPLIES_PER_LOOP = 5     # Max replies per single pass (safety)
BASE_SLEEP_SECONDS = 30      # Standard poll interval
ACTIVE_SLEEP_SECONDS = 10    # Faster poll if we just replied (conversation mode)
ERROR_SLEEP_SECONDS = 60     # Wait on error

def has_buying_intent(text: str) -> bool:
    """Check if the text contains buying intent keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in PURCHASE_INTENT_KEYWORDS)

async def fast_reply_loop():
    logger.info("🚀 Fast Responder Bot STARTED")
    logger.info(f"   Target: Last {SCAN_LIMIT} posts")
    logger.info(f"   Rate Limit: Max {MAX_REPLIES_PER_LOOP} replies/loop")
    
    page_id = settings.facebook_page_id
    access_token = settings.facebook_page_access_token

    if not page_id or not access_token:
        logger.error("❌ Missing Facebook configuration!")
        return

    # Initialize Services
    gemini_service = get_gemini_service()
    facebook_service = get_facebook_service(get_rate_limiter())
    
    # Initialize RAG (Safe mode)
    knowledge_base = None
    try:
        knowledge_base = get_knowledge_base(settings.chroma_persist_dir)
        # Ensure products are loaded
        csv_path = Path("data/products.csv")
        if csv_path.exists():
            knowledge_base.load_products_from_csv(str(csv_path))
        logger.info(f"✓ RAG Loaded")
    except Exception as e:
        logger.warning(f"⚠ RAG Load Failed: {e}")

    status_logger = get_status_logger()
    consecutive_errors = 0
    just_replied = False
    total_processed = 0
    total_replies = 0

    while True:
        try:
            # Smart Sleep Logic
            sleep_time = ACTIVE_SLEEP_SECONDS if just_replied else BASE_SLEEP_SECONDS
            # Add small jitter to avoid exact patterns
            sleep_time += random.uniform(-2, 5) 
            
            logger.info(f"💤 Sleeping {sleep_time:.1f}s...")
            await asyncio.sleep(sleep_time)

            replies_in_this_loop = 0
            just_replied = False

            async with httpx.AsyncClient(timeout=30.0) as client:
                # 1. Fetch recent posts
                url = f"{settings.facebook_graph_api_url}/{page_id}/feed"
                params = {
                    "access_token": access_token,
                    "limit": SCAN_LIMIT,
                    "fields": "id,message,created_time,comments{id,message,from,created_time,comments{from,message}}"
                }
                
                resp = await client.get(url, params=params)
                
                if resp.status_code == 400 or resp.status_code == 403:
                     # PANIC SWITCH - Rate Limit or Auth Error
                    logger.error(f"⛔ CRITICAL API ERROR {resp.status_code}: {resp.text}")
                    logger.warning("⏳ Entering COOL DOWN mode (60 mins)...")
                    await asyncio.sleep(3600)
                    continue

                if resp.status_code != 200:
                    logger.error(f"API Error {resp.status_code}: {resp.text}")
                    consecutive_errors += 1
                    await asyncio.sleep(ERROR_SLEEP_SECONDS)
                    continue

                data = resp.json()
                consecutive_errors = 0
                posts = data.get("data", [])
                total_processed += len(posts)

                # Update dashboard status
                status_logger.update_bot_status(
                    bot_type="comment",
                    bot_name="Fast Responder",
                    status="active",
                    processed_count=total_processed,
                    reply_count=total_replies,
                    last_action=f"Scanning {len(posts)} posts"
                )

                for post in posts:
                    if replies_in_this_loop >= MAX_REPLIES_PER_LOOP:
                        break

                    post_id = post.get("id")
                    post_context = post.get("message", "")
                    
                    if not is_relevant_post(post_context):
                        continue

                    comments = post.get("comments", {}).get("data", [])
                    
                    for comment in comments:
                        if replies_in_this_loop >= MAX_REPLIES_PER_LOOP:
                            break
                            
                        comment_id = comment.get("id")
                        user_msg = comment.get("message", "")
                        user_id = comment.get("from", {}).get("id")
                        
                        # --- FILTERS ---
                        if user_id == page_id: continue # Self
                        if is_ignored_user(comment.get("from", {}).get("name", "")): continue
                        
                        # Check if already replied
                        replies = comment.get("comments", {}).get("data", [])
                        if any(r.get("from", {}).get("id") == page_id for r in replies):
                            continue # Already replied

                        # Check intent
                        if not has_buying_intent(user_msg):
                            continue

                        # --- FOUND TARGET ---
                        logger.info(f"🎯 New Comment: {user_msg[:30]}...")

                        # RAG Context
                        context_text = ""
                        if knowledge_base:
                            try:
                                query = f"{user_msg} {post_context[:50]}"
                                context_text = knowledge_base.generate_context(query, top_products=1, top_qa=1)
                            except: pass

                        # Generate Reply
                        reply_text = await gemini_service.generate_reply(
                            comment_text=user_msg,
                            post_caption=post_context,
                            reply_mode="public_link",
                            context=context_text
                        )

                        if reply_text:
                            # ⚠️ SAFETY DELAY before posting (Human-like)
                            # 5-15 seconds reaction time is fast but human
                            delay = random.uniform(5.0, 15.0)
                            logger.info(f"   ⏳ Typing... ({delay:.1f}s)")
                            await asyncio.sleep(delay)

                            success = await facebook_service.send_comment_reply(comment_id, reply_text)
                            if success:
                                replies_in_this_loop += 1
                                total_replies += 1
                                just_replied = True
                                logger.info(f"   ✅ Replied to {comment_id}")
                                
                                # Log activity for dashboard
                                status_logger.log_activity(
                                    bot_name="Fast Responder",
                                    action="comment_reply",
                                    user_name=comment.get("from", {}).get("name", "Unknown"),
                                    user_message=user_msg,
                                    bot_reply=reply_text,
                                    comment_id=comment_id
                                )
                                
                                # Log to Google Sheets (fire-and-forget)
                                log_to_sheet(
                                    bot_name="Fast Responder",
                                    action="comment_reply",
                                    user_name=comment.get("from", {}).get("name", "Unknown"),
                                    user_message=user_msg,
                                    bot_reply=reply_text,
                                    comment_id=comment_id,
                                    post_id=post_id,
                                    page_id=page_id,
                                    status="success"
                                )

                                # Learn (Fire and forget)
                                try:
                                    if knowledge_base:
                                        knowledge_base.add_qa_pair(user_msg, reply_text, "comment")
                                except: pass
                            else:
                                logger.error("   ❌ Failed to send reply")
                                log_to_sheet(
                                    bot_name="Fast Responder",
                                    action="comment_reply",
                                    user_name=comment.get("from", {}).get("name", "Unknown"),
                                    user_message=user_msg,
                                    comment_id=comment_id,
                                    post_id=post_id,
                                    page_id=page_id,
                                    status="error"
                                )

        except Exception as e:
            logger.error(f"💥 LOOP CRASH: {e}")
            await asyncio.sleep(ERROR_SLEEP_SECONDS)

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(fast_reply_loop())
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
