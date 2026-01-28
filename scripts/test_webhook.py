"""
Simple test to verify webhook configuration.
"""

import requests

# Your configuration
WEBHOOK_URL = "https://rent-rim-eight-momentum.trycloudflare.com/webhook"
VERIFY_TOKEN = "six_dragon_dildos_88"

def test_webhook_verification():
    """Test the webhook verification endpoint."""
    url = WEBHOOK_URL
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": VERIFY_TOKEN,
        "hub.challenge": "test_challenge_12345"
    }

    print("Testing webhook verification...")
    print(f"URL: {url}")
    print(f"Verify Token: {VERIFY_TOKEN}")
    print()

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("\n✓ Webhook verification SUCCESS!")
            print("Facebook can now send webhooks to your bot.")
        else:
            print("\n✗ Webhook verification FAILED!")
            print("Check:")
            print("  1. Bot is running (uvicorn main:app --reload)")
            print("  2. Cloudflare tunnel is running")
            print("  3. Verify token matches in .env")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def test_health_endpoint():
    """Test the health endpoint."""
    print("\n" + "=" * 60)
    print("Testing Health Endpoint")
    print("=" * 60)

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"Local bot status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: Bot may not be running - {e}")

    try:
        response = requests.get(f"{WEBHOOK_URL.rsplit('/', 1)[0]}/health", timeout=5)
        print(f"\nTunnel status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Tunnel error: {e}")


if __name__ == "__main__":
    test_health_endpoint()
    print("\n" + "=" * 60)
    test_webhook_verification()
