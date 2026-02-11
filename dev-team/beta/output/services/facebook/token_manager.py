"""
Facebook Access Token Manager.

Manages access token lifecycle with proactive expiration detection,
automatic refresh, and validation.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import httpx
from loguru import logger

from config.settings import settings
from services.facebook.errors import (
    ErrorClassifier, 
    FacebookError, 
    ErrorCategory,
    AuthenticationError,
    TokenExpiredError
)


class TokenInfo:
    """Token metadata and state."""
    
    def __init__(
        self, 
        token: str, 
        expires_at: Optional[datetime] = None,
        token_type: str = "PAGE_ACCESS_TOKEN"
    ):
        self.token = token
        self.expires_at = expires_at
        self.token_type = token_type
        self.last_validated: Optional[datetime] = None
        self.is_valid: bool = True
        self.metadata: Dict[str, Any] = {}


class TokenManager:
    """
    Manages Facebook access token lifecycle.
    
    Features:
    - Proactive expiration detection
    - Token validation with Facebook's debug endpoint
    - Automatic refresh support (if refresh token available)
    - Thread-safe token access
    
    Usage:
        manager = TokenManager()
        token = await manager.get_valid_token()
        # Use token for API calls
    """
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        refresh_threshold_minutes: int = 5,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None
    ):
        """
        Initialize token manager.
        
        Args:
            access_token: Initial access token (defaults to settings)
            refresh_threshold_minutes: Minutes before expiry to trigger refresh
            app_id: Facebook app ID (defaults to settings)
            app_secret: Facebook app secret (defaults to settings)
        """
        self._token_info = TokenInfo(
            token=access_token or settings.facebook_page_access_token
        )
        self.refresh_threshold = timedelta(minutes=refresh_threshold_minutes)
        self.app_id = app_id or settings.facebook_app_id
        self.app_secret = app_secret or settings.facebook_app_secret
        self.api_version = settings.facebook_api_version
        self.base_url = settings.facebook_graph_api_url
        self._error_classifier = ErrorClassifier()
        
        logger.info("TokenManager initialized")
    
    async def validate_token(self, force: bool = False) -> bool:
        """
        Validate the current token with Facebook's debug endpoint.
        
        Args:
            force: Force validation even if recently validated
            
        Returns:
            True if token is valid
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        # Skip if recently validated (unless forced)
        if not force and self._token_info.last_validated:
            time_since_validation = datetime.now() - self._token_info.last_validated
            if time_since_validation < timedelta(minutes=5):
                return self._token_info.is_valid
        
        try:
            url = f"{self.base_url}/debug_token"
            params = {
                "input_token": self._token_info.token,
                "access_token": f"{self.app_id}|{self.app_secret}"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                data = response.json()
            
            if response.status_code != 200:
                error_data = data.get("error", {})
                logger.error(f"Token validation failed: {error_data}")
                self._token_info.is_valid = False
                raise AuthenticationError(
                    f"Token validation failed: {error_data.get('message', 'Unknown error')}"
                )
            
            token_data = data.get("data", {})
            
            # Check if token is valid
            if not token_data.get("is_valid", False):
                self._token_info.is_valid = False
                error_message = token_data.get("error", {}).get("message", "Token invalid")
                raise TokenExpiredError(f"Token is invalid: {error_message}")
            
            # Extract expiration
            expires_at_ts = token_data.get("expires_at")
            if expires_at_ts:
                self._token_info.expires_at = datetime.fromtimestamp(expires_at_ts)
                logger.debug(f"Token expires at: {self._token_info.expires_at}")
            
            # Store metadata
            self._token_info.metadata = {
                "app_id": token_data.get("app_id"),
                "type": token_data.get("type"),
                "scopes": token_data.get("scopes", []),
                "issued_at": token_data.get("issued_at"),
            }
            
            self._token_info.is_valid = True
            self._token_info.last_validated = datetime.now()
            
            logger.info("✓ Token validation successful")
            return True
            
        except httpx.TimeoutException as e:
            logger.error(f"Token validation timeout: {e}")
            # Don't mark as invalid on timeout, just return current state
            return self._token_info.is_valid
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            self._token_info.is_valid = False
            raise AuthenticationError(f"Token validation failed: {e}")
    
    def is_near_expiration(self) -> bool:
        """
        Check if token expires within the refresh threshold.
        
        Returns:
            True if token needs refresh
        """
        if not self._token_info.expires_at:
            return False
        
        near_expiry = datetime.now() + self.refresh_threshold
        return near_expiry >= self._token_info.expires_at
    
    def is_expired(self) -> bool:
        """
        Check if token has already expired.
        
        Returns:
            True if token is expired
        """
        if not self._token_info.expires_at:
            return False
        
        return datetime.now() >= self._token_info.expires_at
    
    def get_expires_in_seconds(self) -> Optional[int]:
        """
        Get seconds until token expires.
        
        Returns:
            Seconds until expiration, or None if unknown
        """
        if not self._token_info.expires_at:
            return None
        
        delta = self._token_info.expires_at - datetime.now()
        return max(0, int(delta.total_seconds()))
    
    async def get_valid_token(self, validate: bool = True) -> str:
        """
        Get a valid token, validating and refreshing if necessary.
        
        Args:
            validate: Whether to validate token before returning
            
        Returns:
            Valid access token
            
        Raises:
            AuthenticationError: If token cannot be validated/refreshed
        """
        # Check if we need validation
        if validate:
            try:
                is_valid = await self.validate_token()
                if not is_valid:
                    raise AuthenticationError("Token validation failed")
            except TokenExpiredError:
                logger.error("Token has expired and cannot be refreshed automatically")
                raise
        
        # Check expiration
        if self.is_expired():
            logger.error("Token has expired!")
            raise TokenExpiredError("Access token has expired. Manual re-authentication required.")
        
        if self.is_near_expiration():
            logger.warning("Token is near expiration!")
            # Note: Page access tokens typically can't be refreshed automatically
            # without a long-lived user token. Log for manual intervention.
        
        return self._token_info.token
    
    def update_token(self, new_token: str, expires_at: Optional[datetime] = None):
        """
        Update the stored token.
        
        Args:
            new_token: New access token
            expires_at: New expiration time
        """
        self._token_info = TokenInfo(
            token=new_token,
            expires_at=expires_at,
            token_type=self._token_info.token_type
        )
        logger.info("Token updated successfully")
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get current token information for monitoring.
        
        Returns:
            Dictionary with token metadata
        """
        return {
            "is_valid": self._token_info.is_valid,
            "expires_at": self._token_info.expires_at.isoformat() if self._token_info.expires_at else None,
            "expires_in_seconds": self.get_expires_in_seconds(),
            "is_near_expiration": self.is_near_expiration(),
            "last_validated": self._token_info.last_validated.isoformat() if self._token_info.last_validated else None,
            "token_type": self._token_info.token_type,
            "metadata": self._token_info.metadata,
        }
    
    async def inspect_token(self) -> Dict[str, Any]:
        """
        Inspect token details using Facebook's debug endpoint.
        
        Returns:
            Raw token data from Facebook
        """
        url = f"{self.base_url}/debug_token"
        params = {
            "input_token": self._token_info.token,
            "access_token": f"{self.app_id}|{self.app_secret}"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()


# Singleton instance
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """Get the global token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager


def reset_token_manager():
    """Reset the global token manager instance."""
    global _token_manager
    _token_manager = None
