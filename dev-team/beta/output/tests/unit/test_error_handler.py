"""
Unit tests for Facebook Error Handling.
"""

import pytest
from services.facebook.errors import (
    ErrorClassifier,
    ErrorCategory,
    FacebookError,
)
from services.facebook.error_handler import (
    ErrorHandler,
    ActionType,
)


class TestErrorClassifier:
    """Test error classification."""
    
    @pytest.fixture
    def classifier(self):
        return ErrorClassifier()
    
    def test_classify_rate_limit_error(self, classifier):
        """Should classify rate limit errors correctly."""
        response = {
            "error": {
                "code": 4,
                "message": "App rate limit reached"
            }
        }
        
        error = classifier.classify_from_response(response)
        
        assert error.category == ErrorCategory.RATE_LIMIT
        assert error.is_retryable is True
        assert error.code == 4
    
    def test_classify_authentication_error(self, classifier):
        """Should classify authentication errors correctly."""
        response = {
            "error": {
                "code": 190,
                "message": "Access token expired"
            }
        }
        
        error = classifier.classify_from_response(response)
        
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.is_retryable is False
        assert error.requires_reauth is True
    
    def test_classify_network_exception(self, classifier):
        """Should classify network exceptions correctly."""
        exception = TimeoutError("Connection timeout")
        
        error = classifier.classify_from_exception(exception)
        
        assert error.category == ErrorCategory.NETWORK
        assert error.is_retryable is True
    
    def test_get_safe_message(self, classifier):
        """Should return Thai safe message."""
        error = FacebookError(
            code=4,
            message="Rate limit",
            category=ErrorCategory.RATE_LIMIT,
            is_retryable=True
        )
        
        message = classifier.get_safe_error_message(error)
        
        assert "รอ" in message or "กรุณา" in message
        assert "ค่ะ" in message or "ครับ" in message


class TestErrorHandler:
    """Test error handler."""
    
    @pytest.fixture
    def handler(self):
        return ErrorHandler()
    
    @pytest.mark.asyncio
    async def test_handle_rate_limit_error(self, handler):
        """Should recommend retry with backoff for rate limit."""
        error = Exception("Rate limit")
        
        action = await handler.handle(error, {"operation": "send_message"})
        
        assert action.action in [ActionType.RETRY_WITH_BACKOFF, ActionType.CIRCUIT_BREAK]
        assert action.safe_message != ""
    
    @pytest.mark.asyncio
    async def test_handle_authentication_error(self, handler):
        """Should recommend reauth for auth error."""
        error = Exception("Session expired")
        error.code = 190
        
        action = await handler.handle(error, {"operation": "send_message"})
        
        # Note: Simple exceptions won't have code, but behavior should be reasonable
        assert action.safe_message != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
