"""
Script to analyze unreplied comments and propose AI responses.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import httpx
from loguru import logger

from config.settings import settings
from services.gemini_service import get_gemini_service

# Load environment variables
load_dotenv()

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

async def analyze_unreplied_comments(limit_posts: int = 5):
    """
    Fetch posts, find unreplied comments, and generate AI proposals.
    """
    logger.info(f"Analyzing last {limit_posts} posts for unreplied comments...")
    
    # 1. Setup Services
    page_id = settings.facebook_page_id
    access_token = settings.facebook_page_access_token
    gemini_service = get_gemini_service()
    
    if not access_token or not page_id:
        logger.error("Missing FACEBOOK_PAGE_ID or FACEBOOK_PAGE_ACCESS_TOKEN")
        return

    # 2. Fetch Posts & Comments via Graph API
    async with httpx.AsyncClient() as client:
        url = f"https://graph.facebook.com/{settings.facebook_api_version}/{page_id}/feed"
        params = {
            "access_token": access_token,
            "limit": limit_posts,
            "fields": "id,message,created_time,comments{id,message,from,created_time,comments{from,message}}"
        }
        
        try:
            resp = await client.get(url, params=params)
            data = resp.json()
            
            if "error" in data:
                logger.error(f"Facebook API Error: {data['error']['message']}")
                return
                
            posts = data.get("data", [])
            unreplied_comments = []
            
            for post in posts:
                post_id = post.get("id")
                post_message = post.get("message", "No text")[:50] + "..."
                
                comments_data = post.get("comments", {}).get("data", [])
                
                for comment in comments_data:
                    comment_id = comment.get("id")
                    user_message = comment.get("message", "")
                    user_name = comment.get("from", {}).get("name", "Unknown")
                    user_id = comment.get("from", {}).get("id")
                    
                    # Check replies
                    replies = comment.get("comments", {}).get("data", [])
                    has_admin_reply = False
                    
                    for reply in replies:
                        reply_from_id = reply.get("from", {}).get("id")
                        if reply_from_id == page_id:
                            has_admin_reply = True
                            break
                    
                    if not has_admin_reply and user_id != page_id:
                        # CHECK FOR BUYING INTENT (Strict Filter)
                        # We only want to analyze/reply to comments with buying intent
                        is_buyer = False
                        user_msg_lower = user_message.lower()
                        # Simple check against known keywords (importing constant would be better but this is a script)
                        buyer_keywords = [
                            "สนใจ", "สั่งซื้อยังไง", "สั่งที่ไหน", "ราคา", "ซื้อยังไง",
                            "อยากได้", "สั่งยังไง", "ราคาเท่าไหร่", "กี่บาท", "ส่งยังไง",
                            "จัดส่งยังไง", "เอาค่ะ", "เอาครับ", "สนใจค่ะ", "สนใจครับ",
                            "ซื้อที่ไหน", "สั่งได้ไหม", "มีไหม", "ยังมีไหม", "หมดยัง",
                            "เท่าไหร่", "ซื้อ", "สั่ง", "จ่าย", "โอน", "เอา", "ขอ", 
                            "จะเอา", "รับ", "เก็บเงินปลายทาง", "cod", "ส่งฟรี", "มีส่วนลด", 
                            "โปร", "ถูก", "แพง", "ว1", "v1", "cf", "f"
                        ]
                        
                        if any(kw in user_msg_lower for kw in buyer_keywords):
                            is_buyer = True
                        
                        if is_buyer:
                            unreplied_comments.append({
                                "type": "comment",
                                "post_id": post_id,
                                "post_context": post.get("message", ""),
                                "comment_id": comment_id,
                                "user_name": user_name,
                                "message": user_message
                            })
                        
            logger.info(f"Found {len(unreplied_comments)} unreplied comments.")
            
            # 3. Analyze & Generate Decisions
            report_lines = []
            report_lines.append("# 💬 Unreplied Comments Analysis & Proposals")
            report_lines.append(f"Analyzing last {limit_posts} posts...")
            
            if not unreplied_comments:
                report_lines.append("\n✅ **No unreplied comments found.** Good job!")
            else:
                report_lines.append(f"\nFound **{len(unreplied_comments)}** unreplied comments.\n")
                
                for i, item in enumerate(unreplied_comments, 1):
                    report_lines.append(f"### Comment {i}")
                    report_lines.append(f"**Post Conflict:** `{item['post_context'][:60]}...`")
                    report_lines.append(f"**User:** {item['user_name']}")
                    report_lines.append(f"**Message:** \"{item['message']}\"")
                    
                    import random
                    
                    # STRATEGY: 80% Public Link, 20% Private Reply
                    # But if user specifically asks for "DM" or "inbox", force private.
                    force_private = any(kw in item['message'].lower() for kw in ["ทักแชท", "inbox", "dm", "ส่วนตัว"])
                    
                    if force_private:
                        reply_mode = "private_reply"
                    else:
                        reply_mode = "public_link" if random.random() < 0.8 else "private_reply"

                    print(f"Generating ({reply_mode}) for comment {i}...", end="", flush=True)
                    
                    # Generate AI Reply
                    draft_reply = await gemini_service.generate_reply(
                        comment_text=item['message'],
                        post_caption=item['post_context'],
                        reply_mode=reply_mode
                    )
                    
                    report_lines.append(f"\n> **💡 Proposed Reply ({reply_mode}):**\n> \"{draft_reply}\"")
                    
                    # EXECUTE REPLY (Optional - typically we might want a confirmation step, 
                    # but for this script we might just log it or auto-send if confident.
                    # For now, let's just Log it as a proposal. 
                    # If we wanted to send:
                    # if reply_mode == "private_reply":
                    #     await facebook_service.send_private_reply(item['comment_id'], draft_reply)
                    #     # We also need to reply publicly to say "sent DM" usually? 
                    #     # Actually Facebook rules say you reply publicly OR privately. 
                    #     # If private, we might not need a public reply, or just a generic "Sent!"
                    # else:
                    #     await facebook_service.send_comment_reply(item['comment_id'], draft_reply)
                    
                    report_lines.append("\n---\n")
                    print(" Done.")

            # Save report
            report_path = Path("latest_report.md")
            report_path.write_text("\n".join(report_lines), encoding="utf-8")
            print(f"\n✅ Report saved to {report_path.absolute()}")

                
        except Exception as e:
            logger.error(f"Error analyzing comments: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_unreplied_comments())
