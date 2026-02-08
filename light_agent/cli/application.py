"""Object-oriented CLI application for Light Agent."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from light_agent.agent.loop import AgentLoop
from light_agent.agent.mcp_client import MCPClient
from light_agent.agent.memory import MemoryStore
from light_agent.agent.short_memory import ShortTermMemory
from light_agent.agent.skills import SkillsLoader
from light_agent.agent.subagent import SubagentManager
from light_agent.agent.tools import (
    ExecTool,
    GitHubCheckTool,
    GitHubPublicTool,
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
from light_agent.agent.tools.approval import ApprovalStore, HumanApprovalTool
from light_agent.config.settings import settings
from light_agent.core import event_bus
from light_agent.core.console_subscriber import setup_console_subscriber
from light_agent.providers.litellm_provider import LiteLLMProvider
from light_agent.session.manager import SessionManager


class CLIApplication:
    """Object-oriented CLI application for Light Agent."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize CLI application.

        Args:
            verbose: Enable verbose logging.
        """
        self._verbose = verbose
        self._agent: Optional[AgentLoop] = None
        self._tools: Optional[ToolRegistry] = None
        self._approval_store: Optional[ApprovalStore] = None
        self._console = Console()

    @property
    def agent(self) -> AgentLoop:
        """Get the current agent instance."""
        if self._agent is None:
            msg = "Agent not initialized. Call initialize() first."
            raise RuntimeError(msg)
        return self._agent

    @property
    def tools(self) -> ToolRegistry:
        """Get the current tools registry."""
        if self._tools is None:
            msg = "Tools not initialized. Call initialize() first."
            raise RuntimeError(msg)
        return self._tools

    def _configure_logging(self) -> None:
        """Configure logging based on verbose setting."""
        if not self._verbose:
            logger.remove()
            logger.add(lambda msg: None, level="WARNING")

    def _get_model(self) -> str:
        """Get the model to use based on settings.

        Returns:
            Model string for LLM provider.
        """
        if settings.REASONING_MODEL:
            return settings.REASONING_MODEL
        if settings.FAST_MODEL:
            return settings.FAST_MODEL
        return settings.DEFAULT_MODEL

    def _get_provider_config(self, model: str) -> tuple[Optional[str], Optional[str]]:
        """Get API key and base URL for the model.

        Args:
            model: Model string.

        Returns:
            Tuple of (api_key, base_url).
        """
        api_key = None
        base_url = None

        if "gemini" in model:
            api_key = settings.GOOGLE_API_KEY
        elif model.startswith("ollama/"):
            base_url = settings.OLLAMA_BASE_URL
        elif settings.LLMSTUDY_BASE_URL:
            api_key = settings.LLMSTUDY_API_KEY
            base_url = settings.LLMSTUDY_BASE_URL
            if not model.startswith("openai/"):
                model = f"openai/{model}"

        return api_key, base_url

    async def initialize(self) -> None:
        """Initialize agent and tools."""
        self._configure_logging()

        model = self._get_model()
        api_key, base_url = self._get_provider_config(model)

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
                mcp = MCPClient(name, command, [], suppress_output=not self._verbose)
            else:
                cmd = config.get("command")
                args = config.get("args", [])
                mcp = MCPClient(name, cmd, args, suppress_output=not self._verbose)
            await mcp.connect()
            tools.mcp_clients.append(mcp)

        session_manager = SessionManager(settings.WORKSPACE_DIR)
        subagent_manager = SubagentManager(
            provider=provider,
            workspace=settings.WORKSPACE_DIR,
            session_manager=session_manager,
        )

        # Register tools
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
        tools.register(GitHubPublicTool())
        tools.register(GitHubCheckTool())
        tools.register(GitHubWorkflowTool())

        # Subagent tools
        tools.register(SpawnTool(manager=subagent_manager))
        tools.register(ParallelSpawnTool(manager=subagent_manager))
        tools.register(WaitSubagentsTool(manager=subagent_manager))

        # Long memory
        long_memory = LongMemoryTool(settings.WORKSPACE_DIR)
        tools.register(long_memory)

        # Approval tool
        approval_store = ApprovalStore(storage_dir="data/approvals")
        approval_tool = HumanApprovalTool(store=approval_store)
        tools.register(approval_tool)

        # Test native tool
        async def get_system_load() -> str:
            return "System load: 0.15, 0.20, 0.22"

        system_load_tool = NativeTool(
            name="get_system_load",
            func=get_system_load,
            description="Returns current system load",
            parameters={"type": "object", "properties": {}},
        )
        tools.register(system_load_tool)

        agent = AgentLoop(
            provider=provider,
            memory=memory,
            tools=tools,
            long_memory=long_memory,
            short_memory=ShortTermMemory(),
        )

        self._agent = agent
        self._tools = tools
        self._approval_store = approval_store

        setup_console_subscriber(event_bus)

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._tools and hasattr(self._tools, "mcp_clients"):
            for mcp in self._tools.mcp_clients:
                await mcp.cleanup()

    async def run_chat(self, prompt: str) -> str:
        """Run a single chat prompt.

        Args:
            prompt: The user prompt to process.

        Returns:
            The agent's response.
        """
        if self._agent is None:
            await self.initialize()

        assert self._agent is not None
        assert self._tools is not None

        try:
            result = await self._agent.run(prompt)
            return result
        finally:
            await self.cleanup()

    async def run_interactive(self) -> None:
        """Run an interactive chat session."""
        if self._agent is None:
            await self.initialize()

        assert self._agent is not None
        assert self._tools is not None
        assert self._approval_store is not None

        self._console.print(
            Panel(
                "[bold cyan]Light Agent Interactive Mode[/]\n"
                "Type [bold red]/exit[/] or [bold red]/quit[/] to leave. "
                "Type [bold yellow]/status[/] for health check. "
                "Type [bold yellow]/approvals[/] to list pending approvals."
            )
        )

        try:
            while True:
                try:
                    user_input = self._console.input("\n[bold green]user> [/]").strip()
                except EOFError:
                    break

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                    continue

                result = await self._agent.run(user_input)
                if self._verbose:
                    self._console.print(f"\n[bold green]Final Answer:[/]\n{result}")
                else:
                    self._console.print(f"[bold cyan]lightagent:[/] {result}")

        finally:
            await self.cleanup()

    async def _handle_command(self, command: str) -> None:
        """Handle a slash command.

        Args:
            command: The command string to process.
        """
        assert self._agent is not None
        assert self._tools is not None
        assert self._approval_store is not None

        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()

        if cmd in ["/exit", "/quit"]:
            self._console.print("[yellow]Exiting...[/]")
            raise SystemExit(0)

        if cmd == "/new":
            self._agent.clear_messages()
            self._console.print("[bold green]Conversation cleared. Starting fresh...[/]")

        elif cmd == "/status":
            await self._show_status()

        elif cmd == "/reset":
            self._console.print("[yellow]Resetting tools and MCP clients...[/]")
            for mcp in self._tools.mcp_clients:
                await mcp.cleanup()
            await self.initialize()
            self._console.print("[bold green]Reset complete![/]")

        elif cmd == "/approvals":
            pending = await self._approval_store.list_pending()
            if not pending:
                self._console.print("[bold green]No pending approvals.[/]")
            else:
                self._console.print(f"[bold blue]Pending Approvals ({len(pending)}):[/]")
                for req in pending:
                    self._console.print(
                        f"  - [bold yellow]{req['request_id']}[/]: {req['question']} "
                        f"(Urgency: {req['urgency']})"
                    )
                    if req.get("context"):
                        self._console.print(f"    Context: {req['context'][:100]}...")

        elif cmd == "/approve":
            if len(cmd_parts) < 2:
                self._console.print("[bold red]Usage: /approve <request_id> <yes|no|response>[/]")
                return

            request_id = cmd_parts[1]
            response = cmd_parts[2] if len(cmd_parts) > 2 else "yes"
            approved = response.lower() in ("yes", "y", "true", "1")
            success = await self._approval_store.record_response(
                request_id, response, approved, user="cli"
            )
            if success:
                self._console.print(f"[bold green]Approval recorded for {request_id}[/]")
            else:
                self._console.print(f"[bold red]Request {request_id} not found[/]")

        else:
            self._console.print(f"[bold red]Unknown command:[/] {cmd}")

    async def _show_status(self) -> None:
        """Show current system status."""
        mcp_count = len(self._tools.mcp_clients)

        if self._tools.skills_loader is None:
            self._console.print(
                f"[bold blue]Status:[/]\n- MCP Clients: {mcp_count}\n- Skills Loaded: 0"
            )
            for mcp in self._tools.mcp_clients:
                self._console.print(f"  - [green]✓[/] (MCP) {mcp.name}")
            return

        skills = self._tools.skills_loader.list_skills()
        skill_count = len(skills)

        self._console.print(
            f"[bold blue]Status:[/]\n- MCP Clients: {mcp_count}\n- Skills Loaded: {skill_count}"
        )

        for mcp in self._tools.mcp_clients:
            self._console.print(f"  - [green]✓[/] (MCP) {mcp.name}")

        for s in skills:
            self._console.print(f"  - [green]✓[/] (Skill) {s['name']}")


# Typer app instance
app = typer.Typer(name="lightagent", help="Lightweight SRE AI Agent", no_args_is_help=True)
_console = Console()


@app.command()
def chat(
    prompt: str = typer.Argument(None, help="User prompt (leave empty for interactive chat)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logs"),
):
    """Chat with the agent."""
    cli = CLIApplication(verbose=verbose)

    if prompt:
        result = asyncio.run(cli.run_chat(prompt))
        _console.print(f"[bold cyan]lightagent:[/] {result}")
    else:
        asyncio.run(cli.run_interactive())


@app.command()
def version():
    """Show version."""
    _console.print("Light Agent v0.1.0")


@app.command()
def approvals(
    list_all: bool = typer.Option(False, "--all", "-a", help="List all including responded"),
):
    """List pending approval requests."""
    from light_agent.agent.tools.approval import ApprovalStore

    store = ApprovalStore(storage_dir="data/approvals")
    pending = asyncio.run(store.list_pending())

    if not pending:
        _console.print("[bold green]No pending approvals.[/]")
    else:
        _console.print(f"[bold blue]Pending Approvals ({len(pending)}):[/]")
        for req in pending:
            _console.print(
                f"  - [bold yellow]{req['request_id']}[/]: {req['question']} "
                f"(Urgency: {req['urgency']})"
            )
            if req.get("context"):
                _console.print(f"    Context: {req['context'][:100]}...")


@app.command()
def approve(
    request_id: str = typer.Argument(..., help="Request ID to approve"),
    response: str = typer.Argument(..., help="Response (yes/no or custom)"),
    approved: bool = typer.Option(True, "--approve/--deny", help="Whether approved"),
):
    """Record an approval response."""
    from light_agent.agent.tools.approval import ApprovalStore

    store = ApprovalStore(storage_dir="data/approvals")
    is_approved = approved if not response else response.lower() in ("yes", "y", "true", "1")
    success = asyncio.run(
        store.record_response(request_id, response or "yes", is_approved, user="cli")
    )

    if success:
        _console.print(f"[bold green]Approval recorded for {request_id}[/]")
    else:
        _console.print(f"[bold red]Request {request_id} not found[/]")


if __name__ == "__main__":
    app()
