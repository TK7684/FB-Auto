"""
Configuration management for D Plus Skin Facebook Bot.
Uses pydantic-settings for type-safe environment variable loading.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ===== API Keys =====
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"
    
    # ===== OpenRouter Settings =====
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # ===== Facebook Credentials =====
    facebook_app_id: str
    facebook_app_secret: str
    facebook_page_access_token: str
    facebook_page_id: str
    facebook_webhook_verify_token: str
    facebook_api_version: str = "v19.0"

    # ===== Knowledge Base Settings =====
    vector_db_type: str = "chromadb"
    chroma_persist_dir: str = "./data/knowledge_base"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # ===== Rate Limiting Settings =====
    messenger_max_calls_per_second: int = 250  # 85% of 300
    messenger_max_media_per_second: int = 8    # 85% of 10
    page_max_calls_per_second: int = 100
    private_replies_max_per_hour: int = 700    # 85% of 750

    rate_limit_buffer_percent: float = 0.85
    rate_limit_window_seconds: int = 60
    rate_limit_cleanup_interval: int = 3600

    # ===== Server Settings =====
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    log_level: str = "INFO"

    # ===== Business Settings =====
    business_name: str = "D Plus Skin"
    default_language: str = "th"
    timezone: str = "Asia/Bangkok"

    # ===== Feature Flags =====
    enable_dm_replies: bool = True
    enable_comment_replies: bool = True
    enable_auto_scrape: bool = False
    scrape_interval_hours: int = 168  # Weekly

    @property
    def facebook_graph_api_url(self) -> str:
        """Get the Facebook Graph API base URL."""
        return f"https://graph.facebook.com/{self.facebook_api_version}"

    @property
    def messenger_send_url(self) -> str:
        """Get the Messenger Send API URL."""
        return f"{self.facebook_graph_api_url}/me/messages"

    def get_rate_limits(self) -> dict:
        """Get rate limit configuration as a dictionary."""
        return {
            "messenger_text": {
                "rate": self.messenger_max_calls_per_second,
                "capacity": 50
            },
            "messenger_media": {
                "rate": self.messenger_max_media_per_second,
                "capacity": 5
            },
            "page_api": {
                "rate": self.page_max_calls_per_second,
                "capacity": 20
            },
            "private_replies": {
                "limit": self.private_replies_max_per_hour,
                "window": 3600
            }
        }


# Global settings instance
settings = Settings()
