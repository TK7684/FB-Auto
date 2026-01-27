"""
Rate Limiter Service for Facebook API.

This module implements rate limiting to prevent exceeding Facebook API limits
and avoid getting the application banned.

Uses two strategies:
1. Token Bucket Algorithm - for per-second rate limits
2. Sliding Window Algorithm - for hourly rate limits

Rate limits are set at 85% of Facebook's actual limits for safety.
"""

import time
import asyncio
from threading import Lock
from collections import deque
from typing import Dict, Optional, Tuple
from loguru import logger
from dataclasses import dataclass


@dataclass
class RateLimitStats:
    """Statistics for rate limit usage."""
    usage_percent: float
    remaining_calls: int
    reset_time_seconds: Optional[float] = None


class TokenBucket:
    """
    Token Bucket Algorithm for per-second rate limiting.

    Tokens are added at a fixed rate (tokens per second) up to a maximum capacity.
    Each API call consumes one or more tokens.

    This is ideal for rate limits like "250 calls per second".
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens to add per second
            capacity: Maximum number of tokens that can be stored
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_time = time.time()
        self.lock = Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume the specified number of tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_time

            # Add tokens based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + (elapsed * self.rate)
            )
            self.last_time = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            logger.debug(f"Token bucket: {self.tokens:.2f} tokens available, need {tokens}")
            return False

    def get_stats(self) -> RateLimitStats:
        """Get current rate limit statistics."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_time
            current_tokens = min(
                self.capacity,
                self.tokens + (elapsed * self.rate)
            )
            usage_percent = ((self.capacity - current_tokens) / self.capacity) * 100
            remaining = int(current_tokens)

            return RateLimitStats(
                usage_percent=usage_percent,
                remaining_calls=remaining
            )

    def wait_time(self, tokens: int = 1) -> float:
        """
        Calculate seconds to wait before consuming tokens.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds to wait (0 if tokens available now)
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_time
            current_tokens = min(
                self.capacity,
                self.tokens + (elapsed * self.rate)
            )

            if current_tokens >= tokens:
                return 0.0

            # Calculate time needed to accumulate enough tokens
            needed = tokens - current_tokens
            return needed / self.rate


class SlidingWindow:
    """
    Sliding Window Algorithm for hourly/daily rate limits.

    Tracks API calls within a rolling time window.
    This is ideal for rate limits like "700 calls per hour".
    """

    def __init__(self, limit: int, window: int):
        """
        Initialize sliding window.

        Args:
            limit: Maximum number of calls allowed
            window: Time window in seconds
        """
        self.limit = limit
        self.window = window
        self.requests: deque = deque()
        self.lock = Lock()

    def allow_request(self) -> bool:
        """
        Check if a request is allowed under the rate limit.

        Returns:
            True if request is allowed, False if limit reached
        """
        with self.lock:
            now = time.time()

            # Remove requests outside the time window
            while self.requests and now - self.requests[0] > self.window:
                self.requests.popleft()

            if len(self.requests) < self.limit:
                self.requests.append(now)
                return True

            logger.debug(f"Sliding window: {len(self.requests)}/{self.limit} calls")
            return False

    def get_stats(self) -> RateLimitStats:
        """Get current rate limit statistics."""
        with self.lock:
            now = time.time()

            # Remove old requests
            while self.requests and now - self.requests[0] > self.window:
                self.requests.popleft()

            usage_percent = (len(self.requests) / self.limit) * 100
            remaining = self.limit - len(self.requests)

            reset_time = None
            if self.requests:
                reset_time = self.window - (now - self.requests[0])

            return RateLimitStats(
                usage_percent=usage_percent,
                remaining_calls=remaining,
                reset_time_seconds=reset_time
            )

    def wait_time(self) -> float:
        """
        Calculate seconds to wait before next request.

        Returns:
            Seconds to wait (0 if request can be made now)
        """
        with self.lock:
            now = time.time()

            # Remove old requests
            while self.requests and now - self.requests[0] > self.window:
                self.requests.popleft()

            if len(self.requests) < self.limit:
                return 0.0

            # Wait until oldest request is outside window
            return self.window - (now - self.requests[0])


class RateLimiter:
    """
    Main rate limiter with multiple endpoint-specific limiters.

    Implements conservative rate limits (85% of actual Facebook limits)
    to provide a safety margin and avoid accidental bans.
    """

    # Conservative rate limits (85% of actual Facebook limits)
    DEFAULT_LIMITS = {
        # Messenger Send API: 300/sec actual → 250/sec safe
        "messenger_text": {"rate": 250, "capacity": 50},
        "messenger_media": {"rate": 8, "capacity": 5},  # 10/sec actual → 8/sec safe

        # Pages API: Conservative estimate
        "page_api": {"rate": 100, "capacity": 20},

        # Private Replies: 750/hour actual → 700/hour safe
        "private_replies": {"limit": 700, "window": 3600},

        # Comment reads
        "comment_read": {"limit": 500, "window": 3600},
    }

    def __init__(self, limits: Optional[Dict] = None):
        """
        Initialize rate limiter.

        Args:
            limits: Optional custom limits (uses DEFAULT_LIMITS if not provided)
        """
        self.limiters: Dict[str, object] = {}
        self.limiter_types: Dict[str, str] = {}  # Track limiter type
        self._setup_limiters(limits or self.DEFAULT_LIMITS)
        logger.info("Rate limiter initialized with limits: {}", self.DEFAULT_LIMITS)

    def _setup_limiters(self, limits: Dict):
        """Set up rate limiters based on configuration."""
        for endpoint, config in limits.items():
            if "rate" in config:
                # Use token bucket for rate-based limits
                self.limiters[endpoint] = TokenBucket(
                    rate=config["rate"],
                    capacity=config["capacity"]
                )
                self.limiter_types[endpoint] = "token_bucket"
                logger.debug(f"Token bucket for {endpoint}: {config['rate']}/sec")
            elif "limit" in config:
                # Use sliding window for count-based limits
                self.limiters[endpoint] = SlidingWindow(
                    limit=config["limit"],
                    window=config["window"]
                )
                self.limiter_types[endpoint] = "sliding_window"
                logger.debug(f"Sliding window for {endpoint}: {config['limit']}/{config['window']}s")

    async def acquire(
        self,
        endpoint: str,
        tokens: int = 1,
        max_wait: float = 10.0
    ) -> bool:
        """
        Acquire permission to make an API call.

        Args:
            endpoint: API endpoint/category (e.g., "messenger_text")
            tokens: Number of tokens to consume (for token bucket)
            max_wait: Maximum seconds to wait for permission

        Returns:
            True if permission granted, False if timeout
        """
        limiter = self.limiters.get(endpoint)

        if not limiter:
            logger.warning(f"No rate limiter for endpoint: {endpoint}")
            return True

        start = time.time()
        while time.time() - start < max_wait:
            if self.limiter_types[endpoint] == "token_bucket":
                if limiter.consume(tokens):
                    return True
            else:  # sliding window
                if limiter.allow_request():
                    return True

            # Wait a bit before retrying
            await asyncio.sleep(0.1)

        logger.warning(f"Rate limit timeout for {endpoint} after {max_wait}s")
        return False

    def get_stats(self, endpoint: str) -> Optional[RateLimitStats]:
        """
        Get rate limit statistics for an endpoint.

        Args:
            endpoint: API endpoint/category

        Returns:
            RateLimitStats or None if endpoint not found
        """
        limiter = self.limiters.get(endpoint)
        if not limiter:
            return None

        return limiter.get_stats()

    def get_all_stats(self) -> Dict[str, RateLimitStats]:
        """Get statistics for all endpoints."""
        stats = {}
        for endpoint in self.limiters:
            stats[endpoint] = self.get_stats(endpoint)
        return stats

    def get_wait_time(self, endpoint: str, tokens: int = 1) -> float:
        """
        Get estimated wait time before next allowed request.

        Args:
            endpoint: API endpoint/category
            tokens: Number of tokens needed (for token bucket)

        Returns:
            Seconds to wait (0 if request can be made now)
        """
        limiter = self.limiters.get(endpoint)
        if not limiter:
            return 0.0

        if self.limiter_types[endpoint] == "token_bucket":
            return limiter.wait_time(tokens)
        else:
            return limiter.wait_time()

    def check_and_alert(self) -> None:
        """Check all endpoints and log warnings if approaching limits."""
        for endpoint, stats in self.get_all_stats().items():
            if stats.usage_percent > 85:
                logger.error(
                    f"RATE LIMIT ALERT [{endpoint}]: "
                    f"{stats.usage_percent:.1f}% used, "
                    f"{stats.remaining_calls} remaining"
                )
            elif stats.usage_percent > 70:
                logger.warning(
                    f"Rate limit warning [{endpoint}]: "
                    f"{stats.usage_percent:.1f}% used, "
                    f"{stats.remaining_calls} remaining"
                )
            elif stats.usage_percent > 50:
                logger.info(
                    f"Rate limit status [{endpoint}]: "
                    f"{stats.usage_percent:.1f}% used"
                )


# Singleton instance for use across the application
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def reset_rate_limiter():
    """Reset the global rate limiter (useful for testing)."""
    global _rate_limiter
    _rate_limiter = None
