"""
Main FastAPI Application for D Plus Skin Facebook Bot.

This is the entry point for the application that:
1. Initializes all services on startup
2. Provides webhook endpoints for Facebook
3. Handles incoming messages and comments
4. Provides health check endpoints
"""

from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import sys
from pathlib import Path
from typing import Dict, Optional
import os

from config.settings import settings
from services.rate_limiter import RateLimiter, get_rate_limiter
from services.knowledge_base import KnowledgeBase, get_knowledge_base
from services.facebook_service import FacebookService, get_facebook_service
from services.gemini_service import GeminiService, get_gemini_service
from api import webhooks, health

# Global service instances
rate_limiter: Optional[RateLimiter] = None
knowledge_base: Optional[KnowledgeBase] = None
facebook_service: Optional[FacebookService] = None
gemini_service: Optional[GeminiService] = None

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level
)
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup initialization and shutdown cleanup.
    """
    global rate_limiter, knowledge_base, facebook_service, gemini_service

    # ===== Startup =====
    logger.info("=" * 60)
    logger.info(f"Starting {settings.business_name} Facebook Bot")
    logger.info("=" * 60)

    try:
        # Initialize rate limiter (CRITICAL - do first)
        logger.info("Initializing rate limiter...")
        rate_limiter = get_rate_limiter()
        logger.info("✓ Rate limiter initialized")

        # Initialize knowledge base
        logger.info("Initializing knowledge base...")
        knowledge_base = get_knowledge_base(
            persist_dir=settings.chroma_persist_dir
        )

        # Load products if CSV exists
        csv_path = Path("data/products.csv")
        if csv_path.exists():
            product_count = knowledge_base.load_products_from_csv(str(csv_path))
            logger.info(f"✓ Loaded {product_count} products from CSV")
        else:
            logger.warning(f"Products CSV not found at {csv_path}")

        logger.info(f"✓ Knowledge base: {knowledge_base.get_product_count()} products, "
                   f"{knowledge_base.get_qa_count()} Q&A pairs")

        # Initialize Gemini service
        logger.info("Initializing Gemini AI service...")
        gemini_service = get_gemini_service()
        if gemini_service.test_connection():
            logger.info("✓ Gemini AI service connected")
        else:
            logger.warning("⚠ Gemini AI service connection failed, will use fallback responses")

        # Initialize Facebook service
        logger.info("Initializing Facebook service...")
        facebook_service = get_facebook_service(rate_limiter)
        logger.info("✓ Facebook service initialized")

        # Log configuration
        logger.info(f"Configuration:")
        logger.info(f"  - Server: {settings.server_host}:{settings.server_port}")
        logger.info(f"  - Facebook API: {settings.facebook_api_version}")
        logger.info(f"  - Page ID: {settings.facebook_page_id}")
        logger.info(f"  - Rate limits: {settings.get_rate_limits()}")
        logger.info(f"  - DM replies: {'enabled' if settings.enable_dm_replies else 'disabled'}")
        logger.info(f"  - Comment replies: {'enabled' if settings.enable_comment_replies else 'disabled'}")

        logger.info("=" * 60)
        logger.info("All services initialized successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # ===== Shutdown =====
    logger.info("Shutting down gracefully...")
    logger.info("Thank you for using D Plus Skin Facebook Bot! 💕")


# Create FastAPI app
app = FastAPI(
    title=f"{settings.business_name} Facebook Bot",
    description="AI-powered Facebook bot for D Plus Skin skincare business",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhooks.router, prefix="/webhook", tags=["Webhooks"])
app.include_router(health.router, prefix="/health", tags=["Health"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with bot information."""
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


# Startup event for additional initialization
@app.on_event("startup")
async def startup_event():
    """Additional startup tasks."""
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Create data directories
    Path("data/knowledge_base").mkdir(parents=True, exist_ok=True)
    Path("data/scraped_data").mkdir(parents=True, exist_ok=True)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutdown complete")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
