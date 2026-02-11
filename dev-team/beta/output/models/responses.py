"""
Data Models for D Plus Skin Facebook Bot.

Shared data models used across the application.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    """Types of messages."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TEMPLATE = "template"


class SenderType(Enum):
    """Types of message senders."""
    USER = "user"
    PAGE = "page"
    BOT = "bot"


@dataclass
class User:
    """Facebook user information."""
    id: str
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_pic: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[int] = None
    gender: Optional[str] = None
    
    def get_display_name(self) -> str:
        """Get display name for the user."""
        if self.name:
            return self.name
        if self.first_name:
            return self.first_name
        return "ลูกค้า"


@dataclass
class Message:
    """A message in the conversation."""
    id: str
    text: str
    sender_type: SenderType
    timestamp: datetime
    message_type: MessageType = MessageType.TEXT
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_from_user(self) -> bool:
        """Check if message is from user."""
        return self.sender_type == SenderType.USER
    
    def is_from_bot(self) -> bool:
        """Check if message is from bot."""
        return self.sender_type == SenderType.BOT


@dataclass
class Conversation:
    """A conversation thread."""
    id: str
    user: User
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Message):
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_last_message(self) -> Optional[Message]:
        """Get the last message in the conversation."""
        if self.messages:
            return self.messages[-1]
        return None
    
    def get_user_messages(self) -> List[Message]:
        """Get all user messages."""
        return [m for m in self.messages if m.is_from_user()]
    
    def get_bot_messages(self) -> List[Message]:
        """Get all bot messages."""
        return [m for m in self.messages if m.is_from_bot()]


@dataclass
class Comment:
    """A Facebook page comment."""
    id: str
    message: str
    from_user: User
    created_time: datetime
    post_id: str
    parent_id: Optional[str] = None  # For replies
    can_reply_privately: bool = False
    is_hidden: bool = False
    attachment_url: Optional[str] = None
    
    def is_reply(self) -> bool:
        """Check if this is a reply to another comment."""
        return self.parent_id is not None


@dataclass
class Post:
    """A Facebook page post."""
    id: str
    message: str
    created_time: datetime
    permalink_url: Optional[str] = None
    full_picture: Optional[str] = None
    comments_count: int = 0
    likes_count: int = 0
    
    def get_short_message(self, max_length: int = 100) -> str:
        """Get truncated message."""
        if len(self.message) <= max_length:
            return self.message
        return self.message[:max_length] + "..."


@dataclass
class ProductRecommendation:
    """A product recommendation."""
    product_id: str
    product_name: str
    category: str
    price: float
    description: str
    match_score: float = 0.0
    reason: str = ""
    
    def format_for_display(self) -> str:
        """Format for display in response."""
        return f"{self.product_name} ({self.price:.0f}.-) - {self.description}"


@dataclass
class ResponseContext:
    """Context for generating a response."""
    user_message: str
    conversation_history: List[Message] = field(default_factory=list)
    detected_category: Optional[str] = None
    products: List[ProductRecommendation] = field(default_factory=list)
    post_context: Optional[str] = None
    user_profile: Optional[User] = None
    
    def to_prompt_context(self) -> str:
        """Convert to string for prompt context."""
        parts = []
        
        if self.post_context:
            parts.append(f"บริบทโพสต์: {self.post_context}")
        
        if self.products:
            parts.append("สินค้าแนะนำ:")
            for p in self.products:
                parts.append(f"- {p.format_for_display()}")
        
        return "\n".join(parts)


@dataclass
class WebhookEvent:
    """A webhook event from Facebook."""
    event_type: str
    sender_id: str
    recipient_id: str
    timestamp: datetime
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def is_message(self) -> bool:
        """Check if event is a message."""
        return self.event_type == "message"
    
    def is_comment(self) -> bool:
        """Check if event is a comment."""
        return self.event_type == "comment"


@dataclass
class RateLimitStatus:
    """Rate limit status information."""
    api_type: str
    limit: int
    remaining: int
    reset_timestamp: Optional[datetime] = None
    is_limited: bool = False
    
    def get_reset_seconds(self) -> int:
        """Get seconds until reset."""
        if not self.reset_timestamp:
            return 0
        delta = self.reset_timestamp - datetime.now()
        return max(0, int(delta.total_seconds()))


@dataclass
class SystemHealth:
    """System health status."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime = field(default_factory=datetime.now)
    checks: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.status == "healthy"
