import asyncio

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from light_agent.agent.loop import AgentLoop
from light_agent.agent.mcp_client import MCPClient
from light_agent.agent.memory import MemoryStore
from light_agent.agent.skills import SkillsLoader
from light_agent.agent.subagent import SubagentManager
from light_agent.session.manager import SessionManager
from light_agent.agent.tools import (
    ExecTool,
    ListDirTool,
    ReadFileTool,
    SpawnTool,
    ToolRegistry,
    WebFetchTool,
    WebSearchTool,
    WriteFileTool,
)
from light_agent.agent.tools.native import NativeTool
from light_agent.config.settings import settings
from light_agent.providers.litellm_provider import LiteLLMProvider

app = typer.Typer(name="lightagent", help="Lightweight SRE AI Agent", no_args_is_help=True)
console = Console()


async def main_loop(prompt: str, verbose: bool = False):
    # Configure logging based on verbose flag
    if not verbose:
        logger.remove()  # Remove default handler
        logger.add(lambda msg: None, level="WARNING")  # Only show warnings and errors
    
    # Setup
    model = settings.DEFAULT_MODEL
    api_key = None
    base_url = None

    if "gemini" in model:
        api_key = settings.GOOGLE_API_KEY
    elif model.startswith("ollama/"):
        base_url = settings.OLLAMA_BASE_URL
    elif settings.LLMSTUDY_BASE_URL:
        # If LLMSTUDY is configured, use it
        api_key = settings.LLMSTUDY_API_KEY
        base_url = settings.LLMSTUDY_BASE_URL
        if not model.startswith("openai/"):
            # Ensure it has the openai/ prefix for custom endpoints
            model = f"openai/{model}"
    
    provider = LiteLLMProvider(
        model=model,
        api_key=api_key,
        base_url=base_url,
    )

    memory = MemoryStore(settings.WORKSPACE_DIR)
    skills = SkillsLoader(settings.WORKSPACE_DIR)

    tools = ToolRegistry()
    tools.skills_loader = skills

    # Initialize MCP
    mcp_config = settings.mcp_servers
    for name, config in mcp_config.items():
        if isinstance(config, str):
            command = config
        else:
            # Handle full MCP server config format
            cmd = config.get("command")
            args = config.get("args", [])
            mcp = MCPClient(name, cmd, args, suppress_output=not verbose)
        await mcp.connect()
        tools.mcp_clients.append(mcp)

    session_manager = SessionManager(settings.WORKSPACE_DIR)
    subagent_manager = SubagentManager(provider, settings.WORKSPACE_DIR, session_manager)

    # Register Native Tools
    tools.register(ExecTool())
    tools.register(ListDirTool())
    tools.register(ReadFileTool())
    tools.register(WriteFileTool())
    tools.register(WebSearchTool())
    tools.register(WebFetchTool())
    tools.register(SpawnTool(manager=subagent_manager))

    # Add fake native tool for testing
    async def get_system_load():
        return "System load: 0.15, 0.20, 0.22"

    system_load_tool = NativeTool(
        name="get_system_load",
        func=get_system_load,
        description="Returns current system load",
        parameters={"type": "object", "properties": {}},
    )
    tools.register(system_load_tool)

    try:
        agent = AgentLoop(provider, memory, tools)

        if verbose:
            console.print(
                Panel(f"[bold blue]Light Agent Initialized[/]\nWorkspace: {settings.WORKSPACE_DIR}")
            )

        result = await agent.run(prompt)
        if verbose:
            console.print(f"\n[bold green]Final Answer:[/]\n{result}")
        else:
            console.print(f"[bold cyan]lightagent:[/] {result}")

    finally:
        # Cleanup MCP clients
        for mcp in tools.mcp_clients:
            await mcp.cleanup()


@app.command()
def chat(
    prompt: str = typer.Argument(..., help="User prompt"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logs"),
):
    """Chat with the agent."""
    asyncio.run(main_loop(prompt, verbose))


@app.command()
def version():
    """Show version."""
    console.print("Light Agent v0.1.0")


if __name__ == "__main__":
    app()
