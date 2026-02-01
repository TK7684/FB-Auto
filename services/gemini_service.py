"""
Gemini AI Service for Response Generation.

This module integrates with Google's Gemini API to generate
Thai language responses for customer inquiries about D Plus Skin products.
"""

import google.generativeai as genai
from typing import Optional, List, Dict, Any
from loguru import logger
import re
import json
from datetime import datetime
from pathlib import Path

from config.settings import settings
from config.constants import (
    SYSTEM_PROMPT,
    COMMENT_REPLY_PROMPT,
    MELASMA_SPECIAL_PROMPT,
    FALLBACK_RESPONSE,
    MELASMA_KEYWORDS,
    ACNE_KEYWORDS,
    DRY_SKIN_KEYWORDS,
    WRINKLE_KEYWORDS,
    SUPPLEMENT_KEYWORDS,
    SUPPLEMENT_KEYWORDS,
    PURCHASE_INTENT_KEYWORDS,
    SOCIAL_KEYWORDS,
    SOCIAL_SYSTEM_PROMPT
)
from services.memory_service import get_memory_service


# Load CTA configuration
def _load_cta_config() -> Dict[str, Any]:
    """Load product CTA configuration from JSON file."""
    cta_path = Path("data/products_cta.json")
    if cta_path.exists():
        try:
            with open(cta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading CTA config: {e}")
    return {"categories": {}, "purchase_intent_keywords": [], "default_line_id": "@dplusskin"}

CTA_CONFIG = _load_cta_config()


class GeminiService:
    """
    Service for generating AI responses using Gemini API.

    Features:
    - Thai language support
    - Special handling for "ฝ้า" (melasma) queries
    - Context-aware responses based on product database
    - Fallback responses when API fails
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service.

        Args:
            api_key: Gemini API key (uses settings if not provided)
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = settings.gemini_model
        self.memory_service = get_memory_service()

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini service initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.model = None

    def _is_melasma_query(self, text: str) -> bool:
        """
        Check if the query is about melasma (ฝ้า).

        Args:
            text: Query text

        Returns:
            True if query contains melasma keywords
        """
        return any(keyword in text for keyword in MELASMA_KEYWORDS)

    def _is_purchase_intent(self, text: str) -> bool:
        """
        Check if the query shows purchase intent.

        Args:
            text: Query text

        Returns:
            True if query shows intent to buy
        """
        return any(keyword in text for keyword in PURCHASE_INTENT_KEYWORDS)

    def _is_social_comment(self, text: str) -> bool:
        """
        Check if the query is social/chit-chat.
        """
        return any(keyword in text for keyword in SOCIAL_KEYWORDS)

    def _detect_skin_category(self, text: str) -> str:
        """
        Detect which skin problem category the query is about.

        Args:
            text: Query text (could be comment or post caption)

        Returns:
            Category name (สิว, ฝ้า, ผิวแห้ง, ริ้วรอย, อาหารเสริม, or ทั่วไป)
        """
        text_lower = text.lower()
        if any(kw in text for kw in ACNE_KEYWORDS):
            return "สิว"
        elif any(kw in text for kw in MELASMA_KEYWORDS):
            return "ฝ้า"
        elif any(kw in text for kw in SUPPLEMENT_KEYWORDS) or any(kw in text_lower for kw in SUPPLEMENT_KEYWORDS):
            return "อาหารเสริม"
        elif any(kw in text for kw in DRY_SKIN_KEYWORDS):
            return "ผิวแห้ง"
        elif any(kw in text for kw in WRINKLE_KEYWORDS):
            return "ริ้วรอย"
        return "ทั่วไป"

    def _get_cta_for_category(self, category: str, post_caption: str = "", comment_text: str = "") -> str:
        """
        Get the CTA text and link for a given category with tier-based matching.

        Priority:
        1. Check post caption for exact product name
        2. Check comment/caption for tier keywords
        3. Fall back to default CTA for category

        Args:
            category: Skin problem category
            post_caption: Original post caption (primary source)
            comment_text: User's comment text

        Returns:
            CTA text with link
        """
        cat_config = CTA_CONFIG.get("categories", {}).get(category, {})
        if not cat_config:
            cat_config = CTA_CONFIG.get("categories", {}).get("ทั่วไป", {})

        link = cat_config.get("link", "https://line.me/ti/p/@dplusskin")
        emoji = cat_config.get("emoji", "💕")

        # Check for tier-based matching
        tiers = cat_config.get("tiers", {})
        combined_text = f"{post_caption} {comment_text}".lower()

        if tiers:
            # Check high tier keywords first (post caption priority)
            high_tier = tiers.get("high", {})
            high_keywords = high_tier.get("keywords", [])
            if any(kw.lower() in combined_text for kw in high_keywords):
                cta = high_tier.get("cta", cat_config.get("default_cta", "สนใจสินค้า ทักมาเลยค่ะ 👉"))
                return f"{cta} {link} {emoji}"

            # Check low tier keywords
            low_tier = tiers.get("low", {})
            low_keywords = low_tier.get("keywords", [])
            if any(kw.lower() in combined_text for kw in low_keywords):
                cta = low_tier.get("cta", cat_config.get("default_cta", "สนใจสินค้า ทักมาเลยค่ะ 👉"))
                return f"{cta} {link} {emoji}"

        # Fall back to default CTA
        cta = cat_config.get("default_cta", cat_config.get("cta", "สนใจสินค้า ทักมาเลยค่ะ 👉"))
        return f"{cta} {link} {emoji}"


    def _build_prompt(
        self,
        user_question: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Build the complete prompt for Gemini.

        Args:
            user_question: User's question
            context: Product/relevant information context (may include post caption)
            conversation_history: Previous messages for context

        Returns:
            Complete prompt string
        """
        # Extract post caption from context if available
        post_caption = ""
        if "บริบทโพสต์:" in context:
            lines = context.split("\n")
            for line in lines:
                if line.startswith("บริบทโพสต์:"):
                    post_caption = line.replace("บริบทโพสต์:", "").strip()
                    break

        # Detect category from post caption + user question
        combined_text = f"{post_caption} {user_question}"
        category = self._detect_skin_category(combined_text)
        cta_text = self._get_cta_for_category(category, post_caption, user_question)

        # Check if this is a purchase intent
        is_purchase = self._is_purchase_intent(user_question)

        # Check if social/chit-chat
        if self._is_social_comment(user_question):
            # Use Social Prompt
            # Try to get a specific example from memory if available
            example = self.memory_service.get_random_example("social")
            prompt = SOCIAL_SYSTEM_PROMPT
            if example:
                prompt += f"\n\n## ตัวอย่างจริงจากแอดมิน\nลูกค้า: {example['question']}\nแอดมิน: {example['answer']}"
            
            prompt += f"\n\n## ข้อความลูกค้า\n{user_question}\n\n## ตอบกลับ (สั้นๆ น่ารัก):"
            return prompt

        # Use COMMENT_REPLY_PROMPT for short, CTA-focused responses
        if post_caption or is_purchase:
            prompt = COMMENT_REPLY_PROMPT.format(
                post_caption=post_caption or "(ไม่มีข้อมูลโพสต์)",
                cta_text=cta_text,
                comment_text=user_question
            )
        else:
            # Use regular system prompt for general queries
            prompt = SYSTEM_PROMPT

            # Add special handling for melasma if needed
            if self._is_melasma_query(user_question):
                prompt += f"\n\n{MELASMA_SPECIAL_PROMPT}"

            # Add context
            prompt += f"\n\n## Context (ข้อมูลสินค้าและบริบท)\n{context}"
            
            # --- MEMORY INJECTION ---
            similar_memories = self.memory_service.find_similar(user_question, category="product")
            if similar_memories:
                prompt += "\n\n## ตัวอย่างการตอบในอดีต (เลียนแบบโทนนี้)\n"
                for mem in similar_memories:
                    prompt += f"- Q: {mem['question']}\n  A: {mem['answer']}\n"
            # ------------------------

            # Add current question
            prompt += f"\n\n## คำถามลูกค้า\n{user_question}"

            # Add CTA instruction
            prompt += f"\n\nCTA ที่ใช้: {cta_text}"

            # Add response instruction
            prompt += "\n\n## คำตอบ (ตอบสั้นๆ 1-2 บรรทัด พร้อม CTA)\n"

        return prompt

    def _extract_product_mentions(self, response: str) -> List[str]:
        """
        Extract product names mentioned in the response.

        Args:
            response: Generated response text

        Returns:
            List of product names mentioned
        """
        # This is a simple implementation
        # In production, you might use regex patterns or NER
        products = []

        # Common product patterns
        patterns = [
            r"D Plus \w+",
            r"ซีรั่ม.*",
            r"ครีม.*",
            r"เจล.*",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response)
            products.extend(matches)

        return list(set(products))

    def _validate_response(self, response: str) -> bool:
        """
        Validate the generated response.

        Args:
            response: Generated response text

        Returns:
            True if response is valid
        """
        if not response or len(response.strip()) < 10:
            logger.warning("Response too short or empty")
            return False

        # Check for Thai characters
        if not re.search(r'[\u0E00-\u0E7F]', response):
            logger.warning("Response doesn't contain Thai characters")

        # Check response length (should be reasonable)
        if len(response) > 2000:
            logger.warning(f"Response too long: {len(response)} characters")
            return False

        return True

    async def generate_response(
        self,
        user_question: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        max_retries: int = 2
    ) -> str:
        """
        Generate a response using Gemini AI.

        Args:
            user_question: User's question
            context: Product/relevant information
            conversation_history: Previous messages
            max_retries: Maximum retry attempts

        Returns:
            Generated response text
        """
        if not self.model:
            logger.error("Gemini model not initialized, using fallback")
            return self._get_fallback_response(user_question, context)

        # Build prompt
        prompt = self._build_prompt(user_question, context, conversation_history)

        # Log for debugging
        is_melasma = self._is_melasma_query(user_question)
        logger.info(
            f"Generating response for: {user_question[:50]}... "
            f"(melasma: {is_melasma})"
        )

        # Try to generate with retries
        for attempt in range(max_retries + 1):
            try:
                response = self.model.generate_content(prompt)

                if not response or not response.text:
                    logger.warning(f"Empty response from Gemini (attempt {attempt + 1})")
                    if attempt < max_retries:
                        continue
                    return self._get_fallback_response(user_question, context)

                # Validate response
                if self._validate_response(response.text):
                    logger.info(f"✓ Response generated: {len(response.text)} characters")
                    return response.text
                else:
                    logger.warning(f"Response validation failed (attempt {attempt + 1})")
                    if attempt < max_retries:
                        continue

            except Exception as e:
                logger.error(
                    f"Gemini API error (attempt {attempt + 1}/{max_retries + 1}): {e}"
                )

                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    logger.error("Gemini quota exceeded, using fallback")
                    return self._get_fallback_response(user_question, context)

                if attempt < max_retries:
                    continue

        # All retries failed, use fallback
        logger.warning("All retries failed, using fallback response")
        return self._get_fallback_response(user_question, context)

    def _get_fallback_response(self, question: str, context: str) -> str:
        """
        Get a fallback response when AI generation fails.

        Args:
            question: User's question
            context: Product context

        Returns:
            Fallback response
        """
        # Try to provide a helpful response even without AI
        response = FALLBACK_RESPONSE.format(context=context)

        # Add personalization for melasma queries
        if self._is_melasma_query(question):
            response = (
                "สวัสดีค่ะ คำถามเกี่ยวกับฝ้าใช่ไหมคะ 🌸\n\n"
                "สำหรับปัญหาฝ้า เราแนะนำให้ใช้ผลิตภัณฑ์ที่มีส่วนผสมของ:\n"
                "- Vitamin C\n"
                "- Niacinamide\n"
                "- Tranexamic Acid\n\n"
                "และสำคัญมากคือต้องทาครีมกันแดดทุกวันนะคะ ☀️\n\n"
                f"{context}\n\n"
                "ฝ้าเป็นปัญหาที่ต้องอดทนใช้สม่ำเสมอค่ะ ปกติจะเห็นผลใน 4-8 สัปดาห์ 💕"
            )

        return response

    async def generate_response_streaming(
        self,
        user_question: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ):
        """
        Generate a streaming response (for future use).

        Args:
            user_question: User's question
            context: Product context
            conversation_history: Previous messages

        Yields:
            Response chunks
        """
        if not self.model:
            yield self._get_fallback_response(user_question, context)
            return

        prompt = self._build_prompt(user_question, context, conversation_history)

        try:
            response = self.model.generate_content(prompt, stream=True)

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield self._get_fallback_response(user_question, context)

    def test_connection(self) -> bool:
        """
        Test the Gemini API connection.

        Returns:
            True if connection successful
        """
        try:
            response = self.model.generate_content("สวัสดี")
            if response and response.text:
                logger.info(f"✓ Gemini connection test successful: {response.text[:50]}")
                return True
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")

        return False


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get the global Gemini service instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


def reset_gemini_service():
    """Reset the global Gemini service instance."""
    global _gemini_service
    _gemini_service = None
