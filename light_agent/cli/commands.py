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
from light_agent.agent.tools import (
    ExecTool,
    GitHubTool,
    GitHubWorkflowTool,
    GitTool,
    ListDirTool,
    ParallelSpawnTool,
    ReadFileTool,
    SpawnTool,
    ToolRegistry,
    WaitSubagentsTool,
    WebFetchTool,
    WebSearchTool,
    WriteFileTool,
)
from light_agent.agent.tools.memory_tool import LongMemoryTool
from light_agent.agent.tools.native import NativeTool
from light_agent.config.settings import settings
from light_agent.providers.litellm_provider import LiteLLMProvider
from light_agent.session.manager import SessionManager

app = typer.Typer(name="lightagent", help="Lightweight SRE AI Agent", no_args_is_help=True)
console = Console()


async def setup_agent(verbose: bool = False):
    """Common setup for AgentLoop and its dependencies."""
    # Configure logging based on verbose flag
    if not verbose:
        logger.remove()  # Remove default handler
        logger.add(lambda msg: None, level="WARNING")  # Only show warnings and errors

    # Setup - prioritize REASONING_MODEL > FAST_MODEL > DEFAULT_MODEL
    if settings.REASONING_MODEL:
        model = settings.REASONING_MODEL
    elif settings.FAST_MODEL:
        model = settings.FAST_MODEL
    else:
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
            mcp = MCPClient(name, command, [], suppress_output=not verbose)
        else:
            # Handle full MCP server config format
            cmd = config.get("command")
            args = config.get("args", [])
            mcp = MCPClient(name, cmd, args, suppress_output=not verbose)
        await mcp.connect()
        tools.mcp_clients.append(mcp)

    session_manager = SessionManager(settings.WORKSPACE_DIR)
    long_memory = LongMemoryTool(settings.WORKSPACE_DIR)
    subagent_manager = SubagentManager(provider, settings.WORKSPACE_DIR, session_manager)

    # Register Native Tools
    tools.register(
        ExecTool(
            working_dir=str(settings.WORKSPACE_DIR),
            restrict_to_workspace=settings.RESTRICT_TO_WORKSPACE,
            workspace=settings.WORKSPACE_DIR,
        )
    )
    tools.register(
        ListDirTool(
            workspace=settings.WORKSPACE_DIR,
            restrict_to_workspace=settings.RESTRICT_TO_WORKSPACE,
        )
    )
    tools.register(
        ReadFileTool(
            workspace=settings.WORKSPACE_DIR,
            restrict_to_workspace=settings.RESTRICT_TO_WORKSPACE,
        )
    )
    tools.register(
        WriteFileTool(
            workspace=settings.WORKSPACE_DIR,
            restrict_to_workspace=settings.RESTRICT_TO_WORKSPACE,
        )
    )
    tools.register(WebSearchTool())
    tools.register(WebFetchTool())
    tools.register(GitTool())
    tools.register(GitHubTool())
    tools.register(GitHubWorkflowTool())
    tools.register(SpawnTool(manager=subagent_manager))
    tools.register(ParallelSpawnTool(manager=subagent_manager))
    tools.register(WaitSubagentsTool(manager=subagent_manager))
    tools.register(long_memory)  # Register LongMemoryTool

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

    agent = AgentLoop(provider, memory, tools, long_memory=long_memory)
    return agent, tools


async def interactive_loop(verbose: bool = False):
    """Run a persistent interactive chat session."""
    agent, tools = await setup_agent(verbose)

    console.print(
        Panel(
            "[bold cyan]Light Agent Interactive Mode[/]\nType [bold red]/exit[/] or [bold red]/quit[/] to leave. Type [bold yellow]/status[/] for health check."
        )
    )

    try:
        while True:
            # Get user input
            try:
                user_input = console.input("\n[bold green]user> [/]").strip()
            except EOFError:
                break

            if not user_input:
                continue

            # Handle Slash Commands
            if user_input.startswith("/"):
                cmd_parts = user_input.split()
                cmd = cmd_parts[0].lower()

                if cmd in ["/exit", "/quit"]:
                    console.print("[yellow]Exiting...[/]")
                    break

                elif cmd == "/new":
                    agent.clear_messages()
                    console.print("[bold green]Conversation cleared. Starting fresh...[/]")
                    continue

                elif cmd == "/status":
                    mcp_count = len(tools.mcp_clients)
                    if tools.skills_loader is None:
                        console.print(
                            "[bold blue]Status:[/]\n- MCP Clients: {mcp_count}\n- Skills Loaded: 0"
                        )
                        for mcp in tools.mcp_clients:
                            console.print(f"  - [green]✓[/] (MCP) {mcp.name}")
                        continue
                    skills = tools.skills_loader.list_skills()
                    skill_count = len(skills)
                    console.print(
                        f"[bold blue]Status:[/]\n- MCP Clients: {mcp_count}\n- Skills Loaded: {skill_count}"
                    )
                    for mcp in tools.mcp_clients:
                        console.print(f"  - [green]✓[/] (MCP) {mcp.name}")
                    for s in skills:
                        console.print(f"  - [green]✓[/] (Skill) {s['name']}")
                    continue

                elif cmd == "/reset":
                    console.print("[yellow]Resetting tools and MCP clients...[/]")
                    # Cleanup current
                    for mcp in tools.mcp_clients:
                        await mcp.cleanup()
                    # Re-setup
                    agent, tools = await setup_agent(verbose)
                    console.print("[bold green]Reset complete![/]")
                    continue

                else:
                    console.print(f"[bold red]Unknown command:[/] {cmd}")
                    continue

            # Run regular agent loop
            result = await agent.run(user_input)
            if verbose:
                console.print(f"\n[bold green]Final Answer:[/]\n{result}")
            else:
                console.print(f"[bold cyan]lightagent:[/] {result}")

    finally:
        # Cleanup MCP clients
        for mcp in tools.mcp_clients:
            await mcp.cleanup()


async def main_loop(prompt: str, verbose: bool = False):
    agent, tools = await setup_agent(verbose)

    try:
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
    prompt: str = typer.Argument(None, help="User prompt (leave empty for interactive chat)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logs"),
):
    """Chat with the agent."""
    if prompt:
        asyncio.run(main_loop(prompt, verbose))
    else:
        asyncio.run(interactive_loop(verbose))


@app.command()
def version():
    """Show version."""
    console.print("Light Agent v0.1.0")


if __name__ == "__main__":
    app()
