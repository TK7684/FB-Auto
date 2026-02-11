import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import json

class GoogleSheetService:
    """
    Service to log bot activity to Google Sheets.
    """
    
    SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    SHEET_ID = "1TPv93ZxOHLqvUWcrnZhXpx1HCjhjdQkWEsSCxjO94qs"
    
    def __init__(self, key_file_path: str = "service_account.json"):
        self.key_file_path = key_file_path
        self.client = None
        self.sheet = None
        self.connected = False
        self._connect()

    def _connect(self):
        """authenticate and connect to Google Sheets"""
        if not os.path.exists(self.key_file_path):
            logger.warning(f"Google Sheets Service Account file not found: {self.key_file_path}")
            return

        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.key_file_path, self.SCOPE)
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(self.SHEET_ID)
            self.connected = True
            logger.info("✓ Connected to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            self.connected = False

    def _get_bangkok_time(self) -> str:
        tz = pytz.timezone("Asia/Bangkok")
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def log_comment(self, post_id, post_caption, comment_message, reply_message, comment_link, status="Success", reason=""):
        """Log a comment reply to the 'Comment' tab"""
        if not self.connected: 
            return

        try:
            worksheet = self.sheet.worksheet("Comment")
            # Headers: Date/Time, Post ID, Post Caption, Comment, Reply, Link, Status, Reason
            row = [
                self._get_bangkok_time(),
                str(post_id),
                post_caption,
                comment_message,
                reply_message,
                comment_link,
                status,
                reason
            ]
            # Insert at row 2 (preserve header)
            worksheet.insert_row(row, 2)
            logger.debug(f"Logged comment to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to log comment to Sheet: {e}")
            if "RW" not in str(e): # Avoid reconnect loops on write errors
                self._connect()
                raise e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def log_comment_batch(self, rows_data: list):
        """
        Log multiple comments to the 'Comment' tab in one go.
        Args:
            rows_data: List of dicts or tuples containing comment data.
                       Expected keys/order: post_id, post_caption, comment_message, 
                       reply_message, comment_link, status, reason
        """
        if not self.connected or not rows_data:
            return

        try:
            worksheet = self.sheet.worksheet("Comment")
            
            # Prepare rows for insertion
            rows_to_insert = []
            for item in rows_data:
                # Handle both dict and list/tuple input
                if isinstance(item, dict):
                    row = [
                        self._get_bangkok_time(),
                        str(item.get("post_id", "")),
                        item.get("post_caption", ""),
                        item.get("comment_message", ""),
                        item.get("reply_message", ""),
                        item.get("comment_link", ""),
                        item.get("status", "Unknown"),
                        item.get("reason", "")
                    ]
                else:
                    # Assume list/tuple matches order but needs timestamp prepended
                    row = [self._get_bangkok_time()] + list(item)
                
                rows_to_insert.append(row)

            # Insert all rows at once (at row 2)
            worksheet.insert_rows(rows_to_insert, 2)
            logger.info(f"✓ Batch logged {len(rows_to_insert)} comments to Google Sheets")
            
        except Exception as e:
            logger.error(f"Failed to batch log comments: {e}")
            # Try reconnecting once
            if "RW" not in str(e):
                self._connect()
                raise e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def log_chat(self, sender_id, user_message, bot_response):
        """Log a chat message to the 'Chats' tab"""
        if not self.connected:
            return

        try:
            worksheet = self.sheet.worksheet("Chat")
            # Headers: Date/Time, User ID, Message, Reply
            row = [
                self._get_bangkok_time(),
                str(sender_id),
                user_message,
                bot_response
            ]
            worksheet.insert_row(row, 2)
            logger.debug(f"Logged chat to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to log chat to Sheet: {e}")
            self._connect()
            raise e

# Singleton
_google_sheet_service = None

def get_google_sheet_service():
    global _google_sheet_service
    if _google_sheet_service is None:
        _google_sheet_service = GoogleSheetService()
    return _google_sheet_service
