"""
Facebook API Error Taxonomy and Classification.

This module defines a comprehensive error classification system for Facebook API errors,
enabling appropriate handling strategies based on error categories.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Dict, Any
import re


class ErrorCategory(Enum):
    """Categories of Facebook API errors for targeted handling."""
    AUTHENTICATION = auto()      # Token expired, invalid, permissions
    RATE_LIMIT = auto()          # Throttling, quota exceeded
    TRANSIENT = auto()           # Temporary failures, worth retrying
    CLIENT = auto()              # Bad request, invalid parameters
    SERVER = auto()              # Facebook server errors
    NETWORK = auto()             # DNS, timeout, connection issues
    UNKNOWN = auto()             # Unclassified errors


@dataclass
class FacebookError:
    """
    Structured Facebook API error with classification metadata.
    
    Attributes:
        code: Facebook error code (if available)
        message: Human-readable error message
        category: Classified error category
        is_retryable: Whether the request should be retried
        retry_after: Seconds to wait before retry (from headers)
        requires_reauth: Whether re-authentication is required
        subcode: Facebook error subcode (if available)
        fbtrace_id: Facebook trace ID for debugging
    """
    code: Optional[int] = None
    message: str = "Unknown error"
    category: ErrorCategory = ErrorCategory.UNKNOWN
    is_retryable: bool = False
    retry_after: Optional[int] = None
    requires_reauth: bool = False
    subcode: Optional[int] = None
    fbtrace_id: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


# Facebook Error Code Mapping
# Reference: https://developers.facebook.com/docs/graph-api/guides/error-handling
ERROR_CODE_MAP: Dict[int, Dict[str, Any]] = {
    # Authentication errors (require re-auth)
    102: {"category": ErrorCategory.AUTHENTICATION, "retryable": False, "reauth": True,
          "description": "Session expired"},
    190: {"category": ErrorCategory.AUTHENTICATION, "retryable": False, "reauth": True,
          "description": "Access token expired"},
    191: {"category": ErrorCategory.AUTHENTICATION, "retryable": False, "reauth": True,
          "description": "Access token has expired"},
    
    # Rate limit errors (retryable with backoff)
    4: {"category": ErrorCategory.RATE_LIMIT, "retryable": True, "reauth": False,
        "description": "App rate limit reached"},
    17: {"category": ErrorCategory.RATE_LIMIT, "retryable": True, "reauth": False,
         "description": "User rate limit reached"},
    32: {"category": ErrorCategory.RATE_LIMIT, "retryable": True, "reauth": False,
         "description": "Page request limit reached"},
    613: {"category": ErrorCategory.RATE_LIMIT, "retryable": True, "reauth": False,
          "description": "API throttling"},
    80000: {"category": ErrorCategory.RATE_LIMIT, "retryable": True, "reauth": False,
            "description": "Page rate limit (Business Use Case)"},
    80001: {"category": ErrorCategory.RATE_LIMIT, "retryable": True, "reauth": False,
            "description": "Page rate limit (Page token)"},
    80004: {"category": ErrorCategory.RATE_LIMIT, "retryable": True, "reauth": False,
            "description": "Too many messages to single thread"},
    80006: {"category": ErrorCategory.RATE_LIMIT, "retryable": True, "reauth": False,
            "description": "Messenger rate limit"},
    
    # Transient errors (retryable)
    2: {"category": ErrorCategory.TRANSIENT, "retryable": True, "reauth": False,
        "description": "Service temporarily unavailable"},
    1200: {"category": ErrorCategory.TRANSIENT, "retryable": True, "reauth": False,
           "description": "Temporary error"},
    
    # Server errors (may be retryable)
    500: {"category": ErrorCategory.SERVER, "retryable": True, "reauth": False,
          "description": "Internal server error"},
    503: {"category": ErrorCategory.SERVER, "retryable": True, "reauth": False,
          "description": "Service unavailable"},
    
    # Client errors (not retryable)
    100: {"category": ErrorCategory.CLIENT, "retryable": False, "reauth": False,
          "description": "Invalid parameter"},
    200: {"category": ErrorCategory.CLIENT, "retryable": False, "reauth": False,
          "description": "Permissions error"},
    803: {"category": ErrorCategory.CLIENT, "retryable": False, "reauth": False,
          "description": "Object not found"},
}

# Network error patterns mapped to categories
NETWORK_ERROR_PATTERNS: Dict[str, Dict[str, Any]] = {
    "ETIMEDOUT": {"category": ErrorCategory.NETWORK, "retryable": True},
    "ECONNRESET": {"category": ErrorCategory.NETWORK, "retryable": True},
    "ECONNREFUSED": {"category": ErrorCategory.NETWORK, "retryable": True},
    "EHOSTUNREACH": {"category": ErrorCategory.NETWORK, "retryable": True},
    "DNS_ERROR": {"category": ErrorCategory.NETWORK, "retryable": True},
    "TimeoutException": {"category": ErrorCategory.NETWORK, "retryable": True},
    "ConnectTimeout": {"category": ErrorCategory.NETWORK, "retryable": True},
    "ReadTimeout": {"category": ErrorCategory.NETWORK, "retryable": True},
    "SSL": {"category": ErrorCategory.NETWORK, "retryable": True},
}


class ErrorClassifier:
    """
    Classifies Facebook API errors into appropriate categories.
    
    Usage:
        classifier = ErrorClassifier()
        error = classifier.classify_from_response(api_response)
        if error.category == ErrorCategory.RATE_LIMIT:
            # Handle rate limit
    """
    
    def __init__(self):
        self.error_map = ERROR_CODE_MAP
        self.network_patterns = NETWORK_ERROR_PATTERNS
    
    def classify_from_response(
        self, 
        response_data: Dict[str, Any],
        status_code: Optional[int] = None
    ) -> FacebookError:
        """
        Classify an error from Facebook API response JSON.
        
        Args:
            response_data: Parsed JSON response containing 'error' key
            status_code: HTTP status code
            
        Returns:
            Classified FacebookError instance
        """
        error_data = response_data.get("error", {})
        
        code = error_data.get("code")
        message = error_data.get("message", "Unknown error")
        subcode = error_data.get("error_subcode")
        fbtrace_id = error_data.get("fbtrace_id")
        
        # Get retry_after from error data or headers
        retry_after = error_data.get("error_data", {}).get("retry_after")
        
        # Look up error code in mapping
        if code in self.error_map:
            mapping = self.error_map[code]
            return FacebookError(
                code=code,
                message=message,
                category=mapping["category"],
                is_retryable=mapping["retryable"],
                retry_after=retry_after,
                requires_reauth=mapping.get("reauth", False),
                subcode=subcode,
                fbtrace_id=fbtrace_id,
                raw_response=response_data
            )
        
        # Handle HTTP status code-based classification
        if status_code:
            if status_code >= 500:
                return FacebookError(
                    code=code or status_code,
                    message=message,
                    category=ErrorCategory.SERVER,
                    is_retryable=True,
                    retry_after=retry_after,
                    subcode=subcode,
                    fbtrace_id=fbtrace_id,
                    raw_response=response_data
                )
            elif status_code >= 400:
                return FacebookError(
                    code=code or status_code,
                    message=message,
                    category=ErrorCategory.CLIENT,
                    is_retryable=False,
                    subcode=subcode,
                    fbtrace_id=fbtrace_id,
                    raw_response=response_data
                )
        
        # Unknown error
        return FacebookError(
            code=code,
            message=message,
            category=ErrorCategory.UNKNOWN,
            is_retryable=False,
            subcode=subcode,
            fbtrace_id=fbtrace_id,
            raw_response=response_data
        )
    
    def classify_from_exception(self, exception: Exception) -> FacebookError:
        """
        Classify an exception into appropriate error category.
        
        Args:
            exception: The exception to classify
            
        Returns:
            Classified FacebookError instance
        """
        exception_type = type(exception).__name__
        exception_str = str(exception)
        
        # Check for network-related errors
        for pattern, mapping in self.network_patterns.items():
            if pattern in exception_type or pattern in exception_str:
                return FacebookError(
                    code=None,
                    message=f"Network error: {exception_str}",
                    category=mapping["category"],
                    is_retryable=mapping["retryable"],
                    retry_after=5  # Default 5s for network errors
                )
        
        # Check for specific exception types
        if "Timeout" in exception_type or "timeout" in exception_str.lower():
            return FacebookError(
                code=None,
                message=f"Timeout: {exception_str}",
                category=ErrorCategory.NETWORK,
                is_retryable=True,
                retry_after=5
            )
        
        if "Connection" in exception_type:
            return FacebookError(
                code=None,
                message=f"Connection error: {exception_str}",
                category=ErrorCategory.NETWORK,
                is_retryable=True,
                retry_after=5
            )
        
        # Check for SSL errors
        if "SSL" in exception_type or "TLS" in exception_type or "Certificate" in exception_type:
            return FacebookError(
                code=None,
                message=f"SSL/TLS error: {exception_str}",
                category=ErrorCategory.NETWORK,
                is_retryable=True,
                retry_after=10
            )
        
        # Default: unknown error
        return FacebookError(
            code=None,
            message=f"Unexpected error: {exception_str}",
            category=ErrorCategory.UNKNOWN,
            is_retryable=False
        )
    
    def get_safe_error_message(self, error: FacebookError) -> str:
        """
        Get a user-safe error message (Thai) for display.
        
        Args:
            error: Classified error
            
        Returns:
            Thai error message safe for external display
        """
        messages = {
            ErrorCategory.AUTHENTICATION: "ระบบกำลังปรับปรุง กรุณาลองใหม่ภายหลังค่ะ",
            ErrorCategory.RATE_LIMIT: "กรุณารอสักครู่แล้วลองใหม่อีกครั้งนะคะ",
            ErrorCategory.TRANSIENT: "ระบบชั่วคราวไม่พร้อมใช้งาน กรุณารอสักครู่ค่ะ",
            ErrorCategory.NETWORK: "อินเทอร์เน็ตไม่เสถียร กรุณาลองใหม่ค่ะ",
            ErrorCategory.SERVER: "ระบบกำลังปรับปรุง กรุณาลองใหม่ในอีกสักครู่นะคะ",
            ErrorCategory.CLIENT: "ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบอีกครั้งค่ะ",
            ErrorCategory.UNKNOWN: "ขออภัยค่ะ มีข้อผิดพลาดเกิดขึ้น กรุณาลองใหม่",
        }
        
        return messages.get(error.category, messages[ErrorCategory.UNKNOWN])


# Legacy exceptions for backward compatibility
class FacebookAPIError(Exception):
    """Legacy exception for Facebook API errors."""
    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class RateLimitError(FacebookAPIError):
    """Legacy exception for rate limit errors."""
    pass


class TokenExpiredError(FacebookAPIError):
    """Exception raised when access token has expired."""
    pass


class AuthenticationError(FacebookAPIError):
    """Exception raised for authentication failures."""
    pass
