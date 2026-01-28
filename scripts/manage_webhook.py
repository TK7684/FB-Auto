"""
Manage Facebook Page Webhook Subscriptions via Graph API.

This script can:
- Subscribe/unsubscribe page to apps
- List current subscriptions
- Test webhook locally

Note: Initial webhook setup (URL + verify token) must be done in Meta Developer Portal
for security reasons. This script manages page subscriptions after that.
"""

import requests
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings

# Your webhook URL
WEBHOOK_URL = "https://rent-rim-eight-momentum.trycloudflare.com/webhook"
VERIFY_TOKEN = settings.facebook_webhook_verify_token


def get_headers():
    """Get headers with access token."""
    return {
        "Content-Type": "application/json"
    }


def subscribe_page_to_app():
    """
    Subscribe the Facebook Page to your app using Graph API.

    This enables the app to receive webhooks from the page.
    """
    url = f"{settings.facebook_graph_api_url}/{settings.facebook_page_id}/subscribed_apps"

    params = {
        "access_token": settings.facebook_page_access_token,
        "subscribed_fields": "messages,feed,comments"
    }

    print(f"Subscribing page {settings.facebook_page_id} to app...")

    try:
        response = requests.post(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            print(f"✓ Successfully subscribed page to app!")
            print(f"  Subscribed fields: messages, feed, comments")
            return True
        else:
            print(f"✗ Failed to subscribe: {data}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def list_subscriptions():
    """List current app subscriptions for the page."""
    url = f"{settings.facebook_graph_api_url}/{settings.facebook_page_id}/subscribed_apps"

    params = {
        "access_token": settings.facebook_page_access_token
    }

    print("\nFetching current subscriptions...")

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        print("\nCurrent subscriptions:")
        print(json.dumps(data, indent=2))

        return data

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def get_page_info():
    """Get page information to verify credentials work."""
    url = f"{settings.facebook_graph_api_url}/{settings.facebook_page_id}"

    params = {
        "access_token": settings.facebook_page_access_token,
        "fields": "name,id,fan_count,followers_count"
    }

    print(f"\nFetching page info...")

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        print(f"\n✓ Page: {data.get('name')}")
        print(f"  ID: {data.get('id')}")
        print(f"  Followers: {data.get('followers_count', 'N/A')}")

        return data

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def test_local_webhook():
    """Test the local webhook endpoint."""
    import subprocess

    print("\nTesting local webhook endpoint...")

    test_data = {
        "entry": [
            {
                "id": settings.facebook_page_id,
                "time": 1234567890,
                "messaging": [
                    {
                        "sender": {"id": "test_user_123"},
                        "recipient": {"id": settings.facebook_page_id},
                        "message": {
                            "mid": "test_mid",
                            "text": "ทดสอบระบบ: สวัสดีค่ะ"
                        }
                    }
                ]
            }
        ]
    }

    try:
        # Start the bot if not running (in background)
        subprocess.Popen(
            ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=Path(__file__).parent.parent,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )

        import time
        time.sleep(3)  # Give server time to start

        response = requests.post(
            "http://localhost:8000/webhook",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        if response.status_code == 200:
            print("✓ Webhook endpoint is working!")
        else:
            print(f"✗ Webhook returned: {response.status_code}")

    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Main menu."""
    print("=" * 60)
    print(" Facebook Page Webhook Manager (Graph API)")
    print("=" * 60)
    print()

    while True:
        print("\nOptions:")
        print("1. Test connection (get page info)")
        print("2. Subscribe page to app")
        print("3. List current subscriptions")
        print("4. Test local webhook")
        print("5. Exit")
        print()

        choice = input("Select option (1-5): ").strip()

        if choice == "1":
            get_page_info()
        elif choice == "2":
            subscribe_page_to_app()
        elif choice == "3":
            list_subscriptions()
        elif choice == "4":
            test_local_webhook()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please select 1-5.")


if __name__ == "__main__":
    main()
