"""
Pytest configuration and fixtures for D Plus Skin Facebook Bot tests.

Uses a test-specific FastAPI app that skips the full lifespan initialization
to avoid requiring all production dependencies.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def test_app():
    """
    Create a test-specific FastAPI app without full lifespan.
    
    This avoids importing heavy dependencies like chromadb.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from config.settings import settings
    
    # Create test app without production lifespan
    app = FastAPI(
        title="Test Bot",
        description="Test app for unit testing",
        version="1.0.0"
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Import and include routers
    from api import webhooks, health
    app.include_router(webhooks.router, prefix="/webhook", tags=["Webhooks"])
    app.include_router(health.router, prefix="/health", tags=["Health"])
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "bot": settings.business_name,
            "version": "1.0.0",
            "status": "running",
            "features": {
                "dm_replies": settings.enable_dm_replies,
                "comment_replies": settings.enable_comment_replies,
                "auto_scrape": settings.enable_auto_scrape,
            },
            "endpoints": {
                "webhook": "/webhook",
                "health": "/health",
                "metrics": "/health/metrics"
            }
        }
    
    return app


@pytest.fixture
def mock_services():
    """Mock all external services for unit testing."""
    # Import main only after patching to inject mocks
    import main
    
    # Create mocks
    mock_rate_limiter = MagicMock()
    mock_rate_limiter.get_all_stats.return_value = {
        "dm_rate": MagicMock(usage_percent=10.0, remaining_calls=90, reset_time_seconds=60.0),
        "comment_rate": MagicMock(usage_percent=5.0, remaining_calls=95, reset_time_seconds=120.0),
    }
    
    mock_knowledge_base = MagicMock()
    mock_knowledge_base.get_product_count.return_value = 10
    mock_knowledge_base.get_qa_count.return_value = 5
    
    mock_gemini = MagicMock()
    mock_gemini.test_connection.return_value = True
    
    mock_facebook = MagicMock()
    
    # Inject mocks into main module
    original_rate_limiter = main.rate_limiter
    original_knowledge_base = main.knowledge_base
    original_gemini_service = main.gemini_service
    original_facebook_service = main.facebook_service
    
    main.rate_limiter = mock_rate_limiter
    main.knowledge_base = mock_knowledge_base
    main.gemini_service = mock_gemini
    main.facebook_service = mock_facebook
    
    yield {
        "rate_limiter": mock_rate_limiter,
        "knowledge_base": mock_knowledge_base,
        "gemini_service": mock_gemini,
        "facebook_service": mock_facebook,
    }
    
    # Restore originals
    main.rate_limiter = original_rate_limiter
    main.knowledge_base = original_knowledge_base
    main.gemini_service = original_gemini_service
    main.facebook_service = original_facebook_service


@pytest.fixture
def test_client(test_app, mock_services):
    """Create FastAPI TestClient with mocked services."""
    from fastapi.testclient import TestClient
    
    with TestClient(test_app, raise_server_exceptions=False) as client:
        yield client


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
