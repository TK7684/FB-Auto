"""
Health Check API endpoints.

Provides endpoints for monitoring bot health and status.
"""

from fastapi import APIRouter, HTTPException
from loguru import logger
from typing import Dict, Any
import main
from config.settings import settings

router = APIRouter()


@router.get("/", summary="Basic health check")
async def health_check():
    """
    Basic health check endpoint.

    Returns service status and basic metrics.
    """
    status = {
        "status": "healthy",
        "bot": settings.business_name,
        "version": "1.0.0"
    }

    # Check services
    services = {}

    if main.rate_limiter:
        services["rate_limiter"] = "ok"
    else:
        services["rate_limiter"] = "not initialized"
        status["status"] = "degraded"

    if main.knowledge_base:
        services["knowledge_base"] = {
            "status": "ok",
            "products": main.knowledge_base.get_product_count(),
            "qa_pairs": main.knowledge_base.get_qa_count()
        }
    else:
        services["knowledge_base"] = "not initialized"
        status["status"] = "degraded"

    if main.gemini_service:
        services["gemini"] = "ok"
    else:
        services["gemini"] = "not initialized"
        status["status"] = "degraded"

    if main.facebook_service:
        services["facebook"] = "ok"
    else:
        services["facebook"] = "not initialized"
        status["status"] = "degraded"

    status["services"] = services
    return status


@router.get("/ready", summary="Readiness check")
async def readiness_check():
    """
    Readiness check - verifies all critical services are ready.

    Returns 200 if ready, 503 if not ready.
    """
    checks = {
        "rate_limiter": main.rate_limiter is not None,
        "knowledge_base": main.knowledge_base is not None,
        "gemini": main.gemini_service is not None,
        "facebook": main.facebook_service is not None,
    }

    all_ready = all(checks.values())

    if not all_ready:
        raise HTTPException(
            status_code=503,
            detail={
                "ready": False,
                "checks": checks
            }
        )

    return {"ready": True, "checks": checks}


@router.get("/live", summary="Liveness check")
async def liveness_check():
    """
    Liveness check - verifies the application is running.

    Always returns 200 if the application is alive.
    """
    return {"alive": True}


@router.get("/metrics", summary="Rate limit metrics")
async def rate_limit_metrics():
    """
    Get current rate limit usage metrics.

    Returns detailed rate limit status for all endpoints.
    """
    if not main.rate_limiter:
        raise HTTPException(status_code=503, detail="Rate limiter not initialized")

    metrics = main.rate_limiter.get_all_stats()

    # Format for display
    formatted = {}
    for endpoint, stats in metrics.items():
        formatted[endpoint] = {
            "usage_percent": round(stats.usage_percent, 2),
            "remaining_calls": stats.remaining_calls
        }
        if stats.reset_time_seconds is not None:
            formatted[endpoint]["reset_time_seconds"] = round(stats.reset_time_seconds, 2)

    return {
        "metrics": formatted,
        "timestamp": main.knowledge_base is not None  # Just to indicate we're responding
    }


@router.get("/config", summary="Configuration info")
async def config_info():
    """
    Get current configuration (sanitized).

    Does not expose sensitive information like API keys.
    """
    return {
        "bot_name": settings.business_name,
        "language": settings.default_language,
        "timezone": settings.timezone,
        "features": {
            "dm_replies": settings.enable_dm_replies,
            "comment_replies": settings.enable_comment_replies,
            "auto_scrape": settings.enable_auto_scrape,
        },
        "facebook": {
            "api_version": settings.facebook_api_version,
            "page_id": settings.facebook_page_id,
        },
        "rate_limits": settings.get_rate_limits()
    }
