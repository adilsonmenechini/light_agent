from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Coroutine, Dict, List, Optional

from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Response from LLM with content, tool calls, and reasoning support."""

    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None
    raw: Any = None
    reasoning_content: Optional[str] = None

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls and len(self.tool_calls) > 0)

    @property
    def has_reasoning(self) -> bool:
        return bool(self.reasoning_content and len(self.reasoning_content) > 0)


class LLMProvider(ABC):
    """Abstract base class for LLM providers with reasoning support."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """Generate response with optional tool calls."""
        pass

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response for lower perceived latency.

        Override this method in providers that support streaming.
        Default implementation falls back to non-streaming.
        """
        response = await self.generate(messages, tools, model)
        if response.content:
            yield response.content

    @abstractmethod
    def get_default_model(self) -> str:
        pass

    def is_reasoning_model(self, model: Optional[str] = None) -> bool:
        """Check if model is a reasoning model (e.g., o1, o3, DeepSeek R1)."""
        model_name = model or self.get_default_model()
        reasoning_patterns = ["o1", "o2", "o3", "o4", "deepseek", "r1", "reasoning"]
        return any(pattern in model_name.lower() for pattern in reasoning_patterns)
