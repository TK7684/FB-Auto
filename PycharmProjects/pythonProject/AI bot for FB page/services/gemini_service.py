"""
Gemini AI Service for Response Generation.

This module integrates with Google's Gemini API to generate
Thai language responses for customer inquiries about D Plus Skin products.
"""

import google.generativeai as genai
from typing import Optional, List, Dict, Any
from loguru import logger
import re
from datetime import datetime

from config.settings import settings
from config.constants import (
    SYSTEM_PROMPT,
    MELASMA_SPECIAL_PROMPT,
    FALLBACK_RESPONSE,
    MELASMA_KEYWORDS
)


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
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in MELASMA_KEYWORDS)

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
            context: Product/relevant information context
            conversation_history: Previous messages for context

        Returns:
            Complete prompt string
        """
        # Start with system prompt
        prompt = SYSTEM_PROMPT

        # Add special handling for melasma if needed
        if self._is_melasma_query(user_question):
            prompt += f"\n\n{MELASMA_SPECIAL_PROMPT}"

        # Add context
        prompt += f"\n\n## Context (ข้อมูลสินค้าและบริบท)\n{context}"

        # Add conversation history if available
        if conversation_history and len(conversation_history) > 0:
            prompt += "\n\n## Conversation History (ประวัติการสนทนา)\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = "ลูกค้า" if msg.get("role") == "user" else "ผู้ดูแล"
                prompt += f"{role}: {msg.get('content', '')}\n"

        # Add current question
        prompt += f"\n\n## คำถามลูกค้า\n{user_question}"

        # Add response instruction
        prompt += "\n\n## คำตอบ (กรุณาตอบเป็นภาษาไทยที่สุภาพและเป็นกันเอง)\n"

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
