"""
Prompt Engineering Module.

Provides Thai language prompt management with:
- Few-shot example selection
- Thai language helpers
- Response quality validation
- Conversation type detection
"""

from services.prompts.prompt_manager import (
    ConversationType,
    FewShotExample,
    PromptManager,
    get_prompt_manager,
)

from services.prompts.thai_language import (
    PolitenessLevel,
    ThaiLinguisticProfile,
    ThaiLanguageHelper,
    ThaiResponseFormatter,
)

from services.prompts.quality_validator import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    ResponseValidator,
    get_response_validator,
)

__all__ = [
    # Prompt Manager
    "ConversationType",
    "FewShotExample",
    "PromptManager",
    "get_prompt_manager",
    # Thai Language
    "PolitenessLevel",
    "ThaiLinguisticProfile",
    "ThaiLanguageHelper",
    "ThaiResponseFormatter",
    # Quality Validator
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    "ResponseValidator",
    "get_response_validator",
]
