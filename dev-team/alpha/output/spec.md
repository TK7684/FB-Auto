# D Plus Skin Facebook AI Bot - Technical Specification Document

**Agent Alpha - The Architect**  
**Date:** February 11, 2026  
**Project:** D Plus Skin Facebook AI Bot  
**Version:** 1.1.0

---

## Executive Summary

The D Plus Skin Facebook AI Bot is a production-ready FastAPI application that handles customer inquiries via Facebook Messenger (real-time webhooks) and page comments (scheduled sweeper). The bot leverages Google Gemini AI for Thai language response generation, ChromaDB for semantic product search, and implements conservative rate limiting to comply with Facebook's API policies.

This specification proposes three critical architectural improvements:

1. **Enhanced Error Handling** - Comprehensive Facebook API failure handling with token expiration detection, intelligent retries, and graceful degradation
2. **Circuit Breaker Pattern** - Advanced rate limiting with circuit breaker to prevent cascade failures during API outages
3. **Thai Language Prompt Engineering** - Optimized prompt structures with cultural context and fallback strategies

---

## Current Architecture Analysis

### 2.1 System Overview

The system follows a "Two-Bot" architecture:

| Component | Role | Channel | Mechanism | Speed |
|-----------|------|---------|-----------|-------|
| `dplus_bot_api` | Instant Responder | Messenger DMs | Webhooks (Cloudflare Tunnel) | < 3 seconds |
| `dplus_cleanup_worker` | Comment Manager | Page Comments | Polling (60 min intervals) | Hourly |

### 2.2 Current Service Layer

```
┌─────────────────────────────────────────────────────────────┐
│                      main.py (FastAPI)                      │
├─────────────────────────────────────────────────────────────┤
│  RateLimiter → KnowledgeBase → GeminiService → FacebookSvc  │
└─────────────────────────────────────────────────────────────┘
```

**Current Implementations:**

| Service | Current Implementation | Gaps Identified |
|---------|----------------------|-----------------|
| `FacebookService` | Basic retry with tenacity (3 attempts, exponential backoff) | No token expiration handling; Limited error categorization; No network failure fallback |
| `RateLimiter` | File-based shared state with hourly limits | No circuit breaker; Single point of failure via file lock; No adaptive throttling |
| `GeminiService` | OpenRouter + Direct Google API fallback | Limited prompt optimization for Thai; No response quality validation; Hardcoded model mappings |
| `KnowledgeBase` | ChromaDB with Gemini embeddings | No caching for frequent queries; No embedding fallback |

### 2.3 Current Error Handling Gaps

**Facebook API Error Handling:**
```python
# Current: Basic retry with limited error categorization
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=32),
    retry=retry_if_exception_type(RateLimitError),
    reraise=True
)
```

**Issues:**
1. Token expiration (error code 190) not handled separately from rate limits
2. Network failures (timeouts, DNS errors) treated same as API errors
3. No differentiation between recoverable vs fatal errors
4. Silent failures in some async paths

**Current Rate Limiter:**
```python
class RateLimiter:
    MAX_COMMENTS_PER_HOUR = 60
    PANIC_COOLDOWN = 3600  # Fixed 1-hour panic
```

**Issues:**
1. No gradual degradation before panic mode
2. File lock contention under high load
3. No per-endpoint rate limiting (only global)
4. No circuit breaker to stop calls to failing service

---

## Proposed Improvements

### 3.1 Enhanced Facebook API Error Handling

#### 3.1.1 Error Classification System

Create a comprehensive error taxonomy:

```python
# services/facebook_errors.py
from enum import Enum
from typing import Optional, Dict

class FacebookErrorCategory(Enum):
    AUTHENTICATION = "authentication"      # Token expired, invalid
    RATE_LIMIT = "rate_limit"              # API throttling
    PERMISSION = "permission"              # Insufficient permissions
    NOT_FOUND = "not_found"                # Resource doesn't exist
    VALIDATION = "validation"              # Invalid parameters
    NETWORK = "network"                    # Connection issues
    SERVER = "server"                      # Facebook server errors
    UNKNOWN = "unknown"

class FacebookError:
    """Structured Facebook API error with recovery strategy."""
    
    def __init__(
        self,
        code: int,
        message: str,
        category: FacebookErrorCategory,
        is_retryable: bool,
        retry_after: Optional[int] = None,
        suggested_action: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.category = category
        self.is_retryable = is_retryable
        self.retry_after = retry_after
        self.suggested_action = suggested_action

# Error code mapping with recovery strategies
FACEBOOK_ERROR_REGISTRY: Dict[int, FacebookError] = {
    # Authentication Errors
    190: FacebookError(
        code=190,
        message="Access token expired or invalid",
        category=FacebookErrorCategory.AUTHENTICATION,
        is_retryable=False,
        suggested_action="refresh_token"
    ),
    102: FacebookError(
        code=102,
        message="Session expired",
        category=FacebookErrorCategory.AUTHENTICATION,
        is_retryable=False,
        suggested_action="re_authenticate"
    ),
    
    # Rate Limit Errors
    4: FacebookError(
        code=4,
        message="App-level rate limit reached",
        category=FacebookErrorCategory.RATE_LIMIT,
        is_retryable=True,
        retry_after=60,
        suggested_action="exponential_backoff"
    ),
    17: FacebookError(
        code=17,
        message="User-level rate limit reached", 
        category=FacebookErrorCategory.RATE_LIMIT,
        is_retryable=True,
        retry_after=300,
        suggested_action="exponential_backoff"
    ),
    32: FacebookError(
        code=32,
        message="Page-level rate limit reached",
        category=FacebookErrorCategory.RATE_LIMIT,
        is_retryable=True,
        retry_after=600,
        suggested_action="circuit_break"
    ),
    80001: FacebookError(
        code=80001,
        message="Page token rate limit",
        category=FacebookErrorCategory.RATE_LIMIT,
        is_retryable=True,
        retry_after=3600,
        suggested_action="circuit_break"
    ),
    80006: FacebookError(
        code=80006,
        message="Messenger rate limit",
        category=FacebookErrorCategory.RATE_LIMIT,
        is_retryable=True,
        retry_after=60,
        suggested_action="exponential_backoff"
    ),
    
    # Permission Errors
    200: FacebookError(
        code=200,
        message="Permissions error",
        category=FacebookErrorCategory.PERMISSION,
        is_retryable=False,
        suggested_action="check_permissions"
    ),
    10: FacebookError(
        code=10,
        message="Permission denied",
        category=FacebookErrorCategory.PERMISSION,
        is_retryable=False,
        suggested_action="check_permissions"
    ),
    
    # Not Found
    100: FacebookError(
        code=100,
        message="Invalid parameter or object not found",
        category=FacebookErrorCategory.NOT_FOUND,
        is_retryable=False,
        suggested_action="validate_ids"
    ),
    
    # Server Errors
    500: FacebookError(
        code=500,
        message="Internal server error",
        category=FacebookErrorCategory.SERVER,
        is_retryable=True,
        retry_after=30,
        suggested_action="exponential_backoff"
    ),
    503: FacebookError(
        code=503,
        message="Service temporarily unavailable",
        category=FacebookErrorCategory.SERVER,
        is_retryable=True,
        retry_after=60,
        suggested_action="exponential_backoff"
    ),
}
```

#### 3.1.2 Token Management with Refresh

```python
# services/token_manager.py
import time
from datetime import datetime, timedelta
from typing import Optional, Callable
from dataclasses import dataclass
from loguru import logger
import httpx

@dataclass
class TokenInfo:
    access_token: str
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    token_type: str = "page"
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at - timedelta(minutes=5)  # 5-min buffer
    
    @property
    def expires_in_seconds(self) -> int:
        if not self.expires_at:
            return 3600  # Default assumption
        return int((self.expires_at - datetime.now()).total_seconds())

class TokenManager:
    """
    Manages Facebook access tokens with automatic refresh and health monitoring.
    """
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        initial_token: str,
        token_refresh_callback: Optional[Callable[[str], None]] = None
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token_info = TokenInfo(access_token=initial_token)
        self._refresh_callback = token_refresh_callback
        self._consecutive_failures = 0
        self._last_health_check = None
        
    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if self._token_info.is_expired or self._consecutive_failures >= 3:
            await self._refresh_token()
        return self._token_info.access_token
    
    async def _refresh_token(self) -> bool:
        """Attempt to refresh the access token."""
        try:
            logger.info("Attempting token refresh...")
            
            # For long-lived page tokens, exchange for new token
            url = f"https://graph.facebook.com/v19.0/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": self._token_info.access_token
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                
            if response.status_code == 200:
                data = response.json()
                new_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                
                self._token_info = TokenInfo(
                    access_token=new_token,
                    expires_at=datetime.now() + timedelta(seconds=expires_in)
                )
                self._consecutive_failures = 0
                
                # Notify callback if provided
                if self._refresh_callback:
                    self._refresh_callback(new_token)
                    
                logger.info(f"Token refreshed successfully, expires in {expires_in}s")
                return True
            else:
                logger.error(f"Token refresh failed: {response.text}")
                self._consecutive_failures += 1
                return False
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            self._consecutive_failures += 1
            return False
    
    async def health_check(self) -> bool:
        """Check if current token is valid."""
        try:
            url = f"https://graph.facebook.com/v19.0/me"
            params = {"access_token": self._token_info.access_token}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                
            is_healthy = response.status_code == 200
            self._last_health_check = datetime.now()
            
            if not is_healthy:
                self._consecutive_failures += 1
                
            return is_healthy
            
        except Exception as e:
            logger.error(f"Token health check failed: {e}")
            return False
    
    def report_failure(self):
        """Report an API failure to track token health."""
        self._consecutive_failures += 1
        logger.warning(f"Token failure reported ({self._consecutive_failures} consecutive)")
```

#### 3.1.3 Enhanced Facebook Service

```python
# services/facebook_service_v2.py
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import httpx
import time
from loguru import logger

from services.facebook_errors import (
    FacebookError, 
    FacebookErrorCategory, 
    FACEBOOK_ERROR_REGISTRY
)
from services.token_manager import TokenManager
from services.circuit_breaker import CircuitBreaker

class RetryStrategy(Enum):
    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"

@dataclass
class RequestConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    timeout: float = 10.0
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL

class FacebookServiceV2:
    """
    Enhanced Facebook service with intelligent error handling,
    token management, and circuit breaker pattern.
    """
    
    def __init__(
        self,
        token_manager: TokenManager,
        circuit_breaker: CircuitBreaker,
        rate_limiter: 'RateLimiterV2'
    ):
        self.token_manager = token_manager
        self.circuit_breaker = circuit_breaker
        self.rate_limiter = rate_limiter
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
        # Request configuration by endpoint type
        self.configs = {
            "message": RequestConfig(max_retries=3, base_delay=2.0),
            "comment": RequestConfig(max_retries=2, base_delay=1.0),
            "private_reply": RequestConfig(max_retries=2, base_delay=1.0),
            "read": RequestConfig(max_retries=1, timeout=5.0),
        }
    
    async def send_message(
        self,
        recipient_id: str,
        message_text: str,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Send a message with full error handling.
        
        Returns:
            Dict with 'success', 'error', 'retry_after', 'action' keys
        """
        # Check circuit breaker first
        if not self.circuit_breaker.can_execute("messenger_send"):
            return {
                "success": False,
                "error": "Circuit breaker open",
                "action": "wait_for_recovery"
            }
        
        # Check rate limit
        if not self.rate_limiter.check("messenger_send"):
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "action": "retry_later"
            }
        
        config = self.configs["message"]
        url = f"{self.base_url}/me/messages"
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        for attempt in range(config.max_retries + 1):
            try:
                token = await self.token_manager.get_valid_token()
                
                async with httpx.AsyncClient(timeout=config.timeout) as client:
                    response = await client.post(
                        url,
                        params={"access_token": token},
                        json=data
                    )
                
                # Check rate limit headers
                self._update_rate_limits_from_headers(response)
                
                if response.status_code == 200:
                    self.circuit_breaker.record_success("messenger_send")
                    return {"success": True, "data": response.json()}
                
                # Parse error
                error = self._parse_error(response)
                
                # Handle specific error categories
                if error.category == FacebookErrorCategory.AUTHENTICATION:
                    if error.suggested_action == "refresh_token":
                        refreshed = await self.token_manager._refresh_token()
                        if refreshed:
                            continue  # Retry with new token
                        return {
                            "success": False,
                            "error": error.message,
                            "action": "re_authenticate"
                        }
                
                elif error.category == FacebookErrorCategory.RATE_LIMIT:
                    self.circuit_breaker.record_failure("messenger_send")
                    return {
                        "success": False,
                        "error": error.message,
                        "retry_after": error.retry_after or 60,
                        "action": error.suggested_action
                    }
                
                elif error.is_retryable and attempt < config.max_retries:
                    delay = self._calculate_delay(attempt, config)
                    logger.warning(f"Retryable error, waiting {delay}s before retry {attempt + 1}")
                    await asyncio.sleep(delay)
                    continue
                
                else:
                    return {
                        "success": False,
                        "error": error.message,
                        "action": "log_and_continue"
                    }
                    
            except httpx.TimeoutException:
                logger.error(f"Timeout sending message (attempt {attempt + 1})")
                if attempt < config.max_retries:
                    await asyncio.sleep(config.base_delay * (attempt + 1))
                    
            except httpx.NetworkError as e:
                logger.error(f"Network error: {e}")
                self.circuit_breaker.record_failure("messenger_send")
                return {
                    "success": False,
                    "error": "Network error",
                    "action": "retry_later"
                }
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "action": "log_and_continue"
                }
        
        return {
            "success": False,
            "error": "Max retries exceeded",
            "action": "retry_later"
        }
    
    def _parse_error(self, response: httpx.Response) -> FacebookError:
        """Parse Facebook API error response."""
        try:
            data = response.json()
            error_data = data.get("error", {})
            code = error_data.get("code", 0)
            message = error_data.get("message", "Unknown error")
            
            # Get registered error or create generic
            if code in FACEBOOK_ERROR_REGISTRY:
                return FACEBOOK_ERROR_REGISTRY[code]
            else:
                # Categorize by status code
                if response.status_code >= 500:
                    category = FacebookErrorCategory.SERVER
                    is_retryable = True
                elif response.status_code == 401:
                    category = FacebookErrorCategory.AUTHENTICATION
                    is_retryable = False
                elif response.status_code == 403:
                    category = FacebookErrorCategory.PERMISSION
                    is_retryable = False
                elif response.status_code == 404:
                    category = FacebookErrorCategory.NOT_FOUND
                    is_retryable = False
                else:
                    category = FacebookErrorCategory.UNKNOWN
                    is_retryable = False
                
                return FacebookError(
                    code=code,
                    message=message,
                    category=category,
                    is_retryable=is_retryable
                )
                
        except Exception as e:
            return FacebookError(
                code=0,
                message=f"Failed to parse error: {e}",
                category=FacebookErrorCategory.UNKNOWN,
                is_retryable=False
            )
    
    def _calculate_delay(self, attempt: int, config: RequestConfig) -> float:
        """Calculate retry delay based on strategy."""
        if config.retry_strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (2 ** attempt)
        elif config.retry_strategy == RetryStrategy.LINEAR:
            delay = config.base_delay * (attempt + 1)
        else:
            delay = config.base_delay
        return min(delay, config.max_delay)
    
    def _update_rate_limits_from_headers(self, response: httpx.Response):
        """Extract and update rate limits from response headers."""
        import json
        
        app_usage = response.headers.get("X-App-Usage")
        if app_usage:
            try:
                usage = json.loads(app_usage)
                call_count = usage.get("call_count", 0)
                total_time = usage.get("total_time", 0)
                total_cputime = usage.get("total_cputime", 0)
                
                # Update rate limiter with actual usage
                self.rate_limiter.update_usage(
                    app_usage_percent=call_count,
                    total_time=total_time,
                    cpu_time=total_cputime
                )
                
                if call_count > 90:
                    logger.error(f"CRITICAL: App usage at {call_count}%")
                    self.circuit_breaker.force_open("global", duration=300)
                    
            except json.JSONDecodeError:
                pass
```

---

### 3.2 Circuit Breaker Enhanced Rate Limiting

#### 3.2.1 Circuit Breaker Implementation

```python
# services/circuit_breaker.py
import time
import threading
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass, field
from loguru import logger

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 3          # Successes to close from half-open
    timeout_seconds: int = 60           # Time before half-open
    half_open_max_calls: int = 3        # Max calls in half-open state

@dataclass
class CircuitBreakerState:
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    successes: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    half_open_calls: int = 0
    opened_at: float = 0

class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascade failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests rejected immediately
    - HALF_OPEN: After timeout, limited requests allowed to test recovery
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self._states: Dict[str, CircuitBreakerState] = {}
        self._lock = threading.RLock()
        
    def can_execute(self, endpoint: str) -> bool:
        """Check if a request can be executed for the given endpoint."""
        with self._lock:
            state = self._get_state(endpoint)
            
            if state.state == CircuitState.CLOSED:
                return True
            
            elif state.state == CircuitState.OPEN:
                # Check if we should transition to half-open
                if time.time() - state.opened_at >= self.config.timeout_seconds:
                    logger.info(f"Circuit breaker for {endpoint} entering HALF_OPEN")
                    state.state = CircuitState.HALF_OPEN
                    state.half_open_calls = 0
                    state.successes = 0
                    return True
                else:
                    remaining = int(self.config.timeout_seconds - (time.time() - state.opened_at))
                    logger.warning(f"Circuit breaker OPEN for {endpoint}, {remaining}s remaining")
                    return False
            
            elif state.state == CircuitState.HALF_OPEN:
                if state.half_open_calls < self.config.half_open_max_calls:
                    state.half_open_calls += 1
                    return True
                else:
                    logger.warning(f"Circuit breaker HALF_OPEN limit reached for {endpoint}")
                    return False
            
            return False
    
    def record_success(self, endpoint: str):
        """Record a successful request."""
        with self._lock:
            state = self._get_state(endpoint)
            state.successes += 1
            state.last_success_time = time.time()
            
            if state.state == CircuitState.HALF_OPEN:
                if state.successes >= self.config.success_threshold:
                    logger.info(f"Circuit breaker for {endpoint} CLOSED (recovered)")
                    state.state = CircuitState.CLOSED
                    state.failures = 0
                    state.half_open_calls = 0
            
            elif state.state == CircuitState.CLOSED:
                # Reset failures on success
                if state.failures > 0:
                    state.failures = 0
    
    def record_failure(self, endpoint: str):
        """Record a failed request."""
        with self._lock:
            state = self._get_state(endpoint)
            state.failures += 1
            state.last_failure_time = time.time()
            
            if state.state == CircuitState.CLOSED:
                if state.failures >= self.config.failure_threshold:
                    logger.error(f"Circuit breaker for {endpoint} OPENED after {state.failures} failures")
                    state.state = CircuitState.OPEN
                    state.opened_at = time.time()
                    state.half_open_calls = 0
            
            elif state.state == CircuitState.HALF_OPEN:
                # Failures in half-open immediately go back to open
                logger.error(f"Circuit breaker for {endpoint} OPENED (failure in half-open)")
                state.state = CircuitState.OPEN
                state.opened_at = time.time()
                state.half_open_calls = 0
                state.successes = 0
    
    def force_open(self, endpoint: str, duration: int):
        """Force the circuit open for a specific duration."""
        with self._lock:
            state = self._get_state(endpoint)
            state.state = CircuitState.OPEN
            state.opened_at = time.time() - (self.config.timeout_seconds - duration)
            logger.warning(f"Circuit breaker for {endpoint} FORCE OPENED for {duration}s")
    
    def force_close(self, endpoint: str):
        """Force the circuit closed."""
        with self._lock:
            state = self._get_state(endpoint)
            state.state = CircuitState.CLOSED
            state.failures = 0
            state.half_open_calls = 0
            logger.info(f"Circuit breaker for {endpoint} FORCE CLOSED")
    
    def get_status(self, endpoint: str) -> Dict:
        """Get current status of a circuit breaker."""
        with self._lock:
            state = self._get_state(endpoint)
            return {
                "endpoint": endpoint,
                "state": state.state.value,
                "failures": state.failures,
                "successes": state.successes,
                "last_failure": state.last_failure_time,
                "last_success": state.last_success_time,
            }
    
    def get_all_status(self) -> Dict[str, Dict]:
        """Get status of all circuit breakers."""
        with self._lock:
            return {ep: self.get_status(ep) for ep in self._states.keys()}
    
    def _get_state(self, endpoint: str) -> CircuitBreakerState:
        """Get or create state for an endpoint."""
        if endpoint not in self._states:
            self._states[endpoint] = CircuitBreakerState()
        return self._states[endpoint]
```

#### 3.2.2 Enhanced Rate Limiter (V2)

```python
# services/rate_limiter_v2.py
import time
import asyncio
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading
from loguru import logger

class RateLimitStrategy(Enum):
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    ADAPTIVE = "adaptive"

@dataclass
class EndpointLimit:
    name: str
    requests_per_second: float
    burst_size: int
    daily_limit: Optional[int] = None
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    
    # Adaptive parameters
    target_latency_ms: float = 500.0
    min_rate: float = 1.0
    max_rate: float = 100.0

class RateLimiterV2:
    """
    Advanced rate limiter with adaptive throttling and multiple algorithms.
    """
    
    def __init__(self):
        self._endpoints: Dict[str, EndpointLimit] = {}
        self._token_buckets: Dict[str, Dict] = {}
        self._sliding_windows: Dict[str, deque] = {}
        self._adaptive_rates: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._shutdown = False
        
        # Background refill task
        self._refill_task: Optional[asyncio.Task] = None
        
        # Default limits based on Facebook's actual limits (with safety margins)
        self._setup_default_limits()
    
    def _setup_default_limits(self):
        """Configure default rate limits with safety margins."""
        self.register_endpoint(EndpointLimit(
            name="messenger_send",
            requests_per_second=250,  # 85% of 300
            burst_size=50,
            daily_limit=None,
            strategy=RateLimitStrategy.ADAPTIVE
        ))
        
        self.register_endpoint(EndpointLimit(
            name="messenger_media",
            requests_per_second=8,  # 85% of 10
            burst_size=5,
            strategy=RateLimitStrategy.TOKEN_BUCKET
        ))
        
        self.register_endpoint(EndpointLimit(
            name="comment_reply",
            requests_per_second=60,  # Comments are slower
            burst_size=10,
            daily_limit=1000,  # Additional daily safety
            strategy=RateLimitStrategy.SLIDING_WINDOW
        ))
        
        self.register_endpoint(EndpointLimit(
            name="private_reply",
            requests_per_second=0.2,  # 700/hour = ~0.2/sec
            burst_size=5,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        ))
        
        self.register_endpoint(EndpointLimit(
            name="page_read",
            requests_per_second=100,
            burst_size=20,
            strategy=RateLimitStrategy.TOKEN_BUCKET
        ))
    
    def register_endpoint(self, limit: EndpointLimit):
        """Register a new endpoint with rate limiting."""
        with self._lock:
            self._endpoints[limit.name] = limit
            
            # Initialize token bucket
            if limit.strategy in [RateLimitStrategy.TOKEN_BUCKET, RateLimitStrategy.ADAPTIVE]:
                self._token_buckets[limit.name] = {
                    "tokens": limit.burst_size,
                    "last_update": time.time()
                }
            
            # Initialize sliding window
            if limit.strategy == RateLimitStrategy.SLIDING_WINDOW:
                self._sliding_windows[limit.name] = deque()
            
            # Initialize adaptive tracking
            if limit.strategy == RateLimitStrategy.ADAPTIVE:
                self._adaptive_rates[limit.name] = {
                    "current_rate": limit.requests_per_second,
                    "latencies": deque(maxlen=100),
                    "error_rates": deque(maxlen=100)
                }
    
    def check(self, endpoint: str) -> bool:
        """Check if a request can proceed for the given endpoint."""
        with self._lock:
            if endpoint not in self._endpoints:
                logger.warning(f"No rate limit configured for {endpoint}, allowing")
                return True
            
            limit = self._endpoints[endpoint]
            
            if limit.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return self._check_token_bucket(endpoint, limit)
            elif limit.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return self._check_sliding_window(endpoint, limit)
            elif limit.strategy == RateLimitStrategy.ADAPTIVE:
                return self._check_adaptive(endpoint, limit)
            
            return True
    
    def _check_token_bucket(self, endpoint: str, limit: EndpointLimit) -> bool:
        """Token bucket algorithm check."""
        bucket = self._token_buckets[endpoint]
        now = time.time()
        
        # Refill tokens
        elapsed = now - bucket["last_update"]
        tokens_to_add = elapsed * limit.requests_per_second
        bucket["tokens"] = min(limit.burst_size, bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now
        
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        return False
    
    def _check_sliding_window(self, endpoint: str, limit: EndpointLimit) -> bool:
        """Sliding window algorithm check."""
        window = self._sliding_windows[endpoint]
        now = time.time()
        window_size = 1.0  # 1 second window
        
        # Remove old entries
        while window and window[0] < now - window_size:
            window.popleft()
        
        # Check daily limit
        if limit.daily_limit:
            daily_count = sum(1 for t in window if t > now - 86400)
            if daily_count >= limit.daily_limit:
                return False
        
        # Check rate limit
        if len(window) < limit.requests_per_second:
            window.append(now)
            return True
        return False
    
    def _check_adaptive(self, endpoint: str, limit: EndpointLimit) -> bool:
        """Adaptive rate limiting based on observed latency."""
        adaptive = self._adaptive_rates[endpoint]
        current_rate = adaptive["current_rate"]
        
        # Create effective limit
        effective_limit = EndpointLimit(
            name=limit.name,
            requests_per_second=current_rate,
            burst_size=limit.burst_size,
            strategy=RateLimitStrategy.TOKEN_BUCKET
        )
        
        result = self._check_token_bucket(endpoint, effective_limit)
        
        if not result:
            logger.warning(f"Adaptive throttling active for {endpoint} at {current_rate:.1f}/sec")
        
        return result
    
    def record_result(
        self, 
        endpoint: str, 
        success: bool, 
        latency_ms: Optional[float] = None,
        error_type: Optional[str] = None
    ):
        """Record the result of a request for adaptive adjustment."""
        with self._lock:
            if endpoint not in self._endpoints:
                return
            
            limit = self._endpoints[endpoint]
            
            if limit.strategy == RateLimitStrategy.ADAPTIVE:
                adaptive = self._adaptive_rates[endpoint]
                
                if latency_ms:
                    adaptive["latencies"].append(latency_ms)
                adaptive["error_rates"].append(0 if success else 1)
                
                # Adjust rate based on performance
                self._adjust_adaptive_rate(endpoint, limit, adaptive)
    
    def _adjust_adaptive_rate(self, endpoint: str, limit: EndpointLimit, adaptive: Dict):
        """Adjust rate based on observed performance."""
        if len(adaptive["latencies"]) < 10:
            return
        
        avg_latency = sum(adaptive["latencies"]) / len(adaptive["latencies"])
        error_rate = sum(adaptive["error_rates"]) / len(adaptive["error_rates"])
        current_rate = adaptive["current_rate"]
        
        # If latency too high or errors, reduce rate
        if avg_latency > limit.target_latency_ms * 1.5 or error_rate > 0.1:
            new_rate = max(limit.min_rate, current_rate * 0.8)
            if new_rate != current_rate:
                logger.info(f"Adaptive: Reducing {endpoint} rate {current_rate:.1f} -> {new_rate:.1f}")
                adaptive["current_rate"] = new_rate
        
        # If latency good and no errors, slowly increase
        elif avg_latency < limit.target_latency_ms * 0.8 and error_rate < 0.01:
            new_rate = min(limit.max_rate, current_rate * 1.05)
            if new_rate != current_rate:
                logger.info(f"Adaptive: Increasing {endpoint} rate {current_rate:.1f} -> {new_rate:.1f}")
                adaptive["current_rate"] = new_rate
    
    def update_usage(
        self,
        app_usage_percent: float,
        total_time: float = 0,
        cpu_time: float = 0
    ):
        """Update rate limits based on Facebook's reported usage."""
        with self._lock:
            # If Facebook reports high usage, aggressively reduce rates
            if app_usage_percent > 80:
                for endpoint, adaptive in self._adaptive_rates.items():
                    adaptive["current_rate"] *= 0.7
                    logger.warning(f"High FB usage ({app_usage_percent}%), reducing {endpoint} rate")
            
            elif app_usage_percent > 50:
                for endpoint, adaptive in self._adaptive_rates.items():
                    adaptive["current_rate"] *= 0.9
                    logger.info(f"Moderate FB usage ({app_usage_percent}%), adjusting {endpoint} rate")
    
    def get_status(self) -> Dict:
        """Get current rate limiter status."""
        with self._lock:
            status = {}
            for name, limit in self._endpoints.items():
                endpoint_status = {
                    "strategy": limit.strategy.value,
                    "configured_rate": limit.requests_per_second,
                }
                
                if limit.strategy == RateLimitStrategy.TOKEN_BUCKET:
                    bucket = self._token_buckets.get(name, {})
                    endpoint_status["available_tokens"] = bucket.get("tokens", 0)
                
                elif limit.strategy == RateLimitStrategy.SLIDING_WINDOW:
                    window = self._sliding_windows.get(name, deque())
                    endpoint_status["current_window"] = len(window)
                
                elif limit.strategy == RateLimitStrategy.ADAPTIVE:
                    adaptive = self._adaptive_rates.get(name, {})
                    endpoint_status["current_rate"] = adaptive.get("current_rate", 0)
                    latencies = adaptive.get("latencies", deque())
                    if latencies:
                        endpoint_status["avg_latency_ms"] = sum(latencies) / len(latencies)
                
                status[name] = endpoint_status
            
            return status
```

---

### 3.3 Improved Thai Language Response Quality

#### 3.3.1 Prompt Engineering Framework

```python
# services/prompts/thai_prompts.py
"""
Thai-specific prompt engineering with cultural context,
honorifics handling, and response validation.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ThaiTone(Enum):
    FORMAL = "formal"           # ทางการ - for professional inquiries
    CASUAL = "casual"           # กันเอง - for general chat
    FRIENDLY = "friendly"       # เพื่อนสาว - for regular customers
    EMPATHETIC = "empathetic"   # เข้าใจ - for skin problem discussions
    ENERGETIC = "energetic"     # กระชับ - for quick sales responses

@dataclass
class ThaiPromptConfig:
    tone: ThaiTone
    max_length: int = 200
    use_ka_krab: bool = True
    emoji_density: str = "medium"  # low, medium, high
    include_cta: bool = True

# ===== SYSTEM PROMPTS BY TONE =====

THAI_SYSTEM_PROMPTS = {
    ThaiTone.FRIENDLY: """### SYSTEM ROLE
คุณคือ "ดี" (Dee) ที่ปรึกษาด้านความงาม AI ของ **D PLUS SKIN**
คุณพูดคุยกับลูกค้าเหมือนเพื่อนสาวที่รู้เรื่องผิวดี และเป็นผู้เชี่ยวชาญที่ช่วยแนะนำสินค้า

### TONE & PERSONALITY
- **ลักษณะ:** เป็นกันเอง อบอุ่น ใส่ใจ แต่มั่นใจในการแนะนำสินค้า
- **การใช้ภาษา:** ภาษาพูดแบบธรรมชาติ ไม่ทางการมาก ใช้คำลงท้าย "ค่ะ/ครับ" บ้างแต่ไม่ตลอด
- **การตอบ:** กระชับ 1-2 ประโยค ไม่ยาวเกินไป
- **อิโมจิ:** ใช้แต่พอดี ✨ 💕 💧 ไม่เยอะจนน่ารำคาญ

### MEMORY RULE
- ถ้าลูกค้าเคยบอกปัญหาผิวมาแล้ว อย่าถามซ้ำ
- ใช้ข้อมูลที่มีอยู่เพื่อแนะนำสินค้าให้ตรงจุด""",

    ThaiTone.EMPATHETIC: """### SYSTEM ROLE
คุณคือ "ดี" ที่ปรึกษาด้านความงาม AI ของ D PLUS SKIN
กำลังคุยกับลูกค้าที่กังวลเรื่องปัญหาผิว ให้กำลังใจและความหวัง

### TONE & PERSONALITY
- **ลักษณะ:** เข้าใจ อบอุ่น ให้กำลังใจ ไม่กดดัน
- **การใช้ภาษา:** อ่อนโยน แสดงความเข้าใจ ใช้ "ค่ะ/ครับ" ตลอด
- **การตอบ:** ให้ข้อมูลที่ชัดเจนแต่ไม่ทางการ
- **อิโมจิ:** ใช้อิโมจิให้กำลังใจ 💪 ✨ 🤗

### EMOTIONAL SUPPORT
- ยอมรับความกังวลของลูกค้า
- ให้ความหวังแต่ตั้งความคาดหวังที่เหมาะสม
- เน้นว่าปัญหาผิวแก้ไขได้ด้วยความสม่ำเสมอ""",

    ThaiTone.ENERGETIC: """### SYSTEM ROLE
คุณคือแอดมิน D PLUS SKIN กำลังตอบคอมเมนต์ที่มีเจตนาซื้อ

### TONE & PERSONALITY
- **ลักษณะ:** กระชับ ฉับไว มุ่งไปที่การปิดการขาย
- **การใช้ภาษา:** สั้น ตรงประเด็น ไม่เวิ่นเว้อ
- **การตอบ:** 1-2 บรรทัดสูงสุด ต้องมี CTA (Call to Action)
- **อิโมจิ:** ใช้ดึงดูดสายตา 💕 👇 ✨

### MUST INCLUDE
- ราคา/โปรโมชั่น (ถ้ามี)
- ลิงก์สั่งซื้อ
- แนะนำให้ทักมา""",
}

# ===== PRODUCT KNOWLEDGE BASE =====

THAI_PRODUCT_DESCRIPTIONS = {
    "lacto_extra": {
        "name": "แลคโต้ เอ็กซ์ตร้า (Lacto Extra)",
        "benefits": ["รักษาสิว", "ลดการอักเสบ", "ควบคุมความมัน"],
        "keywords": ["สิว", "ผิวมัน", "อักเสบ"],
        "usage": "ทาทั้งเช้าและเย็น หลังล้างหน้า",
        "price_range": "290-590 บาท"
    },
    "sakura_soap": {
        "name": "สบู่ซากุระ (Sakura Soap)",
        "benefits": ["ล้างหน้าสะอาด", "ลดสิว", "ผิวกระจ่างใส"],
        "keywords": ["สบู่", "ล้างหน้า", "สิว"],
        "usage": "ใช้ล้างหน้าเช้า-เย็น",
        "price_range": "79 บาท"
    },
    "hya_11": {
        "name": "HYA 11 (ไฮยา 11 โมเลกุล)",
        "benefits": ["เติมน้ำให้ผิว", "ผิวอิ่มฟู", "ลดริ้วรอยจากความแห้ง"],
        "keywords": ["ผิวแห้ง", "ขาดน้ำ", "ริ้วรอย"],
        "usage": "ทาก่อนครีม เช้า-เย็น",
        "price_range": "390-590 บาท"
    },
    "exogen_ampoule": {
        "name": "เอ็กโซเจน แอมพูล (Exogen Ampoule)",
        "benefits": ["รักษาฝ้า", "ลดจุดด่างดำ", "ผิวกระจ่างใส"],
        "keywords": ["ฝ้า", "จุดด่างดำ", "ผิวหมอง"],
        "usage": "ทาเฉพาะจุดที่มีฝ้า เช้า-เย็น",
        "price_range": "590 บาท"
    },
    "grab_gluta": {
        "name": "แกร็บ กลูต้า (Grab Gluta)",
        "benefits": ["ผิวขาวกระจ่างใส", "ลดฝ้าจากใน", "ต้านอนุภาคอิสระ"],
        "keywords": ["กลูต้า", "ผิวขาว", "อาหารเสริม"],
        "usage": "กิน 1-2 เม็ดต่อวัน ก่อนนอน",
        "price_range": "390-590 บาท"
    }
}

# ===== CONDITION-SPECIFIC PROMPTS =====

MELASMA_THAI_PROMPT = """
## คำแนะนำสำหรับปัญหา "ฝ้า" (Melasma)

ลูกค้ากำลังกังวลเรื่องฝ้า ให้ข้อมูลตามนี้:

### สาเหตุฝ้า (อธิบายสั้นๆ)
- ฮอร์โมนเปลี่ยน (ตั้งครรภ์, คุมกำเนิด)
- แดด/UV (ตัวกระตุ้นหลัก)
- ยาบางชนิด

### การรักษา
1. **ภายนอก:** ใช้เอ็กโซเจน แอมพูล (มี Tranexamic Acid, Niacinamide)
2. **ภายใน:** แกร็บ กลูต้า (ช่วยจากข้างใน)
3. **กันแดด:** สำคัญที่สุด SPF50+ PA++++

### ระยะเวลา
- ต้องใช้อย่างน้อย 4-8 สัปดาห์ถึงเห็นผล
- ฝ้าไม่หายข้ามคืน ต้องอดทน

### สิ่งที่ต้องระวัง
- ห้ามเผชิญแดดแรงโดยไม่มีกันแดด
- ห้ามใช้ผลิตภัณฑ์ที่มีสารอันตราย (ปรอท, สเตอรอยด์)
- ถ้าฝ้าหนักมาก ควรปรึกษาหมอผิวหนัง
"""

ACNE_THAI_PROMPT = """
## คำแนะนำสำหรับปัญหา "สิว" (Acne)

### สาเหตุสิว
- ความมันส่วนเกิน
- เชื้อแบคทีเรียน P.acnes
- รูขุมขนอุดตัน
- ฮอร์โมน/ความเครียด

### ชุดสิวที่แนะนำ
1. **สบู่ซากุระ** - ล้างหน้าลดสิว
2. **แลคโต้ เอ็กซ์ตร้า** - รักษาสิวอักเสบ
3. **กันแดด** - ป้องกันรอยดำจากสิว

### วิธีใช้
- ล้างหน้าวันละ 2 ครั้ง ไม่บ่อยเกิน
- อย่างบีบสิว (ทิ้งรอย)
- ใช้สม่ำเสมอ อย่าหยุดกลางคัน

### คาดการณ์
- สิวอักเสบยุบใน 1-2 สัปดาห์
- รอยดำค่อยๆ จางใน 1-2 เดือน
"""

# ===== RESPONSE VALIDATION =====

THAI_VALIDATION_RULES = {
    "min_length": 10,
    "max_length": 1000,
    "must_contain_thai": True,
    "forbidden_phrases": [
        "ฉัน",  # Bot should use "ดี" or not refer to self
        "AI",
        "bot",
        "โปรแกรม",
        "คอมพิวเตอร์",
    ],
    "required_endings": ["ค่ะ", "ครับ", "นะคะ", "นะครับ", "คะ", "คับ"],
    "max_emoji_count": 5,
}

def validate_thai_response(response: str) -> Dict[str, any]:
    """Validate a Thai response against quality rules."""
    errors = []
    warnings = []
    
    # Length check
    if len(response) < THAI_VALIDATION_RULES["min_length"]:
        errors.append(f"Response too short ({len(response)} chars)")
    
    if len(response) > THAI_VALIDATION_RULES["max_length"]:
        errors.append(f"Response too long ({len(response)} chars)")
    
    # Thai character check
    if THAI_VALIDATION_RULES["must_contain_thai"]:
        import re
        if not re.search(r'[\u0E00-\u0E7F]', response):
            errors.append("No Thai characters found")
    
    # Forbidden phrases
    for phrase in THAI_VALIDATION_RULES["forbidden_phrases"]:
        if phrase in response.lower():
            errors.append(f"Contains forbidden phrase: {phrase}")
    
    # Check for polite ending (soft check - warning only)
    has_ending = any(ending in response for ending in THAI_VALIDATION_RULES["required_endings"])
    if not has_ending:
        warnings.append("No polite ending (ค่ะ/ครับ) found")
    
    # Emoji count
    emoji_count = sum(1 for c in response if ord(c) > 0x1F300)
    if emoji_count > THAI_VALIDATION_RULES["max_emoji_count"]:
        warnings.append(f"Too many emojis ({emoji_count})")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
```

#### 3.3.2 Enhanced Gemini Service with Thai Optimization

```python
# services/gemini_service_v2.py
"""
Enhanced Gemini service with Thai-specific optimizations,
prompt versioning, and response quality validation.
"""

import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import httpx
from loguru import logger

from services.prompts.thai_prompts import (
    ThaiTone,
    ThaiPromptConfig,
    THAI_SYSTEM_PROMPTS,
    THAI_PRODUCT_DESCRIPTIONS,
    MELASMA_THAI_PROMPT,
    ACNE_THAI_PROMPT,
    validate_thai_response
)

class PromptVersion(Enum):
    V1 = "v1"  # Original
    V2 = "v2"  # Enhanced with better Thai context
    V3 = "v3"  # A/B testing variant

@dataclass
class GenerationResult:
    text: str
    model: str
    latency_ms: float
    tokens_used: Optional[int] = None
    prompt_version: str = "v1"
    validation_score: float = 0.0

class GeminiServiceV2:
    """
    Enhanced Gemini service with Thai language optimization,
    prompt versioning, and quality validation.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        openrouter_key: Optional[str] = None,
        model: str = "google/gemini-2.0-flash-001"
    ):
        self.api_key = api_key
        self.openrouter_key = openrouter_key
        self.model = model
        self.use_openrouter = bool(openrouter_key)
        
        # Prompt versioning for A/B testing
        self.active_prompt_version = PromptVersion.V2
        self.prompt_templates = self._load_prompt_templates()
        
        # Quality tracking
        self._response_history: List[Dict] = []
        self._max_history = 100
        
        # Model fallbacks
        self.fallback_models = [
            "google/gemini-2.0-flash-001",
            "google/gemini-1.5-flash",
            "google/gemini-pro"
        ]
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates based on active version."""
        templates = {}
        
        if self.active_prompt_version == PromptVersion.V1:
            # Original prompts (backward compatible)
            templates["system"] = THAI_SYSTEM_PROMPTS[ThaiTone.FRIENDLY]
        
        elif self.active_prompt_version == PromptVersion.V2:
            # Enhanced prompts
            templates["system"] = THAI_SYSTEM_PROMPTS[ThaiTone.FRIENDLY]
            templates["melasma"] = MELASMA_THAI_PROMPT
            templates["acne"] = ACNE_THAI_PROMPT
        
        return templates
    
    async def generate_response_v2(
        self,
        user_question: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        tone: ThaiTone = ThaiTone.FRIENDLY,
        force_tone: bool = False
    ) -> GenerationResult:
        """
        Generate a response with Thai language optimization.
        """
        import time
        start_time = time.time()
        
        # 1. Detect intent and select appropriate tone
        detected_tone = self._detect_tone(user_question) if not force_tone else tone
        
        # 2. Build optimized prompt
        prompt = self._build_optimized_prompt(
            user_question=user_question,
            context=context,
            conversation_history=conversation_history,
            tone=detected_tone
        )
        
        # 3. Try generation with fallbacks
        result = await self._generate_with_fallbacks(prompt, user_question)
        
        # 4. Validate response
        validation = validate_thai_response(result.text)
        result.validation_score = 1.0 if validation["valid"] else 0.5
        
        if validation["warnings"]:
            logger.debug(f"Response warnings: {validation['warnings']}")
        
        if not validation["valid"]:
            logger.warning(f"Response validation failed: {validation['errors']}")
            # Try regeneration with stricter instructions
            result = await self._regenerate_with_constraints(
                prompt, validation["errors"], user_question
            )
        
        # 5. Track for quality improvement
        self._track_response(user_question, result, validation)
        
        return result
    
    def _detect_tone(self, text: str) -> ThaiTone:
        """Detect the appropriate tone based on user message."""
        text_lower = text.lower()
        
        # Detect purchase intent
        purchase_keywords = ["สนใจ", "ซื้อ", "สั่ง", "ราคา", "เอา", "cf"]
        if any(kw in text_lower for kw in purchase_keywords):
            return ThaiTone.ENERGETIC
        
        # Detect emotional distress about skin
        distress_keywords = ["ท้อ", "เครียด", "หมดหวัง", "แย่", "ไม่ไหว", "ช่วยด้วย"]
        if any(kw in text_lower for kw in distress_keywords):
            return ThaiTone.EMPATHETIC
        
        # Detect casual chat
        casual_keywords = ["555", "ฮา", "น่ารัก", "สวย", "ชอบ"]
        if any(kw in text_lower for kw in casual_keywords):
            return ThaiTone.FRIENDLY
        
        return ThaiTone.FRIENDLY  # Default
    
    def _build_optimized_prompt(
        self,
        user_question: str,
        context: str,
        conversation_history: Optional[List[Dict]],
        tone: ThaiTone
    ) -> str:
        """Build an optimized prompt for Thai response generation."""
        
        # Start with system prompt for the tone
        system_prompt = THAI_SYSTEM_PROMPTS.get(tone, THAI_SYSTEM_PROMPTS[ThaiTone.FRIENDLY])
        
        # Add condition-specific guidance
        condition_prompt = self._get_condition_prompt(user_question)
        
        # Build conversation context
        history_text = ""
        if conversation_history:
            history_text = "\n\n### ประวัติการสนทนา\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = "ลูกค้า" if msg.get("is_user") else "ดี"
                history_text += f"{role}: {msg.get('text', '')}\n"
        
        # Assemble final prompt
        prompt = f"""{system_prompt}

{condition_prompt}

### ข้อมูลสินค้าและบริบท
{context}
{history_text}

### คำถามลูกค้า
{user_question}

### คำตอบ (ตอบเป็นภาษาไทยล้วน กระชับ ใช้อิโมจิแต่พอดี):
"""
        return prompt
    
    def _get_condition_prompt(self, text: str) -> str:
        """Get condition-specific guidance based on keywords."""
        text_lower = text.lower()
        
        # Check for melasma
        if any(kw in text_lower for kw in ["ฝ้า", "จุดด่างดำ", "หมองคล้ำ"]):
            return MELASMA_THAI_PROMPT
        
        # Check for acne
        if any(kw in text_lower for kw in ["สิว", "หัวดำ", "อักเสบ"]):
            return ACNE_THAI_PROMPT
        
        return ""
    
    async def _generate_with_fallbacks(
        self,
        prompt: str,
        original_question: str
    ) -> GenerationResult:
        """Generate with model fallbacks for reliability."""
        
        models_to_try = [self.model] + [m for m in self.fallback_models if m != self.model]
        
        for model in models_to_try:
            try:
                import time
                start = time.time()
                
                if self.use_openrouter:
                    text = await self._generate_openrouter(prompt, model)
                else:
                    text = await self._generate_direct(prompt, model)
                
                latency = (time.time() - start) * 1000
                
                if text and len(text.strip()) > 10:
                    return GenerationResult(
                        text=text.strip(),
                        model=model,
                        latency_ms=latency,
                        prompt_version=self.active_prompt_version.value
                    )
                
            except Exception as e:
                logger.warning(f"Generation failed with {model}: {e}")
                continue
        
        # All models failed, return fallback
        return GenerationResult(
            text=self._get_fallback_response(original_question),
            model="fallback",
            latency_ms=0,
            prompt_version="fallback"
        )
    
    async def _generate_openrouter(self, prompt: str, model: str) -> str:
        """Generate via OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "https://dplusskin.com",
            "X-Title": "D Plus Skin AI",
        }
        
        request_data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                raise Exception(f"OpenRouter error: {response.status_code}")
    
    async def _generate_direct(self, prompt: str, model: str) -> str:
        """Generate via direct Google Gemini API."""
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        
        model = genai.GenerativeModel(model.replace("google/", ""))
        response = model.generate_content(prompt)
        return response.text
    
    async def _regenerate_with_constraints(
        self,
        original_prompt: str,
        errors: List[str],
        user_question: str
    ) -> GenerationResult:
        """Regenerate with stricter constraints if validation failed."""
        
        constraint_prompt = original_prompt + f"""

### ⚠️ คำเตือน (แก้ไขข้อผิดพลาดนี้)
ข้อความก่อนหน้ามีปัญหา: {', '.join(errors)}

กรุณาตอบใหม่โดย:
- ใช้ภาษาไทยล้วน (ไม่มีภาษาอังกฤษ)
- สั้นกระชับ ไม่เกิน 2 ประโยค
- ใช้ "ค่ะ" หรือ "ครับ" ลงท้าย
"""
        
        return await self._generate_with_fallbacks(constraint_prompt, user_question)
    
    def _get_fallback_response(self, question: str) -> str:
        """Get context-aware fallback response."""
        question_lower = question.lower()
        
        if "ฝ้า" in question_lower:
            return "สำหรับปัญหาฝ้า แนะนำเอ็กโซเจน แอมพูลค่ะ ช่วยลดฝ้าได้ดี ทักมาสอบถามเพิ่มเติมได้นะคะ 💕"
        
        if "สิว" in question_lower:
            return "สิวต้องดูแลตั้งแต่ขั้นตอนล้างหน้าค่ะ แนะนำสบู่ซากุระ + แลคโต้ เอ็กซ์ตร้า ทักมาคุยรายละเอียดได้ค่ะ ✨"
        
        return "สนใจสินค้าตัวไหน ทักไลน์มาถามได้เลยนะคะ 👉 @dplusskin 💕"
    
    def _track_response(
        self,
        question: str,
        result: GenerationResult,
        validation: Dict
    ):
        """Track response for quality monitoring."""
        self._response_history.append({
            "question": question[:100],
            "response": result.text[:200],
            "model": result.model,
            "latency_ms": result.latency_ms,
            "validation": validation,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Trim history
        if len(self._response_history) > self._max_history:
            self._response_history = self._response_history[-self._max_history:]
    
    def get_quality_metrics(self) -> Dict:
        """Get quality metrics for monitoring."""
        if not self._response_history:
            return {}
        
        total = len(self._response_history)
        valid = sum(1 for r in self._response_history if r["validation"]["valid"])
        avg_latency = sum(r["latency_ms"] for r in self._response_history) / total
        
        model_distribution = {}
        for r in self._response_history:
            model = r["model"]
            model_distribution[model] = model_distribution.get(model, 0) + 1
        
        return {
            "total_responses": total,
            "valid_rate": valid / total,
            "avg_latency_ms": avg_latency,
            "model_distribution": model_distribution
        }
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Create `services/facebook_errors.py` with error registry | High | 1 day | Backend |
| Implement `TokenManager` with refresh logic | High | 2 days | Backend |
| Add unit tests for error classification | High | 1 day | QA |
| Update environment configuration for token management | Medium | 0.5 day | DevOps |

### Phase 2: Circuit Breaker & Rate Limiting (Week 2-3)

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Implement `CircuitBreaker` class | High | 2 days | Backend |
| Implement `RateLimiterV2` with adaptive throttling | High | 3 days | Backend |
| Integrate circuit breaker into FacebookServiceV2 | High | 2 days | Backend |
| Add metrics endpoints for circuit breaker status | Medium | 1 day | Backend |
| Load testing for rate limiter performance | Medium | 1 day | QA |

### Phase 3: Thai Language Optimization (Week 3-4)

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Create `services/prompts/` module structure | High | 0.5 day | Backend |
| Implement Thai prompt templates with tones | High | 2 days | Content/Backend |
| Build `GeminiServiceV2` with validation | High | 3 days | Backend |
| Add response quality tracking | Medium | 1 day | Backend |
| A/B testing setup for prompt versions | Medium | 2 days | Backend |

### Phase 4: Integration & Migration (Week 4-5)

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Create backward-compatible service wrappers | High | 2 days | Backend |
| Update `main.py` service initialization | High | 1 day | Backend |
| Feature flags for gradual rollout | High | 1 day | Backend |
| Integration testing with Facebook sandbox | High | 2 days | QA |
| Documentation updates | Medium | 1 day | Tech Writer |

### Phase 5: Monitoring & Optimization (Week 5-6)

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Deploy to staging environment | High | 1 day | DevOps |
| Monitor error rates and response quality | High | Ongoing | Backend |
| Fine-tune adaptive rate limits | Medium | 2 days | Backend |
| Prompt optimization based on feedback | Medium | Ongoing | Content |
| Production rollout with feature flags | High | 1 day | DevOps |

---

## File Structure

```
/home/tk578/fb-bot/
├── services/
│   ├── __init__.py
│   ├── facebook_service.py           # Current (deprecated)
│   ├── facebook_service_v2.py        # NEW: Enhanced with error handling
│   ├── facebook_errors.py            # NEW: Error classification
│   ├── token_manager.py              # NEW: Token lifecycle management
│   ├── circuit_breaker.py            # NEW: Circuit breaker pattern
│   ├── rate_limiter.py               # Current (deprecated)
│   ├── rate_limiter_v2.py            # NEW: Adaptive rate limiting
│   ├── gemini_service.py             # Current (deprecated)
│   ├── gemini_service_v2.py          # NEW: Thai-optimized generation
│   ├── prompts/                      # NEW: Prompt engineering module
│   │   ├── __init__.py
│   │   ├── thai_prompts.py           # Thai prompts and validation
│   │   ├── tone_configs.py           # Tone configurations
│   │   └── condition_prompts.py      # Condition-specific guidance
│   ├── knowledge_base.py             # Unchanged
│   └── memory_service.py             # Unchanged
├── config/
│   ├── settings.py                   # Update for new config options
│   ├── constants.py                  # Add error codes
│   └── feature_flags.py              # NEW: Feature flag management
├── tests/
│   ├── unit/
│   │   ├── test_facebook_errors.py   # NEW
│   │   ├── test_circuit_breaker.py   # NEW
│   │   ├── test_rate_limiter_v2.py   # NEW
│   │   └── test_thai_prompts.py      # NEW
│   └── integration/
│       └── test_facebook_service_v2.py # NEW
├── monitoring/
│   ├── __init__.py
│   ├── metrics.py                    # NEW: Custom metrics
│   └── alerts.py                     # NEW: Alert configurations
└── dev-team/
    └── alpha/
        └── output/
            └── spec.md               # This document
```

---

## Security Considerations

### 6.1 Token Security

| Concern | Mitigation |
|---------|------------|
| Token exposure in logs | Redact tokens in all log output; use token prefixes only |
| Token refresh race conditions | Implement distributed locking for token refresh |
| Token storage | Continue using environment variables; never commit tokens |
| Long-lived token exposure | Implement token rotation schedule (quarterly) |

### 6.2 Rate Limiting Security

| Concern | Mitigation |
|---------|------------|
| Circuit breaker bypass | All service calls must go through circuit breaker |
| Rate limit spoofing | Validate X-App-Usage headers against known patterns |
| DoS via rate limit exhaustion | Implement per-user rate limiting in addition to global |

### 6.3 API Security

| Concern | Mitigation |
|---------|------------|
| appsecret_proof verification | Continue generating for all API calls |
| Webhook verification | Maintain verify_token check |
| Request payload validation | Validate all incoming webhook payloads |
| Error information leakage | Return generic errors to clients; log detailed internally |

### 6.4 Data Privacy (Thai Context)

| Concern | Mitigation |
|---------|------------|
| Customer message logging | Anonymize user IDs in logs; encrypt at rest |
| PII in AI prompts | Strip identifying information before sending to Gemini |
| Conversation history | Implement retention policy (30 days default) |
| Thai personal data (PDPA) | Ensure compliance with Thailand's PDPA regulations |

---

## Success Metrics

### 7.1 Error Handling

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Token expiration failures | Unknown | 0 | Error logs |
| Unhandled API errors | Unknown | < 0.1% | Error tracking |
| Successful retry rate | ~60% | > 80% | Request logs |
| Mean time to recovery | Unknown | < 2 min | Incident tracking |

### 7.2 Rate Limiting

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Rate limit violations | ~5/day | 0 | API responses |
| Circuit breaker activations | N/A | < 2/week | Service metrics |
| Adaptive rate accuracy | N/A | ±10% of optimal | Latency vs rate correlation |
| Message throughput | ~50/hour | 100/hour | Business metrics |

### 7.3 Response Quality

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Thai validation pass rate | ~70% | > 95% | Automated validation |
| Average response length | Variable | 50-150 chars | Response analysis |
| Customer satisfaction | Unknown | > 4.0/5 | Manual sampling |
| Response latency (p95) | ~5s | < 3s | Performance metrics |

---

## Appendix A: Migration Guide

### A.1 Service Initialization Changes

**Before:**
```python
# main.py
from services.facebook_service import get_facebook_service
from services.rate_limiter import get_rate_limiter

rate_limiter = get_rate_limiter()
facebook_service = get_facebook_service(rate_limiter)
```

**After:**
```python
# main.py
from services.facebook_service_v2 import FacebookServiceV2
from services.token_manager import TokenManager
from services.circuit_breaker import CircuitBreaker
from services.rate_limiter_v2 import RateLimiterV2

# Initialize new services
token_manager = TokenManager(
    app_id=settings.facebook_app_id,
    app_secret=settings.facebook_app_secret,
    initial_token=settings.facebook_page_access_token
)

circuit_breaker = CircuitBreaker()
rate_limiter = RateLimiterV2()

facebook_service = FacebookServiceV2(
    token_manager=token_manager,
    circuit_breaker=circuit_breaker,
    rate_limiter=rate_limiter
)
```

### A.2 Feature Flags

```python
# config/feature_flags.py
from pydantic_settings import BaseSettings

class FeatureFlags(BaseSettings):
    use_enhanced_error_handling: bool = False
    use_circuit_breaker: bool = False
    use_adaptive_rate_limiter: bool = False
    use_thai_prompt_v2: bool = False
    enable_response_validation: bool = False
```

### A.3 Rollback Plan

If issues occur in production:

1. Set feature flags to `false` in environment
2. Restart services
3. Monitor error rates
4. Investigate root cause in staging

---

## Appendix B: Testing Strategy

### B.1 Unit Tests

```python
# tests/unit/test_circuit_breaker.py
import pytest
from services.circuit_breaker import CircuitBreaker, CircuitState

class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.can_execute("test_endpoint")
    
    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure("test_endpoint")
        assert not cb.can_execute("test_endpoint")
    
    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, timeout_seconds=0)
        cb.record_failure("test_endpoint")
        time.sleep(0.1)
        assert cb.can_execute("test_endpoint")
```

### B.2 Integration Tests

```python
# tests/integration/test_facebook_service_v2.py
import pytest
from services.facebook_service_v2 import FacebookServiceV2
from services.facebook_errors import FacebookErrorCategory

@pytest.mark.asyncio
class TestFacebookServiceV2:
    async def test_token_refresh_on_auth_error(self):
        # Mock expired token response
        pass
    
    async def test_circuit_breaker_on_rate_limit(self):
        # Test circuit opens after rate limit errors
        pass
```

### B.3 Load Testing

```python
# scripts/load_test.py
import asyncio
import aiohttp
import time

async def test_rate_limiter():
    """Test rate limiter under load."""
    limiter = RateLimiterV2()
    
    async def make_request():
        if limiter.check("messenger_send"):
            await asyncio.sleep(0.01)  # Simulate API call
            return True
        return False
    
    # Fire 1000 requests
    tasks = [make_request() for _ in range(1000)]
    results = await asyncio.gather(*tasks)
    
    success_rate = sum(results) / len(results)
    print(f"Success rate: {success_rate:.2%}")
```

---

**Document End**
