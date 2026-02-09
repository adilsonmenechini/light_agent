import asyncio
import contextlib
import os
import shutil
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from loguru import logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from lightagent.utils.output import suppress_output as suppress_stdout


class MCPClient:
    def __init__(
        self,
        name: str,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        suppress_output: bool = False,
    ):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = env
        self.suppress_output = suppress_output
        self.session: Optional[ClientSession] = None
        self.exit_stack: AsyncExitStack = AsyncExitStack()

    async def connect(self):
        if self.args:
            final_command = self.command
            final_args = self.args
        else:
            # Fallback for legacy string command
            parts = self.command.split()
            final_command = parts[0]
            final_args = parts[1:]

        logger.info(
            f"Connecting to MCP server: {self.name} (cmd={final_command}, args={final_args})"
        )

        # Resolve command path if it's npx or similar
        if final_command == "npx":
            final_command = shutil.which("npx") or "npx"

        server_params = StdioServerParameters(
            command=final_command, args=final_args, env=self.env or dict(os.environ)
        )

        try:
            # Use context manager to suppress MCP server startup messages if requested
            ctx = suppress_stdout() if self.suppress_output else contextlib.nullcontext()

            with ctx:
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                read, write = stdio_transport
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()

            self.session = session
            logger.success(f"Connected to MCP server: {self.name}")
        except Exception as e:
            logger.error(f"Error connecting to MCP server {self.name}: {e}")
            await self.cleanup()
            raise

    async def cleanup(self):
        """Clean up MCP client resources."""
        try:
            await self.exit_stack.aclose()
        except (RuntimeError, asyncio.CancelledError) as e:
            # Suppress errors related to cancel scope exit and cancellation during shutdown
            logger.debug(f"Suppressed cleanup error for {self.name}: {type(e).__name__}: {e}")
        except Exception as e:
            # Log unexpected errors but don't crash
            logger.warning(
                f"Unexpected error during cleanup for {self.name}: {type(e).__name__}: {e}"
            )

    async def get_tools(self) -> List[Dict[str, Any]]:
        if not self.session:
            return []
        tools_result = await self.session.list_tools()
        return [
            {
                "name": f"{self.name}__{t.name}",
                "description": t.description,
                "input_schema": t.inputSchema,
            }
            for t in tools_result.tools
        ]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if not self.session:
            return "Error: Session not connected"

        # Remove prefix
        actual_tool_name = tool_name.split("__")[-1]
        result = await self.session.call_tool(actual_tool_name, arguments)
        return str(result.content)
