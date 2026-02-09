"""Tests for LLMProvider base class."""

from typing import Any, AsyncGenerator, Optional
from unittest.mock import MagicMock

import pytest

from lightagent.providers.base import LLMProvider, LLMResponse


class ConcreteProvider(LLMProvider):
    """Concrete implementation of LLMProvider for testing."""

    def __init__(self, response: LLMResponse | None = None):
        self._response = response or LLMResponse(content="test")

    async def generate(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> LLMResponse:
        return self._response

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        if self._response.content:
            yield self._response.content

    def get_default_model(self) -> str:
        return "test/model"


class TestLLMResponse:
    """Tests for LLMResponse model."""

    def test_response_with_content(self) -> None:
        """Test response with only content."""
        response = LLMResponse(content="Hello")
        assert response.content == "Hello"
        assert response.tool_calls is None
        assert response.reasoning_content is None
        assert not response.has_tool_calls
        assert not response.has_reasoning

    def test_response_with_tool_calls(self) -> None:
        """Test response with tool calls."""
        tool_call = MagicMock()
        tool_call.id = "call_1"
        response = LLMResponse(content="Use tool", tool_calls=[tool_call])
        assert response.has_tool_calls
        assert not response.has_reasoning

    def test_response_with_reasoning(self) -> None:
        """Test response with reasoning content."""
        response = LLMResponse(content="Answer", reasoning_content="Thinking...")
        assert response.has_reasoning
        assert not response.has_tool_calls

    def test_response_with_all_fields(self) -> None:
        """Test response with all fields."""
        tool_call = MagicMock()
        response = LLMResponse(
            content="Answer",
            tool_calls=[tool_call],
            reasoning_content="Thinking...",
            raw={"extra": "data"},
        )
        assert response.content == "Answer"
        assert response.tool_calls is not None and len(response.tool_calls) == 1
        assert response.reasoning_content == "Thinking..."
        assert response.raw == {"extra": "data"}
        assert response.has_tool_calls
        assert response.has_reasoning


class TestLLMProvider:
    """Tests for LLMProvider base class."""

    def test_is_reasoning_model_o_series(self) -> None:
        """Test detection of OpenAI o-series models."""
        provider = ConcreteProvider()
        assert provider.is_reasoning_model("o1")
        assert provider.is_reasoning_model("o3")
        assert provider.is_reasoning_model("o4-mini")
        assert not provider.is_reasoning_model("gpt-4")

    def test_is_reasoning_model_deepseek(self) -> None:
        """Test detection of DeepSeek reasoning models."""
        provider = ConcreteProvider()
        assert provider.is_reasoning_model("deepseek/deepseek-r1")
        assert provider.is_reasoning_model("deepseek-r1")

    def test_is_reasoning_model_case_insensitive(self) -> None:
        """Test that reasoning model detection is case insensitive."""
        provider = ConcreteProvider()
        assert provider.is_reasoning_model("O1")
        assert provider.is_reasoning_model("DeepSeek R1")

    def test_is_reasoning_model_default(self) -> None:
        """Test reasoning model detection uses default model when none provided."""
        provider = ConcreteProvider()
        assert not provider.is_reasoning_model()

    @pytest.mark.asyncio
    async def test_generate_stream_fallback(self) -> None:
        """Test that streaming falls back to non-streaming when not overridden."""

        class NoStreamProvider(LLMProvider):
            async def generate(
                self,
                messages: list[dict[str, str]],
                tools: Optional[list[dict[str, Any]]] = None,
                model: Optional[str] = None,
            ) -> LLMResponse:
                return LLMResponse(content="test response")

            def get_default_model(self) -> str:
                return "test"

        provider = NoStreamProvider()

        chunks = []
        async for chunk in provider.generate_stream([]):
            chunks.append(chunk)

        assert chunks == ["test response"]
