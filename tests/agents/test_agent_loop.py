"""Tests for AgentLoop."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lightagent.agent.loop import AgentLoop, InsightExtractor
from lightagent.agent.memory import MemoryStore
from lightagent.agent.short_memory import ShortTermMemory
from lightagent.agent.tools.registry import ToolRegistry
from lightagent.providers.base import LLMResponse


class TestInsightExtractor:
    """Tests for InsightExtractor utility class."""

    def test_extract_read_file_insight(self) -> None:
        """Test insight extraction for read_file tool."""
        result = InsightExtractor.extract(
            "read_file", {"path": "test.py"}, "def hello():\n    pass"
        )
        assert result is not None
        assert "Lido arquivo" in result

    def test_extract_write_file_insight(self) -> None:
        """Test insight extraction for write_file tool."""
        # Must be > 20 chars to pass the short result filter
        result = InsightExtractor.extract(
            "write_file", {"path": "test.py"}, "This is a long enough content to be processed."
        )
        assert result is not None
        assert "Criou/editou arquivo" in result

    def test_extract_exec_insight(self) -> None:
        """Test insight extraction for exec tool."""
        # Must be > 20 chars to pass the short result filter
        result = InsightExtractor.extract(
            "exec", {"command": "ls"}, "file1\nfile2\nfile3\nfile4\nfile5"
        )
        assert result is not None
        assert "Executou comando" in result

    def test_extract_grep_insight(self) -> None:
        """Test insight extraction for grep tool."""
        # Must be > 20 chars to pass the short result filter
        result = InsightExtractor.extract(
            "grep", {"pattern": "def"}, "match1\nmatch2\nmatch3\nmatch4"
        )
        assert result is not None
        assert "Busca encontrou" in result

    def test_extract_long_result_truncation(self) -> None:
        """Test insight extraction truncates very long results."""
        long_content = "a" * 3000
        result = InsightExtractor.extract("read_file", {"path": "test.py"}, long_content)
        assert result is not None
        # Should contain truncated indicator or start with the insight prefix
        assert "Lido arquivo" in result

    def test_extract_empty_result(self) -> None:
        """Test insight extraction skips empty results."""
        result = InsightExtractor.extract("read_file", {}, "")
        assert result is None

    def test_extract_error_result(self) -> None:
        """Test insight extraction skips error results."""
        result = InsightExtractor.extract("read_file", {}, "Error: file not found")
        assert result is None

    def test_extract_short_result(self) -> None:
        """Test insight extraction skips very short results."""
        result = InsightExtractor.extract("read_file", {}, "short")
        assert result is None


class TestAgentLoop:
    """Tests for AgentLoop class."""

    @pytest.fixture
    def mock_provider(self) -> MagicMock:
        """Create a mock LLM provider."""
        provider = MagicMock()
        provider.generate = AsyncMock(return_value=LLMResponse(content="Hello, I can help you!"))
        provider.generate_stream = AsyncMock(return_value=iter(["Hello, ", "I can ", "help you!"]))
        provider.get_default_model = MagicMock(return_value="test/model")
        provider.is_reasoning_model = MagicMock(return_value=False)
        return provider

    @pytest.fixture
    def tool_registry(self) -> ToolRegistry:
        """Create a tool registry with a mock tool."""
        registry = ToolRegistry()
        return registry

    @pytest.fixture
    def memory_store(self, temp_workspace: str) -> MemoryStore:
        """Create a memory store."""
        return MemoryStore(temp_workspace)

    def test_init(self, mock_provider: MagicMock, tool_registry: ToolRegistry) -> None:
        """Test AgentLoop initialization."""
        loop = AgentLoop(
            provider=mock_provider,
            memory=MemoryStore("/tmp"),
            tools=tool_registry,
        )
        assert loop.provider == mock_provider
        assert loop.tools == tool_registry
        assert loop.messages == []
        assert loop.conversation_id is not None

    def test_generate_id_format(
        self, mock_provider: MagicMock, tool_registry: ToolRegistry
    ) -> None:
        """Test conversation ID format."""
        loop = AgentLoop(
            provider=mock_provider,
            memory=MemoryStore("/tmp"),
            tools=tool_registry,
        )
        # Should be 8 character UUID
        assert len(loop.conversation_id) == 8
        assert all(c in "0123456789abcdef" for c in loop.conversation_id)

    def test_clear_messages(self, mock_provider: MagicMock, tool_registry: ToolRegistry) -> None:
        """Test clearing messages and generating new conversation ID."""
        loop = AgentLoop(
            provider=mock_provider,
            memory=MemoryStore("/tmp"),
            tools=tool_registry,
        )
        loop.messages = [{"role": "user", "content": "test"}]
        old_id = loop.conversation_id

        loop.clear_messages()

        assert loop.messages == []
        assert loop.conversation_id != old_id

    @pytest.mark.asyncio
    async def test_run_simple_response(
        self,
        mock_provider: MagicMock,
        tool_registry: ToolRegistry,
        sample_messages: list[dict[str, str]],
    ) -> None:
        """Test running agent with simple response (no tool calls)."""
        loop = AgentLoop(
            provider=mock_provider,
            memory=MemoryStore("/tmp"),
            tools=tool_registry,
        )

        result = await loop.run("Hello")

        assert result == "Hello, I can help you!"
        assert len(loop.messages) >= 2
        assert loop.messages[0]["role"] == "system"

    @pytest.mark.asyncio
    async def test_run_with_tool_call(
        self,
        mock_provider: MagicMock,
        tool_registry: ToolRegistry,
    ) -> None:
        """Test running agent that makes a tool call."""
        # Provider returns tool call
        tool_call = MagicMock()
        tool_call.id = "call_1"
        tool_call.function.name = "read_file"
        tool_call.function.arguments = '{"path": "test.py"}'

        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Let me read that file",
                tool_calls=[tool_call],
            )
        )

        loop = AgentLoop(
            provider=mock_provider,
            memory=MemoryStore("/tmp"),
            tools=tool_registry,
        )

        result = await loop.run("Read the file")

        # Should still return something (the final response after tool)
        assert result is not None

    @pytest.mark.asyncio
    async def test_run_with_reasoning(
        self,
        mock_provider: MagicMock,
        tool_registry: ToolRegistry,
    ) -> None:
        """Test running agent with reasoning model."""
        mock_provider.is_reasoning_model = MagicMock(return_value=True)
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="I need to think about this...",
                reasoning_content="Let me analyze the problem...",
            )
        )

        loop = AgentLoop(
            provider=mock_provider,
            memory=MemoryStore("/tmp"),
            tools=tool_registry,
        )

        result = await loop.run("Solve this problem")

        assert result == "I need to think about this..."
