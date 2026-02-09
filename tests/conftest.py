"""Shared pytest fixtures for Light Agent tests."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

from light_agent.agent.tools.base import Tool
from light_agent.providers.base import LLMProvider, LLMResponse


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, Any, Any]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_workspace() -> Generator[str, Any, Any]:
    """Create a temporary workspace directory."""
    with TemporaryDirectory() as tmp:
        yield tmp


@pytest.fixture
def sample_tool() -> MagicMock:
    """Create a sample tool for testing."""
    tool = MagicMock(spec=Tool)
    tool.name = "test_tool"
    tool.description = "A test tool"
    tool.parameters = {
        "type": "object",
        "properties": {"input": {"type": "string", "description": "Input string"}},
        "required": ["input"],
    }
    tool.execute = AsyncMock(return_value="test result")
    return tool


@pytest.fixture
def mock_provider() -> MagicMock:
    """Create a mock LLM provider."""
    provider = MagicMock(spec=LLMProvider)
    provider.generate = AsyncMock(
        return_value=LLMResponse(content="Mock response", tool_calls=None)
    )
    provider.generate_stream = AsyncMock(return_value=iter(["Mock", " response"]))
    provider.get_default_model = MagicMock(return_value="test/model")
    provider.is_reasoning_model = MagicMock(return_value=False)
    return provider


@pytest.fixture
def mock_reasoning_provider() -> MagicMock:
    """Create a mock LLM provider for reasoning models."""
    provider = MagicMock(spec=LLMProvider)
    provider.generate = AsyncMock(
        return_value=LLMResponse(
            content="Reasoning response",
            reasoning_content="Reasoning trace",
            tool_calls=None,
        )
    )
    provider.get_default_model = MagicMock(return_value="o1-reasoning")
    provider.is_reasoning_model = MagicMock(return_value=True)
    return provider


@pytest.fixture
def mock_provider_with_tools() -> MagicMock:
    """Create a mock LLM provider that returns tool calls."""
    tool_call = MagicMock()
    tool_call.id = "call_123"
    tool_call.function.name = "test_tool"
    tool_call.function.arguments = '{"input": "test"}'

    provider = MagicMock(spec=LLMProvider)
    provider.generate = AsyncMock(
        return_value=LLMResponse(
            content="Please use the tool",
            tool_calls=[tool_call],
        )
    )
    provider.get_default_model = MagicMock(return_value="test/model")
    provider.is_reasoning_model = MagicMock(return_value=False)
    return provider


@pytest.fixture
def sample_messages() -> list[dict[str, str]]:
    """Sample message list for testing."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, world!"},
    ]
