"""
Facebook Service Module.

Provides comprehensive Facebook Graph API integration with:
- Error classification and handling
- Token lifecycle management
- Circuit breaker protection
- Rate limiting integration
"""

from services.facebook.errors import (
    ErrorCategory,
    FacebookError,
    ErrorClassifier,
    FacebookAPIError,
    RateLimitError,
    TokenExpiredError,
    AuthenticationError,
)

from services.facebook.token_manager import (
    TokenManager,
    TokenInfo,
    get_token_manager,
)

from services.facebook.error_handler import (
    ErrorHandler,
    ErrorAction,
    ActionType,
    get_error_handler,
    with_error_handler,
)

__all__ = [
    # Errors
    "ErrorCategory",
    "FacebookError",
    "ErrorClassifier",
    "FacebookAPIError",
    "RateLimitError",
    "TokenExpiredError",
    "AuthenticationError",
    # Token Manager
    "TokenManager",
    "TokenInfo",
    "get_token_manager",
    # Error Handler
    "ErrorHandler",
    "ErrorAction",
    "ActionType",
    "get_error_handler",
    "with_error_handler",
]
