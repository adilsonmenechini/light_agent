"""Agent builder for structured AgentLoop creation."""

from pathlib import Path
from typing import Any, Dict, Optional

from lightagent.agent.loop import AgentLoop
from lightagent.agent.mcp_client import MCPClient
from lightagent.agent.memory import MemoryStore
from lightagent.agent.short_memory import ShortTermMemory
from lightagent.agent.skills import SkillsLoader
from lightagent.agent.subagent import ExecToolConfig, SubagentManager
from lightagent.agent.tools import ToolRegistry
from lightagent.agent.tools.memory_tool import LongMemoryTool
from lightagent.config.settings import settings
from lightagent.providers.base import LLMProvider
from lightagent.providers.litellm_provider import LiteLLMProvider
from lightagent.session.manager import SessionManager


class AgentBuilder:
    """Builder pattern for creating AgentLoop instances.

    Provides a fluent interface for configuring and creating
    agent instances with dependency injection.

    Usage:
        agent = AgentBuilder()
            .with_provider(model="ollama/llama3")
            .with_tools([ReadFileTool(), WriteFileTool()])
            .with_memory(long_term=True, short_term=True)
            .with_mcp_servers({"fetch": "npx @modelcontextprotocol/server-fetch"})
            .build()
    """

    def __init__(self) -> None:
        self._provider: Optional[LLMProvider] = None
        self._tools: ToolRegistry = ToolRegistry()
        self._memory: Optional[MemoryStore] = None
        self._long_memory: Optional[LongMemoryTool] = None
        self._short_memory: Optional[ShortTermMemory] = None
        self._session_manager: Optional[SessionManager] = None
        self._subagent_manager: Optional[SubagentManager] = None
        self._skills_loader: Optional[SkillsLoader] = None
        self._mcp_configs: Dict[str, Any] = {}
        self._verbose: bool = False
        self._restrict_workspace: bool = settings.RESTRICT_TO_WORKSPACE
        self._workspace_dir: Path = settings.WORKSPACE_DIR

    def with_provider(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> "AgentBuilder":
        """Set the LLM provider.

        Args:
            model: Model to use (uses settings defaults if not provided).
            api_key: API key for the provider.
            base_url: Base URL for the provider.

        Returns:
            Self for method chaining.
        """
        # Determine model from settings
        if model is None:
            if settings.REASONING_MODEL:
                model = settings.REASONING_MODEL
            elif settings.FAST_MODEL:
                model = settings.FAST_MODEL
            else:
                model = settings.DEFAULT_MODEL

        # Determine API key and base URL based on model
        actual_api_key = api_key
        actual_base_url = base_url

        if "gemini" in (model or ""):
            actual_api_key = settings.GOOGLE_API_KEY
        elif model and model.startswith("ollama/"):
            actual_base_url = settings.OLLAMA_BASE_URL
        elif settings.LLMSTUDY_BASE_URL:
            actual_api_key = settings.LLMSTUDY_API_KEY
            actual_base_url = settings.LLMSTUDY_BASE_URL
            if model and not model.startswith("openai/"):
                model = f"openai/{model}"

        self._provider = LiteLLMProvider(
            model=model or settings.DEFAULT_MODEL,
            api_key=actual_api_key,
            base_url=actual_base_url,
        )
        return self

    def with_workspace(self, workspace_dir: Path) -> "AgentBuilder":
        """Set the workspace directory.

        Args:
            workspace_dir: Path to the workspace directory.

        Returns:
            Self for method chaining.
        """
        self._workspace_dir = workspace_dir
        return self

    def with_tools(self, tools: list[Any]) -> "AgentBuilder":
        """Register tools with the registry.

        Args:
            tools: List of tool instances to register.

        Returns:
            Self for method chaining.
        """
        for tool in tools:
            self._tools.register(tool)
        return self

    def with_memory(
        self,
        long_term: bool = True,
        short_term: bool = True,
        max_messages: int = 10,
        max_observations: int = 20,
    ) -> "AgentBuilder":
        """Configure memory systems.

        Args:
            long_term: Whether to enable long-term memory.
            short_term: Whether to enable short-term memory.
            max_messages: Maximum messages in short-term memory window.
            max_observations: Maximum observations in short-term memory.

        Returns:
            Self for method chaining.
        """
        if long_term:
            self._long_memory = LongMemoryTool(self._workspace_dir)

        if short_term:
            self._short_memory = ShortTermMemory(
                max_messages=max_messages,
                max_observations=max_observations,
            )

        self._memory = MemoryStore(self._workspace_dir)
        return self

    def with_skills(self) -> "AgentBuilder":
        """Enable markdown skills loading.

        Returns:
            Self for method chaining.
        """
        self._skills_loader = SkillsLoader(self._workspace_dir)
        self._tools.skills_loader = self._skills_loader
        return self

    def with_mcp_servers(self, servers: Dict[str, Any]) -> "AgentBuilder":
        """Configure MCP servers.

        Args:
            servers: Dict mapping server names to configurations.
                     Can be {"name": "command"} or
                     {"name": {"command": "...", "args": [...]}}

        Returns:
            Self for method chaining.
        """
        self._mcp_configs = servers
        return self

    def with_subagents(
        self,
        timeout: int = 60,
        restrict_to_workspace: Optional[bool] = None,
    ) -> "AgentBuilder":
        """Configure subagent support.

        Args:
            timeout: Timeout for subagent executions in seconds.
            restrict_to_workspace: Whether to restrict subagents to workspace.

        Returns:
            Self for method chaining.
        """
        # Provider will be set if not provided, store config for later
        self._session_manager = SessionManager(self._workspace_dir)
        exec_config = ExecToolConfig(
            timeout=timeout,
            restrict_to_workspace=restrict_to_workspace or self._restrict_workspace,
        )

        # Store config, will create SubagentManager in build()
        if not hasattr(self, "_subagent_exec_config"):
            self._subagent_exec_config = exec_config

        return self

    def with_verbose(self, verbose: bool = True) -> "AgentBuilder":
        """Set verbose mode for logging.

        Args:
            verbose: Whether to enable verbose logging.

        Returns:
            Self for method chaining.
        """
        self._verbose = verbose
        return self

    def _configure_logging(self) -> None:
        """Configure logging based on verbose setting."""
        from loguru import logger

        if not self._verbose:
            logger.remove()
            logger.add(lambda msg: None, level="WARNING")

    async def _setup_mcp_clients(self) -> None:
        """Connect to configured MCP servers."""
        for name, config in self._mcp_configs.items():
            if isinstance(config, str):
                command = config
                mcp = MCPClient(name, command, [], suppress_output=not self._verbose)
            else:
                cmd = config.get("command")
                args = config.get("args", [])
                mcp = MCPClient(name, cmd, args, suppress_output=not self._verbose)
            await mcp.connect()
            self._tools.mcp_clients.append(mcp)

    def build(self) -> AgentLoop:
        """Build the configured AgentLoop instance.

        Returns:
            Configured AgentLoop ready for execution.

        Raises:
            ValueError: If provider is not configured.
        """
        if self._provider is None:
            self.with_provider()

        # At this point, self._provider should be set
        provider = self._provider
        assert provider is not None, "Provider should be set after with_provider()"

        # Initialize defaults if not set
        if self._memory is None:
            self._memory = MemoryStore(self._workspace_dir)

        if self._short_memory is None:
            self._short_memory = ShortTermMemory()

        if self._session_manager is None:
            self._session_manager = SessionManager(self._workspace_dir)

        if self._subagent_manager is None:
            # Use exec_config from with_subagents or create default
            exec_config = getattr(self, "_subagent_exec_config", None) or ExecToolConfig(
                restrict_to_workspace=self._restrict_workspace
            )
            self._subagent_manager = SubagentManager(
                provider=provider,
                workspace=self._workspace_dir,
                session_manager=self._session_manager,
                exec_config=exec_config,
            )

        self._configure_logging()

        return AgentLoop(
            provider=provider,
            memory=self._memory,
            tools=self._tools,
            long_memory=self._long_memory,
            short_memory=self._short_memory,
        )

        self._configure_logging()

        return AgentLoop(
            provider=self._provider,
            memory=self._memory,
            tools=self._tools,
            long_memory=self._long_memory,
            short_memory=self._short_memory,
        )

    @staticmethod
    def create_default() -> AgentLoop:
        """Create agent with default configuration.

        Useful for quick setup with all standard tools.

        Returns:
            Fully configured AgentLoop with common tools.
        """
        from lightagent.agent.tools.filesystem import (
            ListDirTool,
            ReadFileTool,
            WriteFileTool,
        )
        from lightagent.agent.tools.gh_api_tool import GitHubTool
        from lightagent.agent.tools.git_tool import GitTool
        from lightagent.agent.tools.github_check import GitHubCheckTool
        from lightagent.agent.tools.github_public import GitHubPublicTool
        from lightagent.agent.tools.github_workflow_tool import GitHubWorkflowTool
        from lightagent.agent.tools.shell import ExecTool
        from lightagent.agent.tools.web import WebFetchTool, WebSearchTool

        builder = (
            AgentBuilder()
            .with_provider()
            .with_workspace(settings.WORKSPACE_DIR)
            .with_memory(long_term=True, short_term=True)
            .with_skills()
            .with_mcp_servers(settings.mcp_servers)
            .with_tools(
                [
                    ExecTool(
                        working_dir=str(settings.WORKSPACE_DIR),
                        restrict_to_workspace=settings.RESTRICT_TO_WORKSPACE,
                        workspace=settings.WORKSPACE_DIR,
                    ),
                    ListDirTool(
                        workspace=settings.WORKSPACE_DIR,
                        restrict_to_workspace=settings.RESTRICT_TO_WORKSPACE,
                    ),
                    ReadFileTool(
                        workspace=settings.WORKSPACE_DIR,
                        restrict_to_workspace=settings.RESTRICT_TO_WORKSPACE,
                    ),
                    WriteFileTool(
                        workspace=settings.WORKSPACE_DIR,
                        restrict_to_workspace=settings.RESTRICT_TO_WORKSPACE,
                    ),
                    WebSearchTool(),
                    WebFetchTool(),
                    GitTool(),
                    GitHubTool(),
                    GitHubPublicTool(),
                    GitHubCheckTool(),
                    GitHubWorkflowTool(),
                ]
            )
        )

        # Build to get subagent manager, then add subagent tools
        agent = builder.build()

        return agent
