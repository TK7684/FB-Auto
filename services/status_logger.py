"""
Shared Status Logger for Dashboard Integration.

Updates status files (`data/status_*.json`) and activity log (`data/activity_log.json`)
so the Dashboard can display real-time bot metrics.
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import pytz


DATA_DIR = Path("data")
ACTIVITY_LOG = DATA_DIR / "activity_log.json"
MAX_ACTIVITY_ITEMS = 50


class StatusLogger:
    """Thread-safe status/activity logger for the Dashboard."""

    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self._lock = threading.Lock()

    def update_bot_status(
        self,
        bot_type: str,
        bot_name: str,
        status: str = "active",
        processed_count: int = 0,
        reply_count: int = 0,
        last_action: str = "",
        extra: Optional[Dict] = None
    ):
        """Update the status file for a specific bot type."""
        tz = pytz.timezone("Asia/Bangkok")
        now = datetime.now(tz)

        data = {
            "bot_type": bot_type,
            "bot_name": bot_name,
            "last_run": now.strftime("%Y-%m-%d %H:%M:%S"),
            "last_active": now.strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "processed_count": processed_count,
            "reply_count": reply_count,
            "timestamp": time.time(),
            "last_action": last_action,
            "rate_limits": self._get_rate_limit_usage()
        }

        if extra:
            data.update(extra)

        path = DATA_DIR / f"status_{bot_type}.json"
        with self._lock:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    def log_activity(
        self,
        bot_name: str,
        action: str,
        user_name: str = "",
        user_message: str = "",
        bot_reply: str = "",
        comment_id: str = "",
        status: str = "success"
    ):
        """Append an activity item to the activity log (capped at MAX_ACTIVITY_ITEMS)."""
        tz = pytz.timezone("Asia/Bangkok")
        now = datetime.now(tz)

        item = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "ts": time.time(),
            "bot": bot_name,
            "action": action,
            "user": user_name,
            "message": user_message[:100] if user_message else "",
            "reply": bot_reply[:100] if bot_reply else "",
            "comment_id": comment_id,
            "status": status
        }

        with self._lock:
            try:
                activities = self._load_activities()
                activities.insert(0, item)
                activities = activities[:MAX_ACTIVITY_ITEMS]

                with open(ACTIVITY_LOG, "w", encoding="utf-8") as f:
                    json.dump(activities, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    def _load_activities(self) -> List[Dict]:
        """Load existing activity log."""
        if ACTIVITY_LOG.exists():
            try:
                with open(ACTIVITY_LOG, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _get_rate_limit_usage(self) -> Dict:
        """Read current rate limit stats for dashboard display."""
        rate_file = DATA_DIR / "rate_limits.json"
        try:
            if rate_file.exists():
                with open(rate_file, "r") as f:
                    state = json.load(f)
                used = state.get("comments_this_hour", 0)
                return {
                    "page_api": {
                        "usage_percent": min(100, int((used / 60) * 100)),
                        "remaining": max(0, 60 - used)
                    }
                }
        except Exception:
            pass
        return {"page_api": {"usage_percent": 0, "remaining": 60}}


# Singleton
_instance: Optional[StatusLogger] = None

def get_status_logger() -> StatusLogger:
    global _instance
    if _instance is None:
        _instance = StatusLogger()
    return _instance
