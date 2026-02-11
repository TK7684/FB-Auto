"""
Models Module.

Data models for the D Plus Skin Facebook Bot.
"""

from models.responses import (
    MessageType,
    SenderType,
    User,
    Message,
    Conversation,
    Comment,
    Post,
    ProductRecommendation,
    ResponseContext,
    WebhookEvent,
    RateLimitStatus,
    SystemHealth,
)

from models.errors import (
    ErrorSeverity,
    ErrorStatus,
    ErrorRecord,
    ErrorSummary,
)

__all__ = [
    # Enums
    "MessageType",
    "SenderType",
    "ErrorSeverity",
    "ErrorStatus",
    # Response Models
    "User",
    "Message",
    "Conversation",
    "Comment",
    "Post",
    "ProductRecommendation",
    "ResponseContext",
    "WebhookEvent",
    "RateLimitStatus",
    "SystemHealth",
    # Error Models
    "ErrorRecord",
    "ErrorSummary",
]
