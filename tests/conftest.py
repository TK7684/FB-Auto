"""
Pytest configuration and fixtures for D Plus Skin Facebook Bot tests.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_products():
    """Sample product data for testing."""
    return [
        {
            "Product_Name": "Test Whitening Serum",
            "Symptom_Target": "ฝ้า รอยดำ",
            "Price": "890",
            "Promotion": "Buy 2 Get 1 Free",
            "Link": "https://test.com/serum",
            "Description": "Test serum for whitening"
        },
        {
            "Product_Name": "Test Anti-Acne Cream",
            "Symptom_Target": "สิว สิวอักเสบ",
            "Price": "650",
            "Promotion": "",
            "Link": "https://test.com/acne",
            "Description": "Test cream for acne"
        }
    ]


@pytest.fixture
def sample_webhook_payload():
    """Sample webhook payload for testing."""
    return {
        "entry": [
            {
                "id": "123456",
                "time": 1234567890,
                "messaging": [
                    {
                        "sender": {"id": "user123"},
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


@pytest.fixture
def sample_comment_webhook():
    """Sample comment webhook for testing."""
    return {
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
