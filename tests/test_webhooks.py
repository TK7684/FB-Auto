"""
Unit tests for Webhook API endpoints.

Uses FastAPI TestClient for testing without a running server.
"""

import pytest
from unittest.mock import patch


class TestWebhookVerification:
    """Test suite for webhook verification."""

    def test_webhook_verification_success(self, test_client, mock_services):
        """Test successful webhook verification returns challenge."""
        # Configure mock to return the challenge
        mock_services["facebook_service"].verify_webhook.return_value = "test_challenge_12345"
        
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "test_token",
            "hub.challenge": "test_challenge_12345"
        }
        response = test_client.get("/webhook", params=params)
        assert response.status_code == 200
        assert response.text == "test_challenge_12345"

    def test_webhook_verification_invalid_token(self, test_client, mock_services):
        """Test invalid token returns 403."""
        # Configure mock to return None (verification failed)
        mock_services["facebook_service"].verify_webhook.return_value = None
        
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "test_challenge"
        }
        response = test_client.get("/webhook", params=params)
        assert response.status_code == 403

    def test_webhook_verification_missing_params(self, test_client, mock_services):
        """Test missing parameters returns 403."""
        response = test_client.get("/webhook")
        assert response.status_code == 403  # Returns 403 when verification fails


class TestWebhookPayloads:
    """Test suite for webhook payload handling."""

    def test_webhook_message_payload(self, test_client, sample_webhook_payload):
        """Test valid message webhook returns 200."""
        response = test_client.post("/webhook", json=sample_webhook_payload)
        assert response.status_code == 200
        # The endpoint returns empty body with status 200

    def test_webhook_comment_payload(self, test_client, sample_comment_webhook):
        """Test valid comment webhook returns 200."""
        response = test_client.post("/webhook", json=sample_comment_webhook)
        assert response.status_code == 200

    def test_webhook_empty_entry(self, test_client):
        """Test empty entry list returns 200."""
        response = test_client.post("/webhook", json={"entry": []})
        assert response.status_code == 200

    def test_webhook_malformed_payload(self, test_client):
        """Test malformed payload is handled gracefully."""
        response = test_client.post("/webhook", json={"invalid": "data"})
        # Should not crash, even with bad data
        assert response.status_code == 200
