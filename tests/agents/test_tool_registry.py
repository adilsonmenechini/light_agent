"""Tests for ToolRegistry."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from light_agent.agent.tools.base import Tool
from light_agent.agent.tools.registry import ToolRegistry


class SimpleTool(Tool):
    """Simple tool for testing."""

    @property
    def name(self) -> str:
        return "simple_tool"

    @property
    def description(self) -> str:
        return "A simple tool"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> str:
        return "simple result"


class ParameterTool(Tool):
    """Tool with parameters for testing."""

    @property
    def name(self) -> str:
        return "parameter_tool"

    @property
    def description(self) -> str:
        return "Tool with parameters"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"input": {"type": "string", "description": "Input"}},
            "required": ["input"],
        }

    async def execute(self, **kwargs: Any) -> str:
        return f"parameter result: {kwargs.get('input')}"


class ErrorTool(Tool):
    """Tool that raises an error for testing."""

    @property
    def name(self) -> str:
        return "error_tool"

    @property
    def description(self) -> str:
        return "Tool that errors"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> str:
        raise ValueError("Test error")


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_init(self) -> None:
        """Test registry initialization."""
        registry = ToolRegistry()
        assert len(registry) == 0
        assert registry.tool_names == []

    def test_register_tool(self) -> None:
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = SimpleTool()
        registry.register(tool)
        assert len(registry) == 1
        assert "simple_tool" in registry

    def test_register_multiple_tools(self) -> None:
        """Test registering multiple tools."""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        registry.register(ParameterTool())
        assert len(registry) == 2
        assert "simple_tool" in registry
        assert "parameter_tool" in registry

    def test_unregister_tool(self) -> None:
        """Test unregistering a tool."""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        registry.unregister("simple_tool")
        assert len(registry) == 0
        assert "simple_tool" not in registry

    def test_unregister_nonexistent(self) -> None:
        """Test unregistering a tool that doesn't exist."""
        registry = ToolRegistry()
        registry.unregister("nonexistent")  # Should not raise
        assert len(registry) == 0

    def test_get_tool(self) -> None:
        """Test getting a tool by name."""
        registry = ToolRegistry()
        tool = SimpleTool()
        registry.register(tool)
        retrieved = registry.get("simple_tool")
        assert retrieved is tool

    def test_get_nonexistent(self) -> None:
        """Test getting a nonexistent tool returns None."""
        registry = ToolRegistry()
        result = registry.get("nonexistent")
        assert result is None

    def test_has_tool(self) -> None:
        """Test checking if tool exists."""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        assert registry.has("simple_tool")
        assert not registry.has("nonexistent")

    def test_get_definitions(self) -> None:
        """Test getting tool definitions in OpenAI format."""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        definitions = registry.get_definitions()
        assert len(definitions) == 1
        assert definitions[0]["function"]["name"] == "simple_tool"

    @pytest.mark.asyncio
    async def test_execute_tool(self) -> None:
        """Test executing a registered tool."""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        result = await registry.execute("simple_tool", {})
        assert result == "simple result"

    @pytest.mark.asyncio
    async def test_execute_with_parameters(self) -> None:
        """Test executing tool with parameters."""
        registry = ToolRegistry()
        registry.register(ParameterTool())
        result = await registry.execute("parameter_tool", {"input": "hello"})
        assert result == "parameter result: hello"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self) -> None:
        """Test executing nonexistent tool returns error message."""
        registry = ToolRegistry()
        result = await registry.execute("nonexistent", {})
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_invalid_parameters(self) -> None:
        """Test executing tool with invalid parameters."""
        registry = ToolRegistry()
        registry.register(ParameterTool())
        result = await registry.execute("parameter_tool", {"invalid": "params"})
        assert "invalid parameters" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_error(self) -> None:
        """Test executing tool that raises an error."""
        registry = ToolRegistry()
        registry.register(ErrorTool())
        result = await registry.execute("error_tool", {})
        assert "error executing" in result.lower()
        assert "test error" in result.lower()

    def test_len(self) -> None:
        """Test len() returns correct count."""
        registry = ToolRegistry()
        assert len(registry) == 0
        registry.register(SimpleTool())
        assert len(registry) == 1
        registry.register(ParameterTool())
        assert len(registry) == 2

    def test_contains(self) -> None:
        """Test 'in' operator."""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        assert "simple_tool" in registry
        assert "nonexistent" not in registry

    @pytest.mark.asyncio
    async def test_execute_async(self) -> None:
        """Test async execution via execute method."""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        result = await registry.execute("simple_tool", {})
        assert result == "simple result"

    @pytest.mark.asyncio
    async def test_get_all_tool_schemas_empty(self) -> None:
        """Test getting all tool schemas when empty."""
        registry = ToolRegistry()
        schemas = await registry.get_all_tool_schemas()
        assert schemas == []

    @pytest.mark.asyncio
    async def test_get_all_tool_schemas_with_tools(self) -> None:
        """Test getting all tool schemas with registered tools."""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        registry.register(ParameterTool())
        schemas = await registry.get_all_tool_schemas()
        assert len(schemas) == 2

    @pytest.mark.asyncio
    async def test_get_all_tool_schemas_with_mcp(self) -> None:
        """Test getting all tool schemas including MCP tools."""
        registry = ToolRegistry()
        registry.register(SimpleTool())

        # Mock MCP client
        mock_mcp = MagicMock()
        mock_mcp.name = "test_mcp"
        mock_mcp.get_tools = AsyncMock(
            return_value=[
                {
                    "name": "mcp__test_mcp__fetch",
                    "description": "Fetch URL",
                    "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}},
                }
            ]
        )
        mock_mcp.call_tool = AsyncMock(return_value="fetched content")

        registry.mcp_clients.append(mock_mcp)

        schemas = await registry.get_all_tool_schemas()
        assert len(schemas) == 2
        assert schemas[0]["function"]["name"] == "simple_tool"
        assert schemas[1]["function"]["name"] == "mcp__test_mcp__fetch"

    @pytest.mark.asyncio
    async def test_call_tool_native(self) -> None:
        """Test calling a native tool."""
        registry = ToolRegistry()
        registry.register(ParameterTool())
        result = await registry.call_tool("parameter_tool", {"input": "test"})
        assert result == "parameter result: test"

    @pytest.mark.asyncio
    async def test_call_tool_mcp_format(self) -> None:
        """Test calling an MCP tool with __ separator."""
        registry = ToolRegistry()

        # Mock MCP client
        mock_mcp = MagicMock()
        mock_mcp.name = "fetch_mcp"
        mock_mcp.get_tools = AsyncMock(return_value=[])
        mock_mcp.call_tool = AsyncMock(return_value="fetched")

        registry.mcp_clients.append(mock_mcp)

        result = await registry.call_tool("fetch_mcp__fetch", {"url": "http://test.com"})
        assert result == "fetched"
        mock_mcp.call_tool.assert_called_once()
