"""
Unit tests for Health API endpoints.

Uses FastAPI TestClient for testing without a running server.
"""

import pytest


class TestHealthEndpoints:
    """Test suite for /health endpoints."""

    def test_health_endpoint(self, test_client):
        """Test basic health check returns 200."""
        response = test_client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

    def test_readiness_endpoint(self, test_client):
        """Test readiness check returns 200 when all services are ready."""
        response = test_client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "checks" in data

    def test_liveness_endpoint(self, test_client):
        """Test liveness check always returns 200."""
        response = test_client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True

    def test_metrics_endpoint(self, test_client):
        """Test metrics endpoint returns rate limit stats."""
        response = test_client.get("/health/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data

    def test_config_endpoint(self, test_client):
        """Test config endpoint returns sanitized configuration."""
        response = test_client.get("/health/config")
        assert response.status_code == 200
        data = response.json()
        assert "bot_name" in data
        assert "features" in data
        assert "rate_limits" in data
        # Ensure no sensitive data exposed
        assert "api_key" not in str(data).lower()
        assert "access_token" not in str(data).lower()


class TestRootEndpoint:
    """Test suite for root endpoint."""

    def test_root_endpoint(self, test_client):
        """Test root endpoint returns bot info."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "bot" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
