"""
Safe Historical Cleanup Script for D Plus Skin.
Scans past comments (up to 12 months) and replies to relevant inquiries.
Includes safety logic:
1. Public replies only (Private replies have a 7-day limit).
2. Purchase intent filtering.
3. 20-second delay between replies to mimic human behavior.
4. Maximum 30 replies per session to stay safe.
"""

import asyncio
import sys
import os
import time
import random
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import httpx

from config.settings import settings
from utils.filters import is_relevant_post
from services.gemini_service import get_gemini_service
from services.facebook_service import get_facebook_service
from services.rate_limiter import get_rate_limiter
from config.constants import PURCHASE_INTENT_KEYWORDS

# Load environment variables
load_dotenv()

# Configure logging
log_path = Path("logs/historical_cleanup.log")
log_path.parent.mkdir(exist_ok=True)
logger.add(log_path, rotation="10 MB", level="INFO")


from utils.filters import is_relevant_post

def has_buying_intent(text: str) -> bool:
    """Check if the text contains buying intent keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in PURCHASE_INTENT_KEYWORDS)

async def run_cleanup(max_replies: int = 30, post_count: int = 50):
    """
    Search for unreplied comments in the last 'post_count' posts
    and reply to a maximum of 'max_replies' to stay safe.
    """
    logger.info(f"--- Historical Cleanup Started: {datetime.now()} ---")
    logger.info(f"Targets: Up to {post_count} posts, Max {max_replies} replies.")
    
    page_id = settings.facebook_page_id
    access_token = settings.facebook_page_access_token
    
    if not page_id or not access_token:
        logger.error("Missing Facebook configuration.")
        return

    # Initialize Services
    gemini_service = get_gemini_service()
    facebook_service = get_facebook_service(get_rate_limiter())

    replies_sent = 0

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Fetch Posts with pagination
        # Note: facebook_graph_api_url already includes the version (e.g., https://graph.facebook.com/v19.0)
        url = f"{settings.facebook_graph_api_url}/{page_id}/feed"
        params = {
            "access_token": access_token,
            "limit": post_count,
            "fields": "id,message,created_time,comments{id,message,from,created_time,comments{from,message}}"
        }
        
        try:
            resp = await client.get(url, params=params)
            data = resp.json()
            
            if "error" in data:
                logger.error(f"FB API error: {data['error']['message']}")
                return

            posts = data.get("data", [])
            logger.info(f"Retrieved {len(posts)} posts for analysis.")

            for post in posts:
                if replies_sent >= max_replies:
                    logger.warning("Reached maximum allowed replies for this session. Stopping for safety.")
                    break

                post_id = post.get("id")
                post_context = post.get("message", "Producl description not available.")
                
                # FILTER: Check if post is relevant
                if not is_relevant_post(post_context):
                    first_line = post_context.split('\n')[0][:50]
                    logger.info(f"Skipping irrelevant post {post_id}: '{first_line}...'")
                    continue
                
                comments = post.get("comments", {}).get("data", [])

                for comment in comments:
                    if replies_sent >= max_replies:
                        break

                    comment_id = comment.get("id")
                    user_msg = comment.get("message", "")
                    user_id = comment.get("from", {}).get("id")
                    user_name = comment.get("from", {}).get("name", "Unknown")

                    # Skip own comments
                    if user_id == page_id:
                        continue

                    # Check for existing admin reply
                    replies = comment.get("comments", {}).get("data", [])
                    if any(r.get("from", {}).get("id") == page_id for r in replies):
                        continue

                    # Check intent
                    if not has_buying_intent(user_msg):
                        continue

                    logger.info(f"Found match: {user_name} said '{user_msg[:30]}...'")
                    
                    # Generate AI Reply
                    try:
                        reply_text = await gemini_service.generate_reply(
                            comment_text=user_msg,
                            post_caption=post_context,
                            reply_mode="public_link" # Force public for old posts
                        )

                        if reply_text:
                            # 20-30s SAFETY DELAY (Mimics human)
                            delay = random.uniform(20.0, 45.0)
                            logger.info(f"Waiting {delay:.1f}s before replying (Anti-Spam Safety)...")
                            await asyncio.sleep(delay)

                            # Send PUBLIC reply
                            success = await facebook_service.send_comment_reply(comment_id, reply_text)
                            if success:
                                replies_sent += 1
                                # Construct Comment Link
                                # Pattern: https://www.facebook.com/{page_id}/posts/{post_id}?comment_id={comment_id}
                                # However, post_id from feed sometimes contains user_id_post_id.
                                # A safer generic link is https://www.facebook.com/{post_id}?comment_id={comment_id}
                                comment_link = f"https://www.facebook.com/{post_id}?comment_id={comment_id}"
                                
                                logger.info(f"✓ Success ({replies_sent}/{max_replies}): Replied to {user_name}")
                                logger.info(f"  > Link: {comment_link}")
                                logger.info(f"  > Comment: {user_msg[:50]}...")
                        
                    except Exception as e:
                        logger.error(f"Error in reply gen: {e}")

            logger.info(f"--- Cleanup Complete! Sent {replies_sent} replies. ---")

        except Exception as e:
            import traceback
            logger.error(f"Cleanup failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    # We set a low limit by default (30) to ensure we NEVER violate FB policies in one go.
    # The user can run it multiple times if they have thousands of comments.
    asyncio.run(run_cleanup(max_replies=30, post_count=50))
