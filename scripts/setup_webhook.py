"""
Setup Facebook Webhook using Graph API.

This script programmatically configures the webhook subscription
instead of using the Meta Developer Portal manually.
"""

import requests
import json
import hashlib
import hmac
from typing import Dict, Any
from loguru import logger
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings


class FacebookWebhookSetup:
    """Handle Facebook webhook setup via Graph API."""

    def __init__(self):
        self.page_access_token = settings.facebook_page_access_token
        self.page_id = settings.facebook_page_id
        self.app_id = settings.facebook_app_id
        self.app_secret = settings.facebook_app_secret
        self.api_version = settings.facebook_api_version
        self.base_url = settings.facebook_graph_api_url

        # Your webhook configuration
        self.webhook_url = "https://potential-nebraska-cycling-caused.trycloudflare.com/webhook"
        self.verify_token = settings.facebook_webhook_verify_token

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

    def _get_app_access_token(self) -> str:
        """
        Get a short-lived app access token.

        Returns:
            App access token
        """
        url = f"https://graph.facebook.com/oauth/access_token"
        params = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "grant_type": "client_credentials"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data["access_token"]
        except Exception as e:
            logger.error(f"Failed to get app access token: {e}")
            return ""

    def subscribe_page_to_app(self) -> bool:
        """
        Subscribe the page to the app.

        This is required before setting up webhooks.

        Returns:
            True if successful
        """
        url = f"{self.base_url}/{self.page_id}/subscribed_apps"
        params = {
            "subscribed_fields": "feed",  # feed includes comments; messages requires pages_messaging permission
            **self._get_auth_params()
        }

        try:
            response = requests.post(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                logger.info(f"✓ Page {self.page_id} subscribed to app")
                return True
            else:
                logger.error(f"Failed to subscribe page: {data}")
                return False

        except Exception as e:
            logger.error(f"Error subscribing page: {e}")
            return False

    def create_webhook_subscription(self) -> bool:
        """
        Create a new webhook subscription.

        Returns:
            True if successful
        """
        # First, we need to subscribe the page
        if not self.subscribe_page_to_app():
            return False

        # For page subscriptions, we use the Page Subscribed Apps edge
        # The webhook subscription happens at the app level
        logger.info("Webhook subscription via Page subscription")
        return True

    def list_subscriptions(self) -> Dict[str, Any]:
        """
        List current webhook subscriptions for the page.

        Returns:
            Subscription data
        """
        url = f"{self.base_url}/{self.page_id}/subscribed_apps"
        params = self._get_auth_params()

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            logger.error(f"Error listing subscriptions: {e}")
            return {}

    def verify_webhook_setup(self) -> bool:
        """
        Verify the webhook is properly configured.

        Returns:
            True if webhook is accessible
        """
        try:
            # Try to access the health endpoint through the tunnel
            response = requests.get(f"{self.webhook_url}/../health", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Webhook URL is accessible")
                return True
            else:
                logger.error(f"Webhook URL returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Webhook URL not accessible: {e}")
            return False

    def get_page_info(self) -> Dict[str, Any]:
        """
        Get page information to verify credentials.

        Returns:
            Page information
        """
        url = f"{self.base_url}/{self.page_id}"
        params = {
            "fields": "name,id",
            **self._get_auth_params()
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting page info: {e}")
            return {}

    def test_webhook_event(self, test_data: Dict[str, Any] = None) -> bool:
        """
        Send a test webhook event to verify it works.

        Args:
            test_data: Mock webhook payload

        Returns:
            True if test successful
        """
        if test_data is None:
            test_data = {
                "entry": [
                    {
                        "id": "test_" + self.page_id,
                        "time": 1234567890,
                        "messaging": [
                            {
                                "sender": {"id": "test_user"},
                                "recipient": {"id": self.page_id},
                                "message": {
                                    "mid": "test_mid",
                                    "text": "สวัสดีค่ะ ทดสอบระบบ"
                                }
                            }
                        ]
                    }
                ]
            }

        try:
            response = requests.post(
                f"http://localhost:8000/webhook",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            if response.status_code == 200:
                logger.info("✓ Test webhook sent successfully")
                return True
            else:
                logger.error(f"Test webhook failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error sending test webhook: {e}")
            return False


def main():
    """Main setup function."""
    logger.info("=== Facebook Webhook Setup via Graph API ===")
    logger.info("")

    setup = FacebookWebhookSetup()

    # Step 1: Verify credentials
    logger.info("[1/5] Verifying page credentials...")
    page_info = setup.get_page_info()
    if page_info and "name" in page_info:
        logger.info(f"✓ Connected to page: {page_info['name']}")
    else:
        logger.error("✗ Failed to connect to page. Check your credentials.")
        return

    # Step 2: Verify webhook URL is accessible
    logger.info("[2/5] Verifying webhook URL accessibility...")
    if not setup.verify_webhook_setup():
        logger.error("✗ Webhook URL is not accessible. Make sure the tunnel is running.")
        return

    # Step 3: Subscribe page to app (this enables webhooks)
    logger.info("[3/5] Subscribing page to app...")
    if not setup.create_webhook_subscription():
        logger.error("✗ Failed to subscribe page to app")
        return

    # Step 4: List current subscriptions
    logger.info("[4/5] Listing current subscriptions...")
    subscriptions = setup.list_subscriptions()
    logger.info(f"Current subscriptions: {json.dumps(subscriptions, indent=2)}")

    # Step 5: Test webhook locally
    logger.info("[5/5] Testing webhook locally...")
    setup.test_webhook_event()

    logger.info("")
    logger.info("=== Setup Complete ===")
    logger.info("")
    logger.info("Your webhook configuration:")
    logger.info(f"  URL: {setup.webhook_url}")
    logger.info(f"  Verify Token: {setup.verify_token}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. In Meta Developer Portal, configure the webhook:")
    logger.info(f"   - Callback URL: {setup.webhook_url}")
    logger.info(f"   - Verify Token: {setup.verify_token}")
    logger.info("")
    logger.info("2. Subscribe to these fields:")
    logger.info("   - messages")
    logger.info("   - feed")
    logger.info("   - comments")
    logger.info("")
    logger.info("3. Test by sending a message to your page!")


if __name__ == "__main__":
    main()
