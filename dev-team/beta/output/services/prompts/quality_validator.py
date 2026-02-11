"""
Response Quality Validator.

Validates AI-generated responses for quality, accuracy, and
appropriateness before sending to customers.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from services.prompts.thai_language import ThaiLanguageHelper


class ValidationSeverity(Enum):
    """Severity level of validation issues."""
    ERROR = "error"       # Must fix - response invalid
    WARNING = "warning"   # Should fix - quality issue
    INFO = "info"         # Minor suggestion


@dataclass
class ValidationIssue:
    """Single validation issue."""
    code: str
    message: str
    severity: ValidationSeverity
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of response validation."""
    is_valid: bool
    score: float  # 0.0 to 1.0
    issues: List[ValidationIssue]
    error_count: int
    warning_count: int
    
    def get_errors(self) -> List[ValidationIssue]:
        """Get error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]


class ResponseValidator:
    """
    Validates AI-generated responses for quality and accuracy.
    
    Validation Rules:
    - Length constraints
    - Thai language requirements
    - Emoji ratio limits
    - Forbidden words
    - Required elements by category
    - Product claim verification
    
    Usage:
        validator = ResponseValidator()
        result = validator.validate(response, category="melasma", context={})
        
        if not result.is_valid:
            # Handle invalid response
    """
    
    # Validation configuration
    CONFIG = {
        "min_length": 10,
        "max_length": 1000,
        "must_contain_thai": True,
        "min_thai_ratio": 0.3,  # At least 30% Thai characters
        "max_emoji_ratio": 0.15,  # Max 15% emoji
        "max_exclamation": 5,  # Max exclamation marks
        
        # Forbidden words (safety)
        "forbidden_words": [
            "สถาบัน", "คลินิก", "โรงพยาบาล", "แพทย์", "หมอ", "ตรวจรักษา",
            "ผ่าตัด", "ฉีดยา", "ยาฉีด", "รับประกันหาย", "รักษาหายขาด",
            "ดีที่สุด", "อันดับหนึ่ง", "ที่สุดในโลก", "100%",
        ],
        
        # Suspicious patterns
        "suspicious_patterns": [
            r"หายภายใน\s*\d+\s*วัน",  # "cure in X days"
            r"เห็นผลทันที",  # "immediate results"
            r"รักษาได้ทุกอย่าง",  # "cures everything"
            r"ไม่ต้องใช้.*อีกต่อไป",  # "never need X again"
        ],
        
        # Required elements by category
        "required_elements": {
            "melasma": {
                "recommended": ["กันแดด", "sunscreen", "ใช้ต่อเนื่อง", "4-8 สัปดาห์", "อดทน"],
                "weight": 0.3,
            },
            "acne": {
                "recommended": ["ห้ามบีบ", "ล้างหน้า", "สะอาด"],
                "weight": 0.2,
            },
            "purchase": {
                "required": ["@dplusskin", "dplusskin"],
                "weight": 0.5,
            },
        },
    }
    
    def __init__(self):
        """Initialize validator."""
        self.config = self.CONFIG
        self.thai_helper = ThaiLanguageHelper()
        
    def validate(
        self,
        response: str,
        category: str = "general",
        context: Optional[Dict[str, Any]] = None,
        original_question: str = ""
    ) -> ValidationResult:
        """
        Validate response against quality criteria.
        
        Args:
            response: Generated response text
            category: Response category (melasma, acne, etc.)
            context: Additional context
            original_question: Original user question
            
        Returns:
            ValidationResult with score and issues
        """
        context = context or {}
        issues = []
        
        # Basic checks
        issues.extend(self._check_length(response))
        issues.extend(self._check_thai_content(response))
        issues.extend(self._check_emoji_ratio(response))
        issues.extend(self._check_forbidden_words(response))
        issues.extend(self._check_suspicious_claims(response))
        issues.extend(self._check_formatting(response))
        
        # Category-specific checks
        issues.extend(self._check_required_elements(response, category))
        issues.extend(self._check_question_answered(response, original_question))
        
        # Calculate score
        score = self._calculate_score(issues)
        
        # Determine validity
        error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])
        
        is_valid = error_count == 0 and score >= 0.5
        
        result = ValidationResult(
            is_valid=is_valid,
            score=score,
            issues=issues,
            error_count=error_count,
            warning_count=warning_count
        )
        
        # Log result
        if not result.is_valid:
            logger.warning(f"Response validation failed: {error_count} errors, score={score:.2f}")
        elif result.warning_count > 0:
            logger.debug(f"Response validation warnings: {warning_count}, score={score:.2f}")
        else:
            logger.debug(f"Response validation passed: score={score:.2f}")
        
        return result
    
    def _check_length(self, response: str) -> List[ValidationIssue]:
        """Check response length."""
        issues = []
        
        if len(response) < self.config["min_length"]:
            issues.append(ValidationIssue(
                code="TOO_SHORT",
                message=f"Response too short ({len(response)} chars, min {self.config['min_length']})",
                severity=ValidationSeverity.ERROR,
                suggestion="Expand response with more helpful information"
            ))
        
        if len(response) > self.config["max_length"]:
            issues.append(ValidationIssue(
                code="TOO_LONG",
                message=f"Response too long ({len(response)} chars, max {self.config['max_length']})",
                severity=ValidationSeverity.WARNING,
                suggestion="Shorten response for better engagement"
            ))
        
        return issues
    
    def _check_thai_content(self, response: str) -> List[ValidationIssue]:
        """Check Thai language content."""
        issues = []
        
        if self.config["must_contain_thai"]:
            thai_count = self.thai_helper.count_thai_characters(response)
            if thai_count == 0:
                issues.append(ValidationIssue(
                    code="NO_THAI",
                    message="Response contains no Thai characters",
                    severity=ValidationSeverity.ERROR,
                    suggestion="Respond in Thai language"
                ))
            else:
                thai_ratio = thai_count / len(response) if response else 0
                if thai_ratio < self.config["min_thai_ratio"]:
                    issues.append(ValidationIssue(
                        code="LOW_THAI_RATIO",
                        message=f"Low Thai content ratio ({thai_ratio:.0%})",
                        severity=ValidationSeverity.WARNING,
                        suggestion="Increase Thai language content"
                    ))
        
        return issues
    
    def _check_emoji_ratio(self, response: str) -> List[ValidationIssue]:
        """Check emoji ratio."""
        issues = []
        
        # Count emojis
        emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+'
        emojis = re.findall(emoji_pattern, response)
        emoji_count = sum(len(e) for e in emojis)
        
        if response and emoji_count / len(response) > self.config["max_emoji_ratio"]:
            issues.append(ValidationIssue(
                code="TOO_MANY_EMOJIS",
                message=f"Too many emojis ({emoji_count} chars, max {self.config['max_emoji_ratio']:.0%})",
                severity=ValidationSeverity.WARNING,
                suggestion="Reduce emoji usage for professional appearance"
            ))
        
        return issues
    
    def _check_forbidden_words(self, response: str) -> List[ValidationIssue]:
        """Check for forbidden words."""
        issues = []
        response_lower = response.lower()
        
        for word in self.config["forbidden_words"]:
            if word in response_lower:
                issues.append(ValidationIssue(
                    code="FORBIDDEN_WORD",
                    message=f"Contains forbidden word: '{word}'",
                    severity=ValidationSeverity.ERROR,
                    suggestion=f"Remove '{word}' - violates content policy"
                ))
        
        return issues
    
    def _check_suspicious_claims(self, response: str) -> List[ValidationIssue]:
        """Check for suspicious medical claims."""
        issues = []
        
        for pattern in self.config["suspicious_patterns"]:
            if re.search(pattern, response):
                issues.append(ValidationIssue(
                    code="SUSPICIOUS_CLAIM",
                    message=f"Contains suspicious claim pattern: {pattern}",
                    severity=ValidationSeverity.ERROR,
                    suggestion="Avoid making unrealistic claims"
                ))
        
        return issues
    
    def _check_formatting(self, response: str) -> List[ValidationIssue]:
        """Check response formatting."""
        issues = []
        
        # Check excessive exclamation marks
        exclamation_count = response.count('!') + response.count('！')
        if exclamation_count > self.config["max_exclamation"]:
            issues.append(ValidationIssue(
                code="TOO_MANY_EXCLAMATIONS",
                message=f"Too many exclamation marks ({exclamation_count})",
                severity=ValidationSeverity.WARNING,
                suggestion="Reduce exclamation marks for professional tone"
            ))
        
        # Check for markdown code blocks (shouldn't be in customer responses)
        if '```' in response:
            issues.append(ValidationIssue(
                code="MARKDOWN_BLOCK",
                message="Contains markdown code block",
                severity=ValidationSeverity.ERROR,
                suggestion="Remove code block formatting"
            ))
        
        return issues
    
    def _check_required_elements(
        self,
        response: str,
        category: str
    ) -> List[ValidationIssue]:
        """Check category-specific required elements."""
        issues = []
        
        category_config = self.config["required_elements"].get(category, {})
        if not category_config:
            return issues
        
        response_lower = response.lower()
        
        # Check required elements
        required = category_config.get("required", [])
        for element in required:
            if element.lower() not in response_lower:
                issues.append(ValidationIssue(
                    code="MISSING_REQUIRED_ELEMENT",
                    message=f"Missing required element: '{element}'",
                    severity=ValidationSeverity.ERROR,
                    suggestion=f"Include '{element}' in response"
                ))
        
        # Check recommended elements
        recommended = category_config.get("recommended", [])
        missing_recommended = []
        for element in recommended:
            if element.lower() not in response_lower:
                missing_recommended.append(element)
        
        if len(missing_recommended) == len(recommended) and recommended:
            issues.append(ValidationIssue(
                code="MISSING_RECOMMENDED_ELEMENTS",
                message=f"Missing recommended elements: {', '.join(missing_recommended[:3])}",
                severity=ValidationSeverity.INFO,
                suggestion="Consider adding recommended context"
            ))
        
        return issues
    
    def _check_question_answered(
        self,
        response: str,
        original_question: str
    ) -> List[ValidationIssue]:
        """Check if original question was answered."""
        issues = []
        
        if not original_question:
            return issues
        
        # Simple check: does response address question keywords?
        # This is a basic heuristic - can be improved with semantic matching
        question_keywords = set(original_question.lower().split())
        question_keywords -= {"ค่ะ", "ครับ", "ค้า", "จ้า", "นะ", "หน่อย", "ได้ไหม", "ไหม"}
        
        response_lower = response.lower()
        addressed_keywords = sum(1 for kw in question_keywords if kw in response_lower)
        
        coverage = addressed_keywords / len(question_keywords) if question_keywords else 1
        
        if coverage < 0.3 and len(question_keywords) > 2:
            issues.append(ValidationIssue(
                code="QUESTION_NOT_ADDRESSED",
                message="Response may not address the original question",
                severity=ValidationSeverity.WARNING,
                suggestion="Ensure response answers the customer's question"
            ))
        
        return issues
    
    def _calculate_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate overall quality score."""
        base_score = 1.0
        
        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                base_score -= 0.25
            elif issue.severity == ValidationSeverity.WARNING:
                base_score -= 0.1
            elif issue.severity == ValidationSeverity.INFO:
                base_score -= 0.02
        
        return max(0.0, min(1.0, base_score))
    
    def quick_validate(self, response: str) -> bool:
        """
        Quick validation for simple checks.
        
        Args:
            response: Response to validate
            
        Returns:
            True if passes basic validation
        """
        # Must have content
        if not response or len(response) < 10:
            return False
        
        # Must contain Thai
        if not self.thai_helper.contains_thai(response):
            return False
        
        # No forbidden words
        response_lower = response.lower()
        for word in self.config["forbidden_words"]:
            if word in response_lower:
                return False
        
        return True


# Singleton
_validator: Optional[ResponseValidator] = None


def get_response_validator() -> ResponseValidator:
    """Get global response validator instance."""
    global _validator
    if _validator is None:
        _validator = ResponseValidator()
    return _validator
