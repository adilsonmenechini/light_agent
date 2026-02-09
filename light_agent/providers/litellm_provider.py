from typing import Any, AsyncGenerator, Dict, List, Optional, cast

import litellm
from loguru import logger

from light_agent.providers.base import LLMProvider, LLMResponse


class LiteLLMProvider(LLMProvider):
    """Provider using LiteLLM for unified API access with multi-provider support.

    Supports Ollama, OpenAI, LLMStudy, and other OpenAI-compatible APIs.
    """

    # Mapping of reasoning content field names across different providers
    REASONING_FIELD_NAMES = ["reasoning_content", "reasoning", "thinking", "thought"]

    # Provider patterns for auto-detection
    PROVIDER_PATTERNS = {
        "ollama": ["ollama", "localhost", "127.0.0.1:11434"],
        "llmstudy": ["llmstudy", "llmstudy.ai", "api.llmstudy.ai"],
        "openai": ["openai", "api.openai.com"],
        "deepseek": ["deepseek", "api.deepseek.com"],
        "anthropic": ["anthropic", "api.anthropic.com"],
        "azure": ["azure", "openai.azure.com"],
        "qwen": ["qwen", "api.qwen-tongyi.com", "tongyi"],
    }

    # Model prefixes that are OpenAI-compatible
    OPENAI_COMPATIBLE_PREFIXES = [
        "qwen",
        "moonshot",
        "yi",
        "minimax",
        "zhipu",
        "openrouter",
        "cerebras",
        "groq",
        "fireworks",
    ]

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def _detect_provider(self) -> str:
        """Detect provider based on base_url and model name."""
        base = (self.base_url or "").lower()
        model = self.model.lower()

        # Check model prefix first
        if "/" in self.model:
            prefix = self.model.split("/")[0]

            # Known providers
            if prefix in ["ollama", "openai", "deepseek", "anthropic", "azure"]:
                return prefix

            # OpenAI-compatible providers
            if prefix in self.OPENAI_COMPATIBLE_PREFIXES:
                return "openai"

        # Check base_url patterns
        for provider, patterns in self.PROVIDER_PATTERNS.items():
            for pattern in patterns:
                if pattern in base:
                    return provider

        # Default to openai-compatible (most APIs are)
        return "openai"

    def _get_model_for_provider(self, provider: str) -> str:
        """Get model name in correct format for provider."""
        # Remove provider prefix if present
        model = self.model
        if "/" in model:
            model = model.split("/", 1)[1]

        return model

    def _get_base_url(self, provider: str) -> Optional[str]:
        """Get base URL for provider if not set."""
        if self.base_url:
            return self.base_url

        # Provider-specific defaults
        defaults = {
            "ollama": "http://localhost:11434",
            "openai": "https://api.openai.com/v1",
            "deepseek": "https://api.deepseek.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "azure": None,  # Azure uses deployment_id instead
        }

        return defaults.get(provider)

    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key with provider-specific env var fallback."""
        if self.api_key:
            return self.api_key

        # Provider-specific environment variables
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "azure": "AZURE_OPENAI_API_KEY",
            "ollama": None,  # Ollama doesn't need API key
            "llmstudy": "LLMSTUDY_API_KEY",
        }

        import os

        env_key = env_vars.get(provider)
        if env_key:
            return os.environ.get(env_key)

        return None

    def is_reasoning_model(self, model: Optional[str] = None) -> bool:
        """Check if model is a reasoning model (e.g., o1, o3, DeepSeek R1)."""
        model_name = model or self.model
        reasoning_patterns = ["o1", "o2", "o3", "o4", "deepseek", "r1", "reasoning"]
        return any(pattern in model_name.lower() for pattern in reasoning_patterns)

    def _get_completion_params(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build completion parameters with optimizations for different model types."""
        from light_agent.config.settings import settings

        model_to_use = model or self.model
        is_reasoning = self.is_reasoning_model(model_to_use)
        provider = self._detect_provider()

        # Get provider-specific configuration
        base_url = self._get_base_url(provider)
        api_key = self._get_api_key(provider)
        clean_model = self._get_model_for_provider(provider)

        params: Dict[str, Any] = {
            "model": clean_model,
            "messages": messages,
            "api_key": api_key,
            "timeout": getattr(settings, "REQUEST_TIMEOUT", 120),
        }

        # Add base_url if available
        if base_url:
            params["base_url"] = base_url

        # Add tools if provided
        if tools:
            params["tools"] = tools

        # Reasoning models have different parameter requirements
        if is_reasoning:
            params.update(
                {
                    "temperature": None,
                    "max_completion_tokens": 8192,
                }
            )
        else:
            params.update(
                {
                    "temperature": 0.7,
                    "top_k": 20,
                    "top_p": 0.8,
                    "repeat_penalty": 1.1,
                }
            )

        # Provider-specific adjustments
        if provider == "ollama":
            # Ollama-specific options
            params["num_predict"] = params.pop("max_completion_tokens", 512)

        logger.debug(
            f"LiteLLM request: provider={provider}, model={clean_model}, "
            f"base_url={base_url}, is_reasoning={is_reasoning}"
        )

        return params

    def _extract_reasoning_content(self, message: Any) -> Optional[str]:
        """Extract reasoning content from message using multiple field names."""
        for field_name in self.REASONING_FIELD_NAMES:
            content = getattr(message, field_name, None)
            if content:
                return content
        return None

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """Generate response with optional tool calls and reasoning support."""
        model_to_use = model or self.model
        params = self._get_completion_params(messages, tools, model)

        response = await litellm.acompletion(**params)

        # Cast to handle LiteLLM's complex type hierarchy
        response_cast = cast(Any, response)
        choice = response_cast.choices[0]
        content = choice.message.content
        tool_calls = getattr(choice.message, "tool_calls", None)

        # Extract reasoning_content for models that support it
        reasoning_content = self._extract_reasoning_content(choice.message)

        if reasoning_content:
            logger.debug(
                f"Reasoning content extracted from {model_to_use}: {len(reasoning_content)} chars"
            )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            raw=response,
            reasoning_content=reasoning_content,
        )

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response for lower perceived latency."""
        model_to_use = model or self.model

        # Reasoning models often don't support streaming
        if self.is_reasoning_model(model_to_use):
            response = await self.generate(messages, tools, model)
            if response.content:
                yield response.content
            return

        params = self._get_completion_params(messages, tools, model)
        params["stream"] = True

        stream = await litellm.acompletion(**params)

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def get_default_model(self) -> str:
        return self.model


class OllamaOptimizer:
    """Optimization utilities for Ollama on Apple Silicon M3."""

    OLLAMA_M3_CONFIG = {
        "num_predict": 256,
        "temperature": 0.7,
        "top_k": 20,
        "top_p": 0.8,
        "repeat_penalty": 1.1,
    }

    @staticmethod
    def create_ollama_provider(
        model: str = "llama3.2:3b",
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:11434",
    ) -> "LiteLLMProvider":
        """Factory for optimized Ollama provider."""
        return LiteLLMProvider(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

    @staticmethod
    def get_model_settings() -> Dict[str, Any]:
        """Return optimized config for Ollama."""
        return OllamaOptimizer.OLLAMA_M3_CONFIG
