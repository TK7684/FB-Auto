"""
24/7 Facebook Comment Monitor for D Plus Skin.
This script periodically polls the Facebook Graph API for unreplied comments
and automatically responds using the Gemini AI service.
"""

import asyncio
import sys
import os
import time
from pathlib import Path
from datetime import datetime
import pytz
from loguru import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import httpx

from config.settings import settings
from services.gemini_service import get_gemini_service
from services.facebook_service import get_facebook_service
from services.rate_limiter import get_rate_limiter
import json

STATUS_FILE = Path("data/status_comment.json")

def save_status(data: dict):
    """Save monitor status to JSON file."""
    try:
        STATUS_FILE.parent.mkdir(exist_ok=True)
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save status: {e}")

# Load environment variables
load_dotenv()

# Configure logging for 24/7 monitor
def bangkok_time(record):
    """Patcher to set log time to Asia/Bangkok."""
    tz = pytz.timezone("Asia/Bangkok")
    record["extra"]["timestamp"] = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    return record

log_path = Path("logs/monitor.log")
log_path.parent.mkdir(exist_ok=True)
logger.remove() # Remove default handler
logger.add(sys.stdout, format="<green>{extra[timestamp]}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.configure(patcher=bangkok_time)
logger.add(log_path, rotation="10 MB", level="INFO", format="{extra[timestamp]} | {level: <8} | {name}:{function}:{line} - {message}")

# Buying Intent Keywords (Thai)
BUYER_KEYWORDS = [
    "สนใจ", "สั่งซื้อยังไง", "สั่งที่ไหน", "ราคา", "ซื้อยังไง",
    "อยากได้", "สั่งยังไง", "ราคาเท่าไหร่", "กี่บาท", "ส่งยังไง",
    "จัดส่งยังไง", "เอาค่ะ", "เอาครับ", "สนใจค่ะ", "สนใจครับ",
    "ซื้อที่ไหน", "สั่งได้ไหม", "มีไหม", "ยังมีไหม", "หมดยัง",
    "เท่าไหร่", "ซื้อ", "สั่ง", "จ่าย", "โอน", "เอา", "ขอ", 
    "จะเอา", "รับ", "เก็บเงินปลายทาง", "cod", "ส่งฟรี", "มีส่วนลด", 
    "โปร", "ถูก", "แพง", "ว1", "v1", "cf", "f"
]

def has_buying_intent(text: str) -> bool:
    """Check if the text contains buying intent keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in BUYER_KEYWORDS)

async def run_monitor_cycle(limit_posts: int = 5):
    """Fetch unreplied comments and reply to them."""
    logger.info(f"Monitor Cycle Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    page_id = settings.facebook_page_id
    access_token = settings.facebook_page_access_token
    
    if not page_id or not access_token:
        logger.error("Missing Facebook configuration in .env")
        return

    # Initialize Services
    rate_limiter = get_rate_limiter()
    gemini_service = get_gemini_service()
    facebook_service = get_facebook_service(rate_limiter)

    async with httpx.AsyncClient() as client:
        # 1. Fetch Posts and Comments
        url = f"{settings.facebook_graph_api_url}/{settings.facebook_api_version}/{page_id}/feed"
        params = {
            "access_token": access_token,
            "limit": limit_posts,
            "fields": "id,message,created_time,comments{id,message,from,created_time,comments{from,message}}"
        }
        
        try:
            resp = await client.get(url, params=params)
            data = resp.json()
            
            if "error" in data:
                logger.error(f"Facebook Graph API Error: {data['error']['message']}")
                return
                
            posts = data.get("data", [])
            processed_count = 0
            reply_count = 0
            
            for post in posts:
                post_id = post.get("id")
                post_context = post.get("message", "Producl description not available.")
                comments_data = post.get("comments", {}).get("data", [])
                
                for comment in comments_data:
                    comment_id = comment.get("id")
                    user_message = comment.get("message", "")
                    user_id = comment.get("from", {}).get("id")
                    user_name = comment.get("from", {}).get("name", "Unknown")
                    
                    # Skip if it's the page's own comment
                    if user_id == page_id:
                        continue
                        
                    # 2. Check for administrative replies
                    replies = comment.get("comments", {}).get("data", [])
                    has_admin_reply = False
                    for reply in replies:
                        if reply.get("from", {}).get("id") == page_id:
                            has_admin_reply = True
                            break
                    
                    if has_admin_reply:
                        continue
                        
                    # 3. Check for Buying Intent
                    if not has_buying_intent(user_message):
                        logger.debug(f"Skipping comment {comment_id} - No buying intent: {user_message[:30]}")
                        continue
                    
                    logger.info(f"Processing buying intent from {user_name}: {user_message[:50]}...")
                    processed_count += 1
                    
                    # 4. Generate Strategy (Public Link vs Private Reply)
                    # Force private if user asks for it
                    force_private = any(kw in user_message.lower() for kw in ["ทักแชท", "inbox", "dm", "ส่วนตัว"])
                    
                    import random
                    if force_private:
                        reply_mode = "private_reply"
                    else:
                        # 80/20 Strategy: 80% Public Link (social proof) / 20% Private
                        reply_mode = "public_link" if random.random() < 0.8 else "private_reply"
                    
                    # 5. Generate AI Reply
                    try:
                        reply_text = await gemini_service.generate_reply(
                            comment_text=user_message,
                            post_caption=post_context,
                            reply_mode=reply_mode
                        )
                        
                        if not reply_text:
                            logger.warning(f"Gemini failed to generate reply for {comment_id}")
                            continue
                            
                        # 6. SEND REPLY
                        if reply_mode == "private_reply":
                            logger.info(f"Sending PRIVATE reply to {user_name}...")
                            success = await facebook_service.send_private_reply(comment_id, reply_text)
                            if success:
                                # Also send a short public comment saying "Sent DM!"
                                await facebook_service.send_comment_reply(comment_id, "ส่งข้อมูลให้ทาง Inbox แล้วนะคะคุณลูกค้า 😊")
                        else:
                            logger.info(f"Sending PUBLIC reply to {user_name}...")
                            success = await facebook_service.send_comment_reply(comment_id, reply_text)
                        
                        if success:
                            reply_count += 1
                            logger.info(f"✓ Responded to {user_name} via {reply_mode}")
                        
                    except Exception as e:
                        logger.error(f"Error responding to comment {comment_id}: {e}")

            # Save Status
            rate_limit_stats = rate_limiter.get_all_stats()
            # Convert objects to dicts
            rl_data = {}
            for k, v in rate_limit_stats.items():
                rl_data[k] = {"usage_percent": v.usage_percent, "remaining": v.remaining_calls}
            
            status_data = {
                "bot_type": "comment",
                "bot_name": "Comment Sweeper",
                "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "active",
                "processed_count": processed_count,
                "reply_count": reply_count,
                "rate_limits": rl_data,
                "timestamp": time.time()
            }
            save_status(status_data)

            logger.info(f"Cycle Complete: Processed {processed_count} relevant comments, sent {reply_count} replies.")
            
        except Exception as e:
            logger.error(f"Monitor cycle exception: {e}")

async def main():
    """Main loop or single run for monitoring."""
    import argparse
    parser = argparse.ArgumentParser(description="24/7 Facebook Monitor")
    parser.add_argument("--once", action="store_true", help="Run once and exit (for GitHub Actions)")
    args = parser.parse_args()

    logger.info("=== D Plus Skin Monitor Initializing ===")
    
    # 1. Initialize Knowledge Base and load data if empty
    kb = get_knowledge_base()
    if kb.get_product_count() == 0:
        csv_path = Path("data/products.csv")
        if csv_path.exists():
            logger.info("Loading products into Knowledge Base...")
            kb.load_products_from_csv(str(csv_path))
        else:
            logger.warning("Products CSV not found! Monitor might not provide product info.")

    interval = int(os.getenv("MONITOR_INTERVAL_SECONDS", "300"))
    
    if args.once:
        logger.info("Running single monitor cycle...")
        await run_monitor_cycle(limit_posts=int(os.getenv("MONITOR_POST_LIMIT", "10")))
        logger.info("Single cycle complete. exiting.")
        return

    while True:
        try:
            await run_monitor_cycle(limit_posts=int(os.getenv("MONITOR_POST_LIMIT", "10")))
        except Exception as e:
            logger.error(f"Critical error in main loop: {e}")
            
        logger.info(f"Sleeping for {interval} seconds...")
        await asyncio.sleep(interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user.")
    except Exception as e:
        logger.critical(f"Monitor crashed: {e}")
