"""Tool registry for dynamic tool management."""

from typing import Any

from light_agent.agent.skills import SkillsLoader
from light_agent.agent.tools.base import Tool


class ToolRegistry:
    """
    Registry for agent tools.

    Allows dynamic registration and execution of tools.
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self.mcp_clients = []
        self.skills_loader: SkillsLoader | None = None

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def get_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions in OpenAI format."""
        return [tool.to_schema() for tool in self._tools.values()]

    async def execute(self, name: str, params: dict[str, Any]) -> str:
        """
        Execute a tool by name with given parameters.

        Args:
            name: Tool name.
            params: Tool parameters.

        Returns:
            Tool execution result as string.

        Raises:
            KeyError: If tool not found.
        """
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found"

        try:
            errors = tool.validate_params(params)
            if errors:
                return f"Error: Invalid parameters for tool '{name}': " + "; ".join(errors)
            return await tool.execute(**params)
        except Exception as e:
            return f"Error executing {name}: {str(e)}"

    @property
    def tool_names(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    async def get_all_tool_schemas(self) -> list[dict[str, Any]]:
        """Get all tool schemas from both native tools and MCP clients."""
        schemas = self.get_definitions()

        # Add MCP tools
        for mcp_client in self.mcp_clients:
            mcp_tools = await mcp_client.get_tools()
            for tool in mcp_tools:
                schemas.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool.get("description", ""),
                            "parameters": tool.get("input_schema", {}),
                        },
                    }
                )

        return schemas

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """
        Call a tool by name with given arguments.

        Handles both native tools and MCP tools.
        """
        # Check if it's an MCP tool (format: mcp_name__tool_name)
        if "__" in name:
            for mcp_client in self.mcp_clients:
                if name.startswith(f"{mcp_client.name}__"):
                    return await mcp_client.call_tool(name, arguments)

        # Otherwise, execute as native tool
        return await self.execute(name, arguments)
