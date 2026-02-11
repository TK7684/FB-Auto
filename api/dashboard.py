"""
Dashboard API endpoints for checking bot status, logs, and recent activity.
"""

from fastapi import APIRouter
from pathlib import Path
import json
from typing import List
from loguru import logger

router = APIRouter()

STATUS_FILES = {
    "comment": Path("data/status_comment.json"),
    "chat": Path("data/status_chat.json"),
    "post": Path("data/status_post.json")
}
LOG_FILE = Path("logs/monitor.log")
ACTIVITY_LOG = Path("data/activity_log.json")


def _read_json(path: Path):
    """Read a JSON file safely, return None on failure."""
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


@router.get("/stats", summary="Get aggregated bot stats")
async def get_stats():
    """Get aggregated stats for all bots."""
    
    bots = []
    total_processed = 0
    total_replies = 0
    api_usage = 0
    
    # Comment Bot
    comment_data = _read_json(STATUS_FILES["comment"])
    if comment_data:
        bots.append(comment_data)
        total_processed += comment_data.get("processed_count", 0)
        total_replies += comment_data.get("reply_count", 0)
        if "rate_limits" in comment_data:
            stats = comment_data["rate_limits"].get("page_api", {})
            api_usage = stats.get("usage_percent", 0)
    else:
        bots.append({"bot_name": "Comment Sweeper", "status": "offline", "bot_type": "comment"})

    # Chat Bot
    chat_data = _read_json(STATUS_FILES["chat"])
    if chat_data:
        bots.append(chat_data)
    else:
        bots.append({"bot_name": "Chat Operator", "status": "offline", "bot_type": "chat"})

    # Post Bot
    post_data = _read_json(STATUS_FILES["post"])
    if post_data:
        bots.append(post_data)
    else:
        bots.append({"bot_name": "FB Auto-Poster", "status": "offline", "bot_type": "post"})

    return {
        "bots": bots,
        "processed_count": total_processed,
        "reply_count": total_replies,
        "api_usage": api_usage,
        "system_status": "active" if any(b.get("status") == "active" for b in bots) else "offline"
    }


@router.get("/activity", summary="Get recent activity feed")
async def get_activity(limit: int = 20):
    """Get the last N activity items for the 'Recent Activity' dashboard section."""
    data = _read_json(ACTIVITY_LOG)
    if not data:
        return {"activities": []}
    return {"activities": data[:limit]}


@router.get("/logs", summary="Get recent logs")
async def get_logs(lines: int = 200):
    """Get the last N lines from the monitor log."""
    # Try multiple log sources
    log_sources = [
        Path("logs/scrape.log"),   # Inbox Scraper logs
        Path("logs/monitor.log"),
        Path("logs/fast_reply.log"),
        Path("logs/app.log"),
    ]
    
    all_log_lines = []
    for log_path in log_sources:
        if log_path.exists():
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    # Read all lines then take last 1000 to ensure we have enough buffer
                    # before sorting and slicing the final N lines
                    file_lines = f.readlines()
                    all_log_lines.extend(file_lines[-1000:])
            except Exception as e:
                logger.error(f"Error reading {log_path}: {e}")

    # Sort by timestamp (best effort) and take last N
    all_log_lines.sort()
    last_lines = all_log_lines[-lines:]
    
    return {"logs": [line.strip() for line in last_lines if line.strip()]}
