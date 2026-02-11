"""
Script to seed dummy status data for dashboard verification.
"""
import json
import time
from datetime import datetime
from pathlib import Path

def save_dummy_status(bot_type, name, file_name, status="active"):
    path = Path(f"data/{file_name}")
    path.parent.mkdir(exist_ok=True)
    
    data = {
        "bot_type": bot_type,
        "bot_name": name,
        "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "processed_count": 123,
        "reply_count": 45,
        "timestamp": time.time(),
        "last_action": "Verified dashboard integration",
        "rate_limits": {
            "page_api": {"usage_percent": 15, "remaining": 85}
        }
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Created {path}")

if __name__ == "__main__":
    save_dummy_status("comment", "Comment Sweeper", "status_comment.json")
    save_dummy_status("chat", "Chat Operator", "status_chat.json")
    save_dummy_status("post", "FB Auto-Poster", "status_post.json", status="offline")
