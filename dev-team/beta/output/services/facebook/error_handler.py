"""
Centralized Facebook Error Handler.

Provides structured error handling with categorized response strategies,
circuit breaker integration, and safe error messaging.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
from loguru import logger

from services.facebook.errors import (
    ErrorClassifier,
    FacebookError,
    ErrorCategory,
    FacebookAPIError,
    RateLimitError,
    TokenExpiredError,
    AuthenticationError
)


class ActionType(Enum):
    """Action to take after error classification."""
    RETRY = auto()           # Retry the request
    RETRY_WITH_BACKOFF = auto()  # Retry with exponential backoff
    FAIL = auto()            # Fail and return error
    REAUTH = auto()          # Require re-authentication
    CIRCUIT_BREAK = auto()   # Open circuit breaker
    IGNORE = auto()          # Ignore error (e.g., duplicate)


@dataclass
class ErrorAction:
    """Recommended action for handling an error."""
    action: ActionType
    delay_seconds: Optional[int] = None
    safe_message: str = ""
    should_log: bool = True
    should_alert: bool = False


class ErrorHandler:
    """
    Centralized error handler for Facebook API operations.
    
    Provides:
    - Error classification
    - Action determination based on category
    - Safe error messages for users
    - Circuit breaker integration
    
    Usage:
        handler = ErrorHandler()
        action = await handler.handle(api_error, context)
        if action.action == ActionType.RETRY:
            await retry_with_delay(action.delay_seconds)
    """
    
    # Category to action mapping
    CATEGORY_ACTIONS: Dict[ErrorCategory, Dict[str, Any]] = {
        ErrorCategory.AUTHENTICATION: {
            "action": ActionType.REAUTH,
            "alert": True,
        },
        ErrorCategory.RATE_LIMIT: {
            "action": ActionType.RETRY_WITH_BACKOFF,
            "default_delay": 60,
            "alert": False,
        },
        ErrorCategory.TRANSIENT: {
            "action": ActionType.RETRY_WITH_BACKOFF,
            "default_delay": 5,
            "alert": False,
        },
        ErrorCategory.NETWORK: {
            "action": ActionType.RETRY_WITH_BACKOFF,
            "default_delay": 5,
            "alert": False,
        },
        ErrorCategory.SERVER: {
            "action": ActionType.RETRY_WITH_BACKOFF,
            "default_delay": 10,
            "alert": False,
        },
        ErrorCategory.CLIENT: {
            "action": ActionType.FAIL,
            "alert": False,
        },
        ErrorCategory.UNKNOWN: {
            "action": ActionType.FAIL,
            "alert": True,
        },
    }
    
    def __init__(self):
        self.classifier = ErrorClassifier()
        self._error_counts: Dict[str, int] = {}
    
    async def handle(
        self, 
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorAction:
        """
        Determine action based on error type and context.
        
        Args:
            error: The exception that occurred
            context: Additional context about the request
            
        Returns:
            ErrorAction with recommended handling strategy
        """
        context = context or {}
        operation = context.get("operation", "unknown")
        
        # Classify the error
        if isinstance(error, FacebookError):
            fb_error = error
        elif isinstance(error, dict):
            # Raw response data
            fb_error = self.classifier.classify_from_response(error)
        else:
            # Exception
            fb_error = self.classifier.classify_from_exception(error)
        
        # Get safe message
        safe_message = self.classifier.get_safe_error_message(fb_error)
        
        # Get action configuration for category
        action_config = self.CATEGORY_ACTIONS.get(fb_error.category, {})
        action_type = action_config.get("action", ActionType.FAIL)
        
        # Determine delay
        delay = fb_error.retry_after
        if delay is None:
            delay = action_config.get("default_delay")
        
        # Check for special cases
        if fb_error.category == ErrorCategory.RATE_LIMIT:
            # Check if we've had too many rate limit errors recently
            self._increment_error_count("rate_limit")
            if self._get_error_count("rate_limit") > 5:
                logger.error("Too many rate limit errors - opening circuit breaker")
                action_type = ActionType.CIRCUIT_BREAK
        
        # Check for authentication errors requiring immediate attention
        if fb_error.category == ErrorCategory.AUTHENTICATION:
            logger.critical(f"Authentication error: {fb_error.message}")
            # Could trigger alert/notification here
        
        # Log the error
        if action_config.get("alert", False):
            logger.error(
                f"Facebook API Error [{operation}]: "
                f"code={fb_error.code}, category={fb_error.category.name}, "
                f"message={fb_error.message}"
            )
        else:
            logger.warning(
                f"Facebook API Error [{operation}]: "
                f"code={fb_error.code}, category={fb_error.category.name}"
            )
        
        return ErrorAction(
            action=action_type,
            delay_seconds=delay,
            safe_message=safe_message,
            should_log=True,
            should_alert=action_config.get("alert", False)
        )
    
    async def handle_api_response(
        self,
        response_data: Dict[str, Any],
        status_code: int,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorAction:
        """
        Handle error from API response data.
        
        Args:
            response_data: Parsed JSON response
            status_code: HTTP status code
            context: Request context
            
        Returns:
            ErrorAction with handling strategy
        """
        fb_error = self.classifier.classify_from_response(response_data, status_code)
        
        # Create synthetic exception for handle() method
        class SyntheticError(Exception):
            pass
        
        synthetic = SyntheticError(fb_error.message)
        return await self.handle(synthetic, {**context, "error_data": response_data})
    
    def _increment_error_count(self, error_type: str):
        """Track error frequency."""
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
    
    def _get_error_count(self, error_type: str) -> int:
        """Get error count."""
        return self._error_counts.get(error_type, 0)
    
    def reset_error_counts(self):
        """Reset error tracking."""
        self._error_counts = {}
    
    def get_safe_message(self, error: Exception) -> str:
        """
        Get user-safe error message for any exception.
        
        Args:
            error: The exception
            
        Returns:
            Thai error message safe for users
        """
        if isinstance(error, FacebookError):
            return self.classifier.get_safe_error_message(error)
        
        fb_error = self.classifier.classify_from_exception(error)
        return self.classifier.get_safe_error_message(fb_error)


# Decorator for automatic error handling
def with_error_handler(operation_name: str):
    """
    Decorator to automatically handle errors in Facebook API methods.
    
    Usage:
        @with_error_handler("send_message")
        async def send_message(self, ...):
            # API call
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            handler = ErrorHandler()
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {"operation": operation_name, "args": args, "kwargs": kwargs}
                action = await handler.handle(e, context)
                
                if action.action == ActionType.RETRY:
                    # Re-raise for tenacity to handle
                    raise
                elif action.action == ActionType.FAIL:
                    raise FacebookAPIError(action.safe_message)
                elif action.action == ActionType.REAUTH:
                    raise AuthenticationError(action.safe_message)
                else:
                    # Other actions - log and return failure
                    logger.error(f"Error in {operation_name}: {action.safe_message}")
                    return False
        return wrapper
    return decorator


# Singleton instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler
