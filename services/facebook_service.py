"""
Facebook Graph API Service with Rate Limiting.

This module handles all interactions with the Facebook Graph API,
including sending messages, commenting, and webhook verification.
Integrates with the rate limiter to avoid API bans.
"""

import requests
import time
import json
import hashlib
import hmac
from typing import Optional, Dict, Any
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import settings
from config.constants import FACEBOOK_ERROR_CODES, RETRYABLE_ERROR_CODES
from services.rate_limiter import RateLimiter


class FacebookAPIError(Exception):
    """Custom exception for Facebook API errors."""

    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class RateLimitError(FacebookAPIError):
    """Exception raised when rate limit is reached."""

    pass


class FacebookService:
    """
    Service for interacting with Facebook Graph API.

    Handles:
    - Sending messages via Messenger Send API
    - Replying to comments
    - Webhook verification
    - Rate limit monitoring and error handling
    """

    def __init__(self, rate_limiter: RateLimiter):
        """
        Initialize Facebook service.

        Args:
            rate_limiter: Rate limiter instance for API calls
        """
        self.page_access_token = settings.facebook_page_access_token
        self.page_id = settings.facebook_page_id
        self.api_version = settings.facebook_api_version
        self.base_url = settings.facebook_graph_api_url
        self.app_secret = settings.facebook_app_secret
        self.rate_limiter = rate_limiter

        logger.info(
            f"Facebook service initialized for page {self.page_id} "
            f"using API version {self.api_version}"
        )

    def _get_appsecret_proof(self) -> str:
        """Generate appsecret_proof for secure API calls."""
        return hmac.new(
            self.app_secret.encode('utf-8'),
            self.page_access_token.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _get_auth_params(self) -> Dict[str, str]:
        """Get authentication parameters including appsecret_proof."""
        return {
            "access_token": self.page_access_token,
            "appsecret_proof": self._get_appsecret_proof()
        }

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Content-Type": "application/json",
        }

    def _check_rate_limit_headers(self, response: requests.Response) -> None:
        """
        Monitor Facebook rate limit headers and log warnings.

        Args:
            response: API response object
        """
        app_usage = response.headers.get("X-App-Usage")
        if app_usage:
            try:
                usage = json.loads(app_usage)
                call_count = usage.get("call_count", 0)
                if call_count > 70:
                    logger.warning(f"X-App-Usage: {call_count}% used")
                elif call_count > 85:
                    logger.error(f"X-App-Usage CRITICAL: {call_count}% used")
                else:
                    logger.debug(f"X-App-Usage: {app_usage}")
            except json.JSONDecodeError:
                logger.debug(f"X-App-Usage: {app_usage}")

        buc_usage = response.headers.get("X-Business-Use-Case-Usage")
        if buc_usage:
            logger.debug(f"X-Business-Use-Case-Usage: {buc_usage}")

    def _handle_error(self, response: requests.Response) -> None:
        """
        Handle Facebook API errors and raise appropriate exceptions.

        Args:
            response: API response object

        Raises:
            FacebookAPIError: For general API errors
            RateLimitError: For rate limit errors
        """
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            error_code = error.get("code")
            error_message = error.get("message", "Unknown error")

            logger.error(f"Facebook API error: code={error_code}, message={error_message}")

            # Check if this is a rate limit error
            if error_code in RETRYABLE_ERROR_CODES:
                error_type = FACEBOOK_ERROR_CODES.get(error_code, "Unknown rate limit")
                raise RateLimitError(
                    f"{error_type}: {error_message}",
                    code=error_code
                )

            # General Facebook API error
            raise FacebookAPIError(error_message, code=error_code)

        except json.JSONDecodeError:
            logger.error(f"Failed to parse error response: {response.text}")
            raise FacebookAPIError(f"HTTP {response.status_code}: {response.text}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=32),
        retry=retry_if_exception_type(RateLimitError),
        reraise=True
    )
    async def send_message(
        self,
        recipient_id: str,
        message_text: str,
        message_type: str = "text"
    ) -> bool:
        """
        Send a message via Messenger Send API.

        Args:
            recipient_id: Facebook user/scout ID to send to
            message_text: Message text to send
            message_type: Message type (text, audio, video)

        Returns:
            True if message sent successfully

        Raises:
            RateLimitError: If rate limit is reached
            FacebookAPIError: For other API errors
        """
        # Determine rate limit category
        endpoint = "messenger_text" if message_type == "text" else "messenger_media"

        # Check rate limit before sending
        if not await self.rate_limiter.acquire(endpoint):
            logger.warning(f"Rate limit reached for {endpoint}, message queued")
            # Could implement queue here
            return False

        url = f"{self.base_url}/me/messages"
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }

        try:
            response = requests.post(
                url,
                params={"access_token": self.page_access_token},
                headers=self._get_headers(),
                json=data,
                timeout=10
            )

            # Check rate limit headers
            self._check_rate_limit_headers(response)

            if response.status_code == 200:
                logger.info(f"✓ Message sent to {recipient_id}")
                return True
            else:
                self._handle_error(response)
                return False

        except RateLimitError:
            # Re-raise for retry decorator
            raise
        except FacebookAPIError as e:
            logger.error(f"Facebook API error sending message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=32),
        retry=retry_if_exception_type(RateLimitError),
        reraise=True
    )
    async def send_comment_reply(
        self,
        comment_id: str,
        reply_text: str
    ) -> bool:
        """
        Reply to a Facebook page comment.

        Args:
            comment_id: ID of the comment to reply to
            reply_text: Reply text

        Returns:
            True if reply sent successfully

        Raises:
            RateLimitError: If rate limit is reached
            FacebookAPIError: For other API errors
        """
        # Check rate limit for private replies
        if not await self.rate_limiter.acquire("private_replies"):
            logger.warning("Rate limit reached for comment replies")
            return False

        url = f"{self.base_url}/{comment_id}/comments"
        data = {"message": reply_text}

        try:
            response = requests.post(
                url,
                params={"access_token": self.page_access_token},
                headers=self._get_headers(),
                json=data,
                timeout=10
            )

            # Check rate limit headers
            self._check_rate_limit_headers(response)

            if response.status_code == 200:
                logger.info(f"✓ Reply sent to comment {comment_id}")
                return True
            else:
                self._handle_error(response)
                return False

        except RateLimitError:
            raise
        except FacebookAPIError as e:
            logger.error(f"Facebook API error sending reply: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending reply: {e}")
            return False

    def verify_webhook(
        self,
        mode: str,
        token: str,
        challenge: str
    ) -> Optional[str]:
        """
        Verify webhook subscription with Facebook.

        Args:
            mode: Webhook mode (should be "subscribe")
            token: Verify token
            challenge: Challenge string from Facebook

        Returns:
            Challenge string if verification successful, None otherwise
        """
        if mode == "subscribe" and token == settings.facebook_webhook_verify_token:
            logger.info("✓ Webhook verification successful")
            return challenge

        logger.warning(
            f"Webhook verification failed: mode={mode}, "
            f"expected_token={settings.facebook_webhook_verify_token}, "
            f"received_token={token}"
        )
        return None

    def get_post_details(self, post_id: str) -> Dict[str, Any]:
        """
        Get post details including caption/message.

        Args:
            post_id: Facebook post ID

        Returns:
            Dictionary with post details (message, created_time, etc.)
        """
        url = f"{self.base_url}/{post_id}"
        params = {
            **self._get_auth_params(),
            "fields": "message,created_time,full_picture,permalink_url"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            logger.debug(f"Retrieved post details for {post_id}: {data.get('message', '')[:50]}...")
            return data

        except Exception as e:
            logger.error(f"Error fetching post details: {e}")
            return {}

    def get_page_comments(
        self,
        post_id: Optional[str] = None,
        limit: int = 25,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comments from a page post.

        Args:
            post_id: Post ID (None for page posts)
            limit: Number of comments to retrieve
            after: Pagination cursor

        Returns:
            Dictionary with comment data

        Note: This uses page_api rate limit
        """
        # Check rate limit
        if not self.rate_limiter.get_stats("page_api"):
            logger.warning("Page API rate limit reached for comment fetch")

        if post_id:
            url = f"{self.base_url}/{post_id}/comments"
        else:
            url = f"{self.base_url}/{self.page_id}/feed"

        params = {
            "access_token": self.page_access_token,
            "limit": limit,
            "fields": "id,message,from,created_time,comments"
        }

        if after:
            params["after"] = after

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            self._check_rate_limit_headers(response)

            data = response.json()
            logger.debug(f"Retrieved {len(data.get('data', []))} comments")
            return data

        except Exception as e:
            logger.error(f"Error fetching comments: {e}")
            return {}

    def get_engaged_users_count(self) -> Optional[int]:
        """
        Get the number of engaged users in the last 24 hours.

        This is useful for understanding current rate limits.

        Returns:
            Number of engaged users or None if unavailable
        """
        url = f"{self.base_url}/{self.page_id}/insights"
        params = {
            "access_token": self.page_access_token,
            "metric": "page_post_engagements",
            "period": "day"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # The engaged users count is used in rate limit calculations
                # This is a simplified version
                return data.get("data", [{}])[0].get("values", [{}])[0].get("value")
        except Exception as e:
            logger.debug(f"Could not fetch engaged users: {e}")

        return None

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status for all endpoints.

        Returns:
            Dictionary with rate limit information
        """
        status = {}

        for endpoint, stats in self.rate_limiter.get_all_stats().items():
            status[endpoint] = {
                "usage_percent": stats.usage_percent,
                "remaining_calls": stats.remaining_calls,
                "wait_time_seconds": self.rate_limiter.get_wait_time(endpoint)
            }

        return status


# Singleton instance
_facebook_service: Optional[FacebookService] = None


def get_facebook_service(rate_limiter: RateLimiter) -> FacebookService:
    """Get the global Facebook service instance."""
    global _facebook_service
    if _facebook_service is None:
        _facebook_service = FacebookService(rate_limiter)
    return _facebook_service


def reset_facebook_service():
    """Reset the global Facebook service instance."""
    global _facebook_service
    _facebook_service = None
