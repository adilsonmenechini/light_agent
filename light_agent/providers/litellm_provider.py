from typing import Any, AsyncGenerator, Dict, List, Optional, cast

import litellm
from loguru import logger

from light_agent.providers.base import LLMProvider, LLMResponse


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
            api_key=api_key or "ollama",
            base_url=base_url,
        )

    @staticmethod
    def get_model_settings() -> Dict[str, Any]:
        """Return optimized config for Ollama."""
        return OllamaOptimizer.OLLAMA_M3_CONFIG


class LiteLLMProvider(LLMProvider):
    """Provider using LiteLLM for unified API access with reasoning support."""

    # Mapping of reasoning content field names across different providers
    REASONING_FIELD_NAMES = ["reasoning_content", "reasoning", "thinking", "thought"]

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

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
        model_to_use = model or self.model
        is_reasoning = self.is_reasoning_model(model_to_use)

        params: Dict[str, Any] = {
            "model": model_to_use,
            "messages": messages,
            "api_key": self.api_key,
            "base_url": self.base_url,
        }

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
