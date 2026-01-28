"""Central configuration for Luna Autonomous Digital Twin"""

import os
import logging
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Dict, Any, List

# Load environment variables immediately when config is imported
load_dotenv()

# Configure logging using centralized config (routes verbose logs to file)
from utils.logging_config import setup_logging  # noqa: E402
logger = logging.getLogger(__name__)


@dataclass
class DomainConfig:
    """Configuration for a specific domain"""
    enabled: bool = True
    risk_tolerance: str = "balanced"  # conservative|balanced|aggressive
    max_position_size: float = 0.05  # For finance: 5% of portfolio
    work_hours: str = "09:00-18:00"  # For business
    priority_mode: str = "impact_urgency"  # For business
    sleep_target: int = 8  # For health: hours
    exercise_frequency: str = "daily"  # For health
    timezone: str = "Asia/Bangkok"  # Thailand (user's location)
    language: str = "en"


@dataclass
class MemoryConfig:
    """Configuration for memory system"""
    path: str = "./luna_memory"
    short_term_capacity: int = 50  # Max items in short-term memory
    working_memory_ttl: int = 72  # Hours before consolidation to long-term
    long_term_collections: List[str] = field(default_factory=lambda: [
        "user_knowledge",
        "decision_patterns_finance",
        "decision_patterns_business",
        "decision_patterns_health",
        "decision_patterns_daily_life",
        "outcomes_finance",
        "outcomes_business",
        "outcomes_health",
        "outcomes_daily_life",
        "safety_rules"
    ])
    max_retrieval_results: int = 5  # Max memories to retrieve per query


@dataclass
class DecisionConfig:
    """Configuration for decision engine"""
    confidence_threshold: float = 0.6  # Minimum confidence to execute
    default_decision_style: str = "balanced"  # conservative|balanced|aggressive
    max_decision_history: int = 1000  # Max decisions to keep in log
    auto_consolidate: bool = True  # Auto-consolidate working memory


@dataclass
class LearningConfig:
    """Configuration for learning system"""
    enabled: bool = True
    min_feedback_samples: int = 3  # Samples needed to form pattern
    pattern_confidence_threshold: float = 0.7
    learning_rate: float = 0.1  # How fast to adjust from feedback
    decay_rate: float = 0.01  # How fast patterns decay without reinforcement


@dataclass
class GeminiConfig:
    """Configuration for Gemini API via Vertex AI"""
    api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    model: str = "gemini-3-flash-preview"  # Gemini 3 model (default to Flash for speed)
    temperature: float = 1.0  # Gemini 3 recommends keeping temperature at 1.0
    timeout: int = 60
    location: str = "us-central1"

    # Gemini 3 specific parameters
    thinking_level: str = "high"  # "low", "medium" (Flash only), "high" (default for Gemini 3)
    include_thoughts: bool = False  # Include reasoning thoughts in response
    media_resolution: str = "media_resolution_medium"  # For images/videos
    use_gemini_3: bool = True  # Enable Gemini 3 features

    # API version for Gemini 3 (v1alpha for media_resolution feature)
    api_version: str = "v1beta"  # Use v1beta for Gemini 3

    # Model aliases for Gemini 3
    gemini_3_pro: str = "gemini-3-pro-preview"
    gemini_3_flash: str = "gemini-3-flash-preview"
    gemini_3_pro_image: str = "gemini-3-pro-image-preview"
    
    # Role-based model selection
    chat_model: str = "gemini-3-flash-preview"  # Fast responses for conversation
    research_model: str = "gemini-3-pro-preview"  # Deep thinking for analysis/research


@dataclass
class ZAIConfig:
    """Configuration for Z.AI (Zhipu) API"""
    api_key: str = field(default_factory=lambda: os.getenv("ZAI_API_KEY", ""))
    model: str = "glm-4"  # GLM-4 model for coding tasks
    temperature: float = 0.7


@dataclass
class TeamConfig:
    """Configuration for multi-agent teams"""
    coding_provider: str = "zai"  # Provider for coding team
    marketing_provider: str = "gemini"  # Provider for marketing team
    max_workers_per_team: int = 5
    enable_brainstorm: bool = True
    brainstorm_rounds: int = 3


@dataclass
class LunaConfig:
    """Core Luna configuration"""

    # Sub-configurations
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    zai: ZAIConfig = field(default_factory=ZAIConfig)
    teams: TeamConfig = field(default_factory=TeamConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    decision: DecisionConfig = field(default_factory=DecisionConfig)
    learning: LearningConfig = field(default_factory=LearningConfig)

    # Domain configurations
    domains: Dict[str, DomainConfig] = field(default_factory=dict)

    # System settings
    debug_mode: bool = False
    log_decisions: bool = True
    enable_safety_layer: bool = True
    
    # Integrations
    obsidian_path: str = field(default_factory=lambda: os.getenv("OBSIDIAN_PATH", "./obsidian_vault"))
    obsidian_inbox: str = "Ideas.md"

    def __post_init__(self):
        """Initialize default domain configurations"""
        if not self.domains:
            self.domains = {
                "finance": DomainConfig(
                    enabled=True,
                    risk_tolerance="conservative",  # From user's memory
                    max_position_size=0.05
                ),
                "business": DomainConfig(
                    enabled=True,
                    work_hours="09:00-18:00",
                    priority_mode="impact_urgency"
                ),
                "health": DomainConfig(
                    enabled=True,
                    sleep_target=8,
                    exercise_frequency="daily"
                ),
                "daily_life": DomainConfig(
                    enabled=True,
                    timezone="Asia/Bangkok",
                    language="en"
                )
            }

    def get_domain_config(self, domain: str) -> DomainConfig:
        """Get configuration for a specific domain"""
        return self.domains.get(domain, DomainConfig())

    def is_domain_enabled(self, domain: str) -> bool:
        """Check if a domain is enabled"""
        config = self.get_domain_config(domain)
        return config.enabled if config else False

    def validate(self) -> bool:
        """Validate configuration"""
        if not self.gemini.api_key:
            raise ValueError("GEMINI_API_KEY not set in environment or .env file")
        if self.decision.confidence_threshold < 0 or self.decision.confidence_threshold > 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
        if self.gemini.temperature < 0 or self.gemini.temperature > 1:
            raise ValueError("temperature must be between 0 and 1")
        return True


# Global config instance
config = LunaConfig()

# User-specific facts (from memories)
USER_FACTS = {
    "trading": {
        "risk_reward_min": 3,  # 1:3 minimum
        "aggressive_growth": True,  # Willing to lose 10% to gain 50%
    },
    "dog": {
        "name": "Dalmatian",
        "allergies": ["chicken", "grain"],
        "certifications": ["BH/VT", "RN-FL V"],  # FCI tested
        "organization": "United SAR K9 Thailand",
        "role": "Search and Rescue"
    },
    "productivity": {
        "quick_task_threshold": 2,  # minutes
        "schedule_longer_tasks": True
    },
    "communication": {
        "style": "direct and brief"
    },
    "smart_home": {
        "platform": "Home Assistant",
        "preference": "local over cloud"
    },
    "location": "Thailand",
    "timezone": "Asia/Bangkok",
    "interests": ["AI Digital Twins", "Search and Rescue", "Crypto Trading"]
}
