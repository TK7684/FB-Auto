"""Gemini client for Luna Autonomous Digital Twin

Supports two modes:
1. Google Generative AI API (using API key from ai.google.com)
2. Vertex AI (using service account JSON file)

Gemini 3 Features:
- thinking_level: Controls reasoning depth (low, medium, high)
- media_resolution: Controls image/video processing resolution
- thought_signature: Maintains reasoning context across API calls
- include_thoughts: Include reasoning thoughts in response
"""

import os
import time
import logging
import threading
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from config import config

logger = logging.getLogger(__name__)

# Rate limiting: semaphore to limit concurrent API requests
_api_semaphore = threading.Semaphore(5)
_last_request_time = {}
_request_lock = threading.Lock()

def _rate_limit(api_name: str, min_interval: float = 0.5):
    """Rate limiter to prevent hitting API rate limits."""
    with _request_lock:
        now = time.time()
        last_time = _last_request_time.get(api_name, 0)
        elapsed = now - last_time

        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

        _last_request_time[api_name] = time.time()

@dataclass
class GenerationResult:
    """Result of an LLM generation"""
    text: str
    model: str
    temperature: float
    tokens_used: Optional[int] = None
    generation_time: float = 0.0
    success: bool = True
    error: Optional[str] = None
    error_type: Optional[str] = None  # 'quota', 'rate_limit', 'auth', etc.

    # Gemini 3 specific fields
    thoughts: Optional[str] = None  # Reasoning thoughts (if include_thoughts=True)
    thought_signature: Optional[str] = None  # For multi-turn conversations
    thinking_level: Optional[str] = None  # The thinking level used

class GeminiClient:
    """
    Wrapper for Google's Gemini API.
    Supports both Google Generative AI API (API key) and Vertex AI (service account).
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini client"""
        self.api_key = api_key or config.gemini.api_key
        self.model_name = config.gemini.model
        self.temperature = config.gemini.temperature
        self.location = getattr(config.gemini, 'location', 'us-central1')
        self.project_id = "auto-blogging-dplus"
        self._initialized = False
        self.model = None
        self.use_vertex_ai = False

        # Gemini 3 specific settings
        self.use_gemini_3 = getattr(config.gemini, 'use_gemini_3', True)
        self.thinking_level = getattr(config.gemini, 'thinking_level', 'high')
        self.include_thoughts = getattr(config.gemini, 'include_thoughts', False)
        self.media_resolution = getattr(config.gemini, 'media_resolution', 'media_resolution_medium')
        self.api_version = getattr(config.gemini, 'api_version', 'v1beta')

        # Conversation history for thought signatures
        self._conversation_history: List[Dict[str, Any]] = []
        self._thought_signatures: List[str] = []  # Accumulated thought signatures

    def _ensure_initialized(self):
        """Lazy initialization of Gemini"""
        if self._initialized:
            return

        try:
            # Prefer API key for Gemini 3 (better support for new features)
            if self.api_key:
                # Use Google Generative AI API
                logger.info("Initializing Google Generative AI API using API Key")
                self._init_google_ai()
                self.use_vertex_ai = False
            else:
                # Fall back to service account file
                sa_key_filename = "auto-blogging-dplus-7c31727bd1be.json"
                sa_key_path = os.path.join(os.getcwd(), sa_key_filename)

                if os.path.exists(sa_key_path):
                    # Use Vertex AI with service account
                    logger.info(f"Initializing Vertex AI using Service Account: {sa_key_filename}")
                    self._init_vertex_ai(sa_key_path)
                    self.use_vertex_ai = True
                else:
                    raise ValueError("No API key or service account found")

            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.model = None

    def _init_google_ai(self):
        """Initialize using Google Gen AI API (for API keys)"""
        from google import genai
        from google.genai import types

        self._client = genai.Client(
            api_key=self.api_key,
            http_options={'api_version': self.api_version} if self.use_gemini_3 else {}
        )

        # Store types for later use
        self._genai_types = types

        # Map model names for Google AI API
        model_name = self.model_name

        # Check if model is a Gemini 3 model
        gemini_3_models = [
            getattr(config.gemini, 'gemini_3_pro', 'gemini-3-pro-preview'),
            getattr(config.gemini, 'gemini_3_flash', 'gemini-3-flash-preview'),
            getattr(config.gemini, 'gemini_3_pro_image', 'gemini-3-pro-image-preview'),
            'gemini-3-pro-preview',
            'gemini-3-flash-preview',
            'gemini-3-pro-image-preview'
        ]

        is_gemini_3 = any(model_name.startswith(m.replace('-preview', '')) or model_name == m for m in gemini_3_models)

        if is_gemini_3:
            # Use the model as-is for Gemini 3
            self.model_name_for_api = model_name
            self.use_gemini_3 = True
        elif model_name.startswith("gemini-1.5-flash") or model_name.startswith("gemini-1.5-pro"):
            model_name = "gemini-2.0-flash-exp"  # Use newer model
            self.model_name_for_api = model_name
            self.use_gemini_3 = False
        elif model_name.startswith("gemini-2.0"):
            model_name = "gemini-2.0-flash-exp"
            self.model_name_for_api = model_name
            self.use_gemini_3 = False
        else:
            self.model_name_for_api = model_name

        self.model = True  # Sentinel value to indicate initialization succeeded
        logger.info(f"Initialized Google AI with model: {self.model_name_for_api} (Gemini 3: {self.use_gemini_3})")

    def _init_vertex_ai(self, sa_key_path: str):
        """Initialize using Vertex AI (for service accounts)"""
        import vertexai
        from vertexai.generative_models import GenerativeModel, GenerationConfig

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key_path
        vertexai.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel(self.model_name)
        self._GenerationConfig = GenerationConfig

    def _get_model_for_role(self, role: str) -> str:
        """
        Get the appropriate model based on the role.
        
        Args:
            role: "chat" for fast responses, "research" for deep thinking
            
        Returns:
            Model name string
        """
        if role == "research":
            model = getattr(config.gemini, 'research_model', config.gemini.gemini_3_pro)
            logger.info(f"Using Pro model for research: {model}")
            return model
        else:
            model = getattr(config.gemini, 'chat_model', config.gemini.gemini_3_flash)
            logger.info(f"Using Flash model for chat: {model}")
            return model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        role: str = "chat"  # "chat" for Flash (fast), "research" for Pro (deep thinking)
    ) -> GenerationResult:
        """
        Generate a response using Gemini.
        """
        self._ensure_initialized()
        if not self.model:
             return GenerationResult(text="", model=self.model_name, temperature=self.temperature, success=False, error="Gemini not initialized")

        # Select model based on role
        model_for_request = self._get_model_for_role(role)

        start_time = time.time()
        _rate_limit("gemini")

        with _api_semaphore:
            try:
                if self.use_vertex_ai:
                    result = self._generate_vertex_ai(prompt, system_prompt, temperature, max_tokens)
                else:
                    result = self._generate_google_ai(prompt, system_prompt, temperature, max_tokens, model_override=model_for_request)

                generation_time = time.time() - start_time
                result.generation_time = generation_time
                return result

            except Exception as e:
                generation_time = time.time() - start_time
                error_str = str(e)

                # Basic error classification
                error_type = "api_error"
                if "quota" in error_str.lower():
                    error_type = "quota"
                elif "429" in error_str:
                    error_type = "rate_limit"
                elif "permission" in error_str.lower() or "401" in error_str or "403" in error_str:
                    error_type = "auth"

                return GenerationResult(
                    text="",
                    model=self.model_name,
                    temperature=temperature or self.temperature,
                    generation_time=generation_time,
                    success=False,
                    error=error_str,
                    error_type=error_type
                )

    def _generate_google_ai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        model_override: Optional[str] = None
    ) -> GenerationResult:
        """Generate using Google Gen AI API with Gemini 3 support"""
        types = self._genai_types
        
        # Use model_override if provided, else use default
        model_to_use = model_override or self.model_name_for_api

        # Build config with Gemini 3 features
        config_kwargs = {}

        if self.use_gemini_3:
            # Thinking config for Gemini 3
            if self.thinking_level:
                config_kwargs['thinking_config'] = types.ThinkingConfig(
                    thinking_level=self.thinking_level
                )

            # Include thoughts in response if requested
            if self.include_thoughts:
                config_kwargs['thinking_config'] = config_kwargs.get('thinking_config', types.ThinkingConfig(
                    thinking_level=self.thinking_level
                ))
                config_kwargs['thinking_config'].include_thoughts = True

        # Build contents
        contents = prompt
        if system_prompt:
            contents = f"{system_prompt}\n\n{prompt}"

        # Create config object if we have special parameters
        generate_config = None
        if config_kwargs:
            generate_config = types.GenerateContentConfig(**config_kwargs)

        # Generate using the API with role-based model selection
        if generate_config:
            response = self._client.models.generate_content(
                model=model_to_use,
                contents=contents,
                config=generate_config
            )
        else:
            response = self._client.models.generate_content(
                model=model_to_use,
                contents=contents
            )

        # Extract thought signature if present
        thought_signature = None
        thoughts = None

        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        # Check for thought signature
                        if hasattr(part, 'thought_signature') and part.thought_signature:
                            thought_signature = part.thought_signature

                        # Check for thoughts (if include_thoughts=True)
                        if hasattr(part, 'text') and part.text:
                            # Thoughts may be in a specific format
                            if self.include_thoughts and thought_signature:
                                thoughts = part.text

        # Store thought signature for next turn
        if thought_signature:
            self._thought_signatures.append(thought_signature)

        # Try to get token count
        tokens_used = None
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            tokens_used = getattr(response.usage_metadata, 'total_token_count', None)

        return GenerationResult(
            text=response.text,
            model=self.model_name,
            temperature=temperature or self.temperature,
            tokens_used=tokens_used,
            thought_signature=thought_signature,
            thoughts=thoughts,
            thinking_level=self.thinking_level if self.use_gemini_3 else None,
            success=True
        )

    def _generate_vertex_ai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> GenerationResult:
        """Generate using Vertex AI"""
        gen_config = self._GenerationConfig(
            temperature=temperature or self.temperature,
            max_output_tokens=max_tokens
        )

        # Incorporate system prompt into the main prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = self.model.generate_content(
            full_prompt,
            generation_config=gen_config
        )

        tokens_used = None
        if hasattr(response, 'usage_metadata'):
            tokens_used = getattr(response.usage_metadata, 'total_token_count', None)

        return GenerationResult(
            text=response.text,
            model=self.model_name,
            temperature=temperature or self.temperature,
            tokens_used=tokens_used,
            success=True
        )

    def analyze(self, query: str, context: str) -> GenerationResult:
        """Perform a deep analysis using Gemini Pro (research role)."""
        analysis_prompt = f"CONTEXT:\n{context}\n\nQUERY:\n{query}\n\nBased on the context, provide a clear analysis."
        return self.generate(prompt=analysis_prompt, role="research")

    def generate_with_media(
        self,
        prompt: str,
        image_data: Optional[bytes] = None,
        mime_type: str = "image/jpeg",
        media_resolution: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> GenerationResult:
        """
        Generate using Gemini 3 with media support.

        Args:
            prompt: The text prompt
            image_data: Optional image data as bytes
            mime_type: MIME type of the image (default: image/jpeg)
            media_resolution: Media resolution level (low, medium, high, ultra_high)
            system_prompt: Optional system prompt
            temperature: Optional temperature override
        """
        self._ensure_initialized()
        if not self.model:
            return GenerationResult(
                text="",
                model=self.model_name,
                temperature=temperature or self.temperature,
                success=False,
                error="Gemini not initialized"
            )

        if not self.use_vertex_ai:
            return self._generate_with_media_google_ai(
                prompt, image_data, mime_type, media_resolution, system_prompt, temperature
            )
        else:
            # Vertex AI doesn't support the new media_resolution parameter yet
            return self.generate(prompt, system_prompt, temperature)

    def _generate_with_media_google_ai(
        self,
        prompt: str,
        image_data: Optional[bytes],
        mime_type: str,
        media_resolution: Optional[str],
        system_prompt: Optional[str],
        temperature: Optional[float]
    ) -> GenerationResult:
        """Generate with media using Google Gen AI API"""
        import base64
        types = self._genai_types

        # Build parts
        parts = [types.Part(text=prompt)]

        if image_data:
            # Build inline data part with optional media resolution
            inline_data_kwargs = {
                "mime_type": mime_type,
                "data": image_data
            }

            # Add media resolution if specified and using Gemini 3
            if self.use_gemini_3 and media_resolution:
                inline_data_kwargs["media_resolution"] = {"level": media_resolution}
            elif self.use_gemini_3 and self.media_resolution:
                inline_data_kwargs["media_resolution"] = {"level": self.media_resolution}

            parts.append(types.Part(
                inline_data=types.Blob(**inline_data_kwargs)
            ))

        # Build content with parts
        contents = [types.Content(parts=parts)]

        # Build config
        config_kwargs = {}
        if self.use_gemini_3 and self.thinking_level:
            config_kwargs['thinking_config'] = types.ThinkingConfig(
                thinking_level=self.thinking_level
            )

        generate_config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        start_time = time.time()
        _rate_limit("gemini")

        with _api_semaphore:
            try:
                if generate_config:
                    response = self._client.models.generate_content(
                        model=self.model_name_for_api,
                        contents=contents,
                        config=generate_config
                    )
                else:
                    response = self._client.models.generate_content(
                        model=self.model_name_for_api,
                        contents=contents
                    )

                generation_time = time.time() - start_time

                tokens_used = None
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    tokens_used = getattr(response.usage_metadata, 'total_token_count', None)

                return GenerationResult(
                    text=response.text,
                    model=self.model_name,
                    temperature=temperature or self.temperature,
                    tokens_used=tokens_used,
                    generation_time=generation_time,
                    success=True
                )

            except Exception as e:
                generation_time = time.time() - start_time
                error_str = str(e)
                error_type = "api_error"
                if "quota" in error_str.lower():
                    error_type = "quota"
                elif "429" in error_str:
                    error_type = "rate_limit"

                return GenerationResult(
                    text="",
                    model=self.model_name,
                    temperature=temperature or self.temperature,
                    generation_time=generation_time,
                    success=False,
                    error=error_str,
                    error_type=error_type
                )

    def generate_conversation(
        self,
        prompt: str,
        history: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> GenerationResult:
        """
        Generate with multi-turn conversation support using thought signatures.

        Args:
            prompt: The current user message
            history: Optional conversation history with thought signatures
            system_prompt: Optional system prompt
            temperature: Optional temperature override
        """
        self._ensure_initialized()
        if not self.model:
            return GenerationResult(
                text="",
                model=self.model_name,
                temperature=temperature or self.temperature,
                success=False,
                error="Gemini not initialized"
            )

        if not self.use_vertex_ai and self.use_gemini_3:
            return self._generate_conversation_google_ai(prompt, history, system_prompt, temperature)
        else:
            # For non-Gemini 3, just use regular generate
            return self.generate(prompt, system_prompt, temperature)

    def _generate_conversation_google_ai(
        self,
        prompt: str,
        history: Optional[List[Dict[str, Any]]],
        system_prompt: Optional[str],
        temperature: Optional[float]
    ) -> GenerationResult:
        """Generate with conversation using Google Gen AI API"""
        types = self._genai_types

        # Build contents from history
        contents = []

        if system_prompt:
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=system_prompt)]
            ))

        # Add history
        if history:
            for item in history:
                role = item.get("role", "user")
                if role == "user":
                    contents.append(types.Content(
                        role="user",
                        parts=[types.Part(text=item.get("content", ""))]
                    ))
                elif role == "model":
                    # Model response with thought signature
                    parts = [types.Part(text=item.get("content", ""))]
                    if "thought_signature" in item:
                        parts[0].thought_signature = item["thought_signature"]
                    contents.append(types.Content(role="model", parts=parts))

        # Add current prompt
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        ))

        # Build config
        config_kwargs = {}
        if self.thinking_level:
            config_kwargs['thinking_config'] = types.ThinkingConfig(
                thinking_level=self.thinking_level
            )

        generate_config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        start_time = time.time()
        _rate_limit("gemini")

        with _api_semaphore:
            try:
                if generate_config:
                    response = self._client.models.generate_content(
                        model=self.model_name_for_api,
                        contents=contents,
                        config=generate_config
                    )
                else:
                    response = self._client.models.generate_content(
                        model=self.model_name_for_api,
                        contents=contents
                    )

                generation_time = time.time() - start_time

                # Extract thought signature
                thought_signature = None
                if hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'thought_signature') and part.thought_signature:
                                    thought_signature = part.thought_signature
                                    break

                tokens_used = None
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    tokens_used = getattr(response.usage_metadata, 'total_token_count', None)

                result = GenerationResult(
                    text=response.text,
                    model=self.model_name,
                    temperature=temperature or self.temperature,
                    tokens_used=tokens_used,
                    generation_time=generation_time,
                    thought_signature=thought_signature,
                    thinking_level=self.thinking_level,
                    success=True
                )

                # Update conversation history
                self._conversation_history.append({
                    "role": "user",
                    "content": prompt
                })
                self._conversation_history.append({
                    "role": "model",
                    "content": response.text,
                    "thought_signature": thought_signature
                })

                return result

            except Exception as e:
                generation_time = time.time() - start_time
                error_str = str(e)
                error_type = "api_error"
                if "quota" in error_str.lower():
                    error_type = "quota"

                return GenerationResult(
                    text="",
                    model=self.model_name,
                    temperature=temperature or self.temperature,
                    generation_time=generation_time,
                    success=False,
                    error=error_str,
                    error_type=error_type
                )

    def clear_conversation_history(self):
        """Clear the conversation history and thought signatures."""
        self._conversation_history = []
        self._thought_signatures = []

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history."""
        return self._conversation_history.copy()

# Singleton instances
_gemini_instance: Optional[GeminiClient] = None

def get_gemini_client() -> GeminiClient:
    """Get or create the singleton GeminiClient instance"""
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = GeminiClient()
    return _gemini_instance

def get_client() -> GeminiClient:
    """Primary client getter (now returns Gemini)"""
    return get_gemini_client()

def reset_client():
    """Reset the singleton client instance"""
    global _gemini_instance
    _gemini_instance = None

# Backwards compatibility aliases
ZaiClient = GeminiClient
ZhipuClient = GeminiClient
