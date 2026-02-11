"""
Google Sheets Logger for Bot Activity.

Appends every comment reply and action as a new row to the configured Google Sheet.
Each row includes: timestamp, bot name, action, user, comment/message, bot reply,
comment link, post link, and status.

Sheet: https://docs.google.com/spreadsheets/d/1TPv93ZxOHLqvUWcrnZhXpx1HCjhjdQkWEsSCxjO94qs
"""

import threading
from datetime import datetime
from typing import Optional
from pathlib import Path
from loguru import logger
import pytz

# Lazy-loaded to avoid import cost if Sheets isn't used
_gspread_client = None
_worksheet = None
_lock = threading.Lock()

SPREADSHEET_ID = "1TPv93ZxOHLqvUWcrnZhXpx1HCjhjdQkWEsSCxjO94qs"
SERVICE_ACCOUNT_FILE = Path("service_account.json")

# Column header row (auto-created if Sheet1 is empty)
HEADERS = [
    "Timestamp",
    "Bot",
    "Action",
    "User",
    "User Message",
    "Bot Reply",
    "Comment Link",
    "Post Link",
    "Status",
]


def _get_worksheet():
    """Lazy-init gspread client and return the first worksheet."""
    global _gspread_client, _worksheet
    if _worksheet is not None:
        return _worksheet

    try:
        import gspread
        _gspread_client = gspread.service_account(filename=str(SERVICE_ACCOUNT_FILE))
        sheet = _gspread_client.open_by_key(SPREADSHEET_ID)
        _worksheet = sheet.sheet1

        # Ensure headers exist
        existing = _worksheet.row_values(1)
        if not existing or existing[0] != HEADERS[0]:
            _worksheet.update("A1", [HEADERS])
            logger.info("Google Sheets: headers written.")

        logger.info(f"Google Sheets logger connected to spreadsheet.")
        return _worksheet

    except Exception as e:
        logger.error(f"Google Sheets init failed: {e}")
        return None


def log_to_sheet(
    bot_name: str,
    action: str,
    user_name: str = "",
    user_message: str = "",
    bot_reply: str = "",
    comment_id: str = "",
    post_id: str = "",
    page_id: str = "",
    status: str = "success",
):
    """
    Append a row to Google Sheets (fire-and-forget, thread-safe).

    Args:
        bot_name: Which bot is logging (e.g. "Fast Responder", "Deep Cleaner")
        action: Action type (e.g. "comment_reply", "dm_reply", "scan")
        user_name: Facebook user's display name
        user_message: The user's comment/message text
        bot_reply: The generated reply text
        comment_id: Facebook comment ID (used to build traceability link)
        post_id: Facebook post ID
        page_id: Facebook page ID
        status: Result status ("success", "error", "skipped")
    """

    def _do_append():
        with _lock:
            try:
                ws = _get_worksheet()
                if ws is None:
                    return

                tz = pytz.timezone("Asia/Bangkok")
                now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

                # Build traceable links
                comment_link = ""
                post_link = ""
                if post_id:
                    post_link = f"https://www.facebook.com/{post_id}"
                    if comment_id:
                        comment_link = f"https://www.facebook.com/{post_id}?comment_id={comment_id}"

                row = [
                    now,
                    bot_name,
                    action,
                    user_name[:50] if user_name else "",
                    user_message[:200] if user_message else "",
                    bot_reply[:200] if bot_reply else "",
                    comment_link,
                    post_link,
                    status,
                ]

                ws.insert_rows([row], row=2, value_input_option="USER_ENTERED")

            except Exception as e:
                logger.error(f"Google Sheets log failed: {e}")

    # Fire and forget in a background thread so it never blocks the bot loop
    t = threading.Thread(target=_do_append, daemon=True)
    t.start()
