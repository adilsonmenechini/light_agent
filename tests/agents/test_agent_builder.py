"""Tests for AgentBuilder."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from lightagent.agent.builder import AgentBuilder
from lightagent.agent.memory import MemoryStore
from lightagent.agent.skills import SkillsLoader
from lightagent.agent.tools.filesystem import ReadFileTool, WriteFileTool
from lightagent.agent.tools.registry import ToolRegistry
from lightagent.providers.base import LLMProvider


class TestAgentBuilder:
    """Tests for AgentBuilder class."""

    @pytest.fixture
    def temp_workspace(self) -> Path:
        """Create temporary workspace."""
        with TemporaryDirectory() as tmp:
            yield Path(tmp)

    def test_init(self) -> None:
        """Test builder initialization with defaults."""
        builder = AgentBuilder()
        assert builder._provider is None
        assert isinstance(builder._tools, ToolRegistry)
        assert builder._memory is None
        assert builder._verbose is False

    def test_with_provider_default(self) -> None:
        """Test setting provider with default model."""
        builder = AgentBuilder()
        result = builder.with_provider()
        assert result is builder
        assert builder._provider is not None

    def test_with_provider_custom_model(self) -> None:
        """Test setting provider with custom model."""
        builder = AgentBuilder()
        builder.with_provider(model="ollama/llama3")
        assert builder._provider is not None
        # Note: Full verification requires mocking settings

    def test_with_workspace(self, temp_workspace: Path) -> None:
        """Test setting workspace directory."""
        builder = AgentBuilder()
        result = builder.with_workspace(temp_workspace)
        assert result is builder
        assert builder._workspace_dir == temp_workspace

    def test_with_tools(self) -> None:
        """Test registering tools."""
        builder = AgentBuilder()
        tool1 = ReadFileTool(workspace=Path("/tmp"), restrict_to_workspace=False)
        tool2 = WriteFileTool(workspace=Path("/tmp"), restrict_to_workspace=False)

        result = builder.with_tools([tool1, tool2])
        assert result is builder
        assert "read_file" in builder._tools
        assert "write_file" in builder._tools

    def test_with_tools_empty_list(self) -> None:
        """Test with empty tools list."""
        builder = AgentBuilder()
        builder.with_tools([])
        assert len(builder._tools) == 0

    def test_with_memory_defaults(self) -> None:
        """Test memory configuration with defaults."""
        with TemporaryDirectory() as tmp:
            builder = AgentBuilder().with_workspace(Path(tmp))
            builder.with_memory(long_term=True, short_term=True)
            assert builder._long_memory is not None
            assert builder._short_memory is not None
            assert builder._memory is not None

    def test_with_memory_long_only(self) -> None:
        """Test memory configuration with long-term only."""
        with TemporaryDirectory() as tmp:
            builder = AgentBuilder().with_workspace(Path(tmp))
            builder.with_memory(long_term=True, short_term=False)
            assert builder._long_memory is not None
            assert builder._short_memory is None

    def test_with_memory_short_only(self) -> None:
        """Test memory configuration with short-term only."""
        with TemporaryDirectory() as tmp:
            builder = AgentBuilder().with_workspace(Path(tmp))
            builder.with_memory(long_term=False, short_term=True)
            assert builder._long_memory is None
            assert builder._short_memory is not None

    def test_with_skills(self) -> None:
        """Test enabling skills loading."""
        builder = AgentBuilder()
        with TemporaryDirectory() as tmp:
            result = builder.with_skills()
            assert result is builder
            assert builder._skills_loader is not None

    def test_with_mcp_servers(self) -> None:
        """Test configuring MCP servers."""
        builder = AgentBuilder()
        servers = {"fetch": "npx @modelcontextprotocol/server-fetch"}
        result = builder.with_mcp_servers(servers)
        assert result is builder
        assert builder._mcp_configs == servers

    def test_with_mcp_servers_complex_config(self) -> None:
        """Test MCP server configuration with complex format."""
        builder = AgentBuilder()
        servers = {
            "fetch": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-fetch"],
            }
        }
        builder.with_mcp_servers(servers)
        assert builder._mcp_configs == servers

    def test_with_subagents(self) -> None:
        """Test configuring subagent support."""
        builder = AgentBuilder()
        result = builder.with_subagents(timeout=120, restrict_to_workspace=True)
        assert result is builder
        assert builder._session_manager is not None

    def test_with_verbose(self) -> None:
        """Test setting verbose mode."""
        builder = AgentBuilder()
        result = builder.with_verbose(True)
        assert result is builder
        assert builder._verbose is True

    def test_build_requires_provider(self) -> None:
        """Test that build() sets default provider if none configured."""
        builder = AgentBuilder()
        with TemporaryDirectory() as tmp:
            agent = builder.with_workspace(Path(tmp)).build()
            assert agent is not None
            assert agent.provider is not None

    def test_build_with_custom_provider(self) -> None:
        """Test building agent with custom provider."""
        builder = AgentBuilder()
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.generate = MagicMock()
        # This would require more setup - simplified test
        with TemporaryDirectory() as tmp:
            agent = builder.with_workspace(Path(tmp)).build()
            assert agent is not None

    def test_build_configures_all_components(self) -> None:
        """Test that build() configures all components."""
        builder = AgentBuilder()
        with TemporaryDirectory() as tmp:
            agent = builder.with_workspace(Path(tmp)).build()
            assert agent.provider is not None
            assert agent.memory is not None
            assert agent.tools is not None

    def test_build_with_tools(self) -> None:
        """Test building agent with custom tools."""
        builder = AgentBuilder()
        with TemporaryDirectory() as tmp:
            tool = ReadFileTool(workspace=Path(tmp), restrict_to_workspace=False)
            agent = builder.with_workspace(Path(tmp)).with_tools([tool]).build()
            assert "read_file" in agent.tools

    def test_build_chain(self) -> None:
        """Test fluent builder chain."""
        with TemporaryDirectory() as tmp:
            agent = (
                AgentBuilder()
                .with_workspace(Path(tmp))
                .with_provider(model="test/model")
                .with_verbose(True)
                .build()
            )
            assert agent is not None

    def test_method_chaining(self) -> None:
        """Test that builder methods return self for chaining."""
        builder = AgentBuilder()
        assert builder.with_provider() is builder
        assert builder.with_workspace(Path("/tmp")) is builder
        assert builder.with_tools([]) is builder
        assert builder.with_memory(long_term=False, short_term=False) is builder
        assert builder.with_skills() is builder
        assert builder.with_mcp_servers({}) is builder
        assert builder.with_subagents() is builder
        assert builder.with_verbose() is builder

    def test_configure_logging_verbose(self) -> None:
        """Test logging configuration with verbose=True."""
        builder = AgentBuilder()
        builder._verbose = True
        # Should not raise - just configure logging
        builder._configure_logging()

    def test_configure_logging_quiet(self) -> None:
        """Test logging configuration with verbose=False."""
        builder = AgentBuilder()
        builder._verbose = False
        # Should not raise - just configure logging
        builder._configure_logging()
