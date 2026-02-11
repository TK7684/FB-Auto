"""
Enhanced Rate Limiter with Circuit Breaker Integration.

Combines file-based rate limiting with circuit breaker protection
to prevent cascade failures and handle rate limits gracefully.
"""

from typing import Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from services.rate_limiter import RateLimiter as FileBasedLimiter
from services.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerOpenError,
    get_facebook_circuit
)
from services.facebook.errors import ErrorCategory, ErrorClassifier


class RateLimitResult(Enum):
    """Result of rate limit check."""
    ALLOWED = "allowed"
    LIMITED = "limited"
    CIRCUIT_OPEN = "circuit_open"
    PANIC_MODE = "panic_mode"


@dataclass
class RateLimitStatus:
    """Status of rate limiting."""
    result: RateLimitResult
    allowed: bool
    message: str
    retry_after: Optional[int] = None
    circuit_state: Optional[str] = None


class EnhancedRateLimiter:
    """
    Enhanced rate limiter with circuit breaker protection.
    
    Combines:
    - File-based rate limiting (cross-process)
    - Circuit breaker pattern (per API type)
    - Metrics and monitoring
    
    Usage:
        limiter = EnhancedRateLimiter()
        
        result = await limiter.execute(
            api_type="messages",
            func=send_message,
            recipient_id=user_id,
            message_text=text
        )
    """
    
    def __init__(self):
        """Initialize enhanced rate limiter."""
        self.file_limiter = FileBasedLimiter()
        self.error_classifier = ErrorClassifier()
        
        # Circuit breakers for different API types
        self._circuits: Dict[str, CircuitBreaker] = {}
        
        # Initialize circuits
        for api_type in ["messages", "comments", "private_replies", "insights"]:
            self._circuits[api_type] = get_facebook_circuit(api_type)
        
        logger.info("EnhancedRateLimiter initialized with circuit breakers")
    
    def check_rate_limit(self, api_type: str = "default") -> RateLimitStatus:
        """
        Check if request is allowed by rate limits.
        
        Args:
            api_type: Type of API request
            
        Returns:
            RateLimitStatus with result details
        """
        # Check circuit breaker state first
        circuit = self._circuits.get(api_type)
        if circuit and circuit.state.name == "OPEN":
            return RateLimitStatus(
                result=RateLimitResult.CIRCUIT_OPEN,
                allowed=False,
                message="Circuit breaker is open - too many failures",
                circuit_state=circuit.state.name
            )
        
        # Check file-based rate limit
        if not self.file_limiter.check_and_increment():
            return RateLimitStatus(
                result=RateLimitResult.LIMITED,
                allowed=False,
                message="Rate limit exceeded",
                retry_after=60  # Estimate
            )
        
        return RateLimitStatus(
            result=RateLimitResult.ALLOWED,
            allowed=True,
            message="Request allowed"
        )
    
    async def execute(
        self,
        api_type: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with rate limiting and circuit breaker protection.
        
        Flow:
        1. Check file-based rate limits
        2. Check circuit breaker state
        3. Execute with error tracking
        4. Update metrics
        
        Args:
            api_type: Type of API (messages, comments, private_replies, insights)
            func: Async function to execute
            *args, **kwargs: Arguments for function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            RateLimitExceeded: If rate limit reached
        """
        # 1. Check file-based rate limit
        if not self.file_limiter.check_and_increment():
            logger.warning(f"Rate limit reached for {api_type}")
            raise RateLimitExceeded("Global rate limit reached")
        
        # 2. Get circuit breaker
        circuit = self._circuits.get(api_type)
        
        # 3. Execute with circuit protection
        if circuit:
            try:
                return await circuit.call(func, *args, **kwargs)
            except CircuitBreakerOpenError:
                logger.error(f"Circuit breaker open for {api_type}")
                raise
            except Exception as e:
                # Classify error and potentially trigger circuit breaker
                fb_error = self.error_classifier.classify_from_exception(e)
                
                if fb_error.category == ErrorCategory.RATE_LIMIT:
                    logger.warning(f"Rate limit error in {api_type}, triggering panic")
                    self.file_limiter.trigger_panic()
                
                raise
        else:
            # No circuit breaker - execute directly
            return await func(*args, **kwargs)
    
    def get_circuit_state(self, api_type: str) -> Optional[Dict[str, Any]]:
        """
        Get circuit breaker state for API type.
        
        Args:
            api_type: Type of API
            
        Returns:
            Circuit state dictionary or None
        """
        circuit = self._circuits.get(api_type)
        if circuit:
            return circuit.get_state_dict()
        return None
    
    def get_all_circuit_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all circuit breaker states."""
        return {
            api_type: circuit.get_state_dict()
            for api_type, circuit in self._circuits.items()
        }
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        state = self.file_limiter._load_state()
        return {
            "comments_this_hour": state.get("comments_this_hour", 0),
            "hour_start_ts": state.get("hour_start_ts", 0),
            "panic_until_ts": state.get("panic_until_ts", 0),
            "last_action_ts": state.get("last_action_ts", 0),
            "circuits": self.get_all_circuit_states()
        }
    
    def trigger_panic(self):
        """Trigger global panic mode."""
        self.file_limiter.trigger_panic()
    
    def reset_circuit(self, api_type: str):
        """Reset circuit breaker for API type."""
        circuit = self._circuits.get(api_type)
        if circuit:
            circuit.force_close()
            logger.info(f"Reset circuit breaker for {api_type}")


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


# Singleton instance
_enhanced_limiter: Optional[EnhancedRateLimiter] = None


def get_enhanced_rate_limiter() -> EnhancedRateLimiter:
    """Get global enhanced rate limiter instance."""
    global _enhanced_limiter
    if _enhanced_limiter is None:
        _enhanced_limiter = EnhancedRateLimiter()
    return _enhanced_limiter
