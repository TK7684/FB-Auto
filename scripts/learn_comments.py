
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from services.facebook_service import get_facebook_service
from services.memory_service import get_memory_service
from services.rate_limiter import RateLimiter
from config.constants import SOCIAL_KEYWORDS

async def learn_from_comments(limit: int = 50):
    """
    Fetch past comments and learn from them.
    
    Args:
        limit: Number of comments to fetch
    """
    rate_limiter = RateLimiter()
    fb_service = get_facebook_service(rate_limiter)
    memory_service = get_memory_service()
    
    logger.info(f"Starting learning process (limit={limit})...")
    
    # 1. Fetch comments from page feed
    # We fetch page feed first to get post IDs, then comments for those posts
    # For simplicity in this v1, we'll try to get comments from the feed endpoint directly if possible
    # or iterate through recent posts.
    
    # Let's try getting recent posts first
    url = f"{fb_service.base_url}/{fb_service.page_id}/feed"
    params = {
        "access_token": fb_service.page_access_token,
        "limit": 10,
        "fields": "id,message,comments{message,comment_count,like_count,from,comments{message,from,like_count}}"
    }
    
    import requests
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        posts = data.get("data", [])
        learned_count = 0
        
        for post in posts:
            post_id = post.get("id")
            post_message = post.get("message", "")
            
            comments = post.get("comments", {}).get("data", [])
            
            for comment in comments:
                # We are looking for: User Question -> Admin Reply pairs
                user_message = comment.get("message", "")
                user_id = comment.get("from", {}).get("id")
                
                # Check for replies (threaded comments)
                replies = comment.get("comments", {}).get("data", [])
                
                admin_reply = None
                
                # Find reply from page (admin)
                for reply in replies:
                    if reply.get("from", {}).get("id") == fb_service.page_id:
                        admin_reply = reply.get("message")
                        break
                
                if user_message and admin_reply:
                    # Categorize
                    category = "general"
                    
                    # Check for social keywords
                    if any(kw in user_message for kw in SOCIAL_KEYWORDS):
                        category = "social"
                    
                    # Store in memory
                    memory_service.add_memory(user_message, admin_reply, category)
                    logger.info(f"Learned: '{user_message}' -> '{admin_reply}' [{category}]")
                    learned_count += 1
                    
        logger.info(f"Learning complete. Learned {learned_count} new interactions.")
        
    except Exception as e:
        logger.error(f"Error during learning: {e}")

if __name__ == "__main__":
    asyncio.run(learn_from_comments())
