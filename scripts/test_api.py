"""
Test script for the D Plus Skin Facebook Bot API.

Run this to test the bot locally before connecting to Facebook.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("\n" + "=" * 50)
    print("Testing Health Endpoint")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_readiness():
    """Test readiness endpoint."""
    print("\n" + "=" * 50)
    print("Testing Readiness Endpoint")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/health/ready")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_metrics():
    """Test metrics endpoint."""
    print("\n" + "=" * 50)
    print("Testing Metrics Endpoint")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/health/metrics")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_config():
    """Test config endpoint."""
    print("\n" + "=" * 50)
    print("Testing Config Endpoint")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/health/config")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_webhook_verification():
    """Test webhook verification endpoint."""
    print("\n" + "=" * 50)
    print("Testing Webhook Verification")
    print("=" * 50)

    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "test_token",  # Should match .env
        "hub.challenge": "test_challenge"
    }

    response = requests.get(f"{BASE_URL}/webhook", params=params)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    return response.status_code == 200


def simulate_webhook_message():
    """Simulate an incoming message webhook."""
    print("\n" + "=" * 50)
    print("Simulating Message Webhook")
    print("=" * 50)

    payload = {
        "entry": [
            {
                "id": "123456",
                "time": 1234567890,
                "messaging": [
                    {
                        "sender": {"id": "test_user_123"},
                        "recipient": {"id": "page123"},
                        "message": {
                            "mid": "msg123",
                            "text": "เป็นฝ้า ใช้ตัวไหนคะ"
                        }
                    }
                ]
            }
        ]
    }

    response = requests.post(
        f"{BASE_URL}/webhook",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")


def simulate_comment_webhook():
    """Simulate an incoming comment webhook."""
    print("\n" + "=" * 50)
    print("Simulating Comment Webhook")
    print("=" * 50)

    payload = {
        "entry": [
            {
                "id": "123456",
                "time": 1234567890,
                "changes": [
                    {
                        "field": "feed",
                        "value": {
                            "post_id": "post123",
                            "comment_id": "comment123",
                            "message": "สิวเยอะค่ะ แนะนำตัวไหนดี"
                        }
                    }
                ]
            }
        ]
    }

    response = requests.post(
        f"{BASE_URL}/webhook",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print(" D Plus Skin Facebook Bot - API Test Suite")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    print("Make sure the bot is running before testing!")

    try:
        # Test basic endpoints
        test_health()
        test_readiness()
        test_metrics()
        test_config()

        # Test webhook (commented out as it requires proper setup)
        # if test_webhook_verification():
        #     simulate_webhook_message()
        #     simulate_comment_webhook()

        print("\n" + "=" * 70)
        print(" All tests completed!")
        print("=" * 70)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to the bot!")
        print("Please make sure the bot is running:")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    main()
