"""Context classes for structured agent execution."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from light_agent.agent.short_memory import ShortTermMemory
    from light_agent.agent.tools.registry import ToolRegistry
    from light_agent.agent.tools.memory_tool import LongMemoryTool
    from light_agent.providers.base import LLMProvider


@dataclass
class AgentContext:
    """Immutable context object for agent execution.

    Contains all state needed for a single agent run including:
    - Workspace and configuration
    - Provider and model information
    - Memory systems
    - Tool registry reference
    - Execution metadata

    Usage:
        context = AgentContext(
            workspace=Path("./workspace"),
            provider=my_provider,
            model="ollama/llama3"
        )
        agent = AgentLoop(context=context)
    """

    workspace: Path
    provider: "LLMProvider"
    model: str
    tools: Optional["ToolRegistry"] = None
    long_memory: Optional["LongMemoryTool"] = None
    short_memory: Optional["ShortTermMemory"] = None
    session_id: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_model(self, model: str) -> "AgentContext":
        """Create new context with different model.

        Args:
            model: New model to use.

        Returns:
            New AgentContext instance.
        """
        return AgentContext(
            workspace=self.workspace,
            provider=self.provider,
            model=model,
            tools=self.tools,
            long_memory=self.long_memory,
            short_memory=self.short_memory,
            session_id=self.session_id,
            metadata=self.metadata,
        )


@dataclass
class ExecutionContext:
    """Runtime context for a single execution iteration.

    Tracks the state during agent execution including:
    - Current iteration number
    - Message history
    - Tool calls made
    - Timing information
    """

    iteration: int = 0
    max_iterations: int = 10
    messages: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls_made: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    reasoning_content: Optional[str] = None

    @property
    def is_complete(self) -> bool:
        """Check if execution is complete."""
        return not self.tool_calls_made or self.iteration >= self.max_iterations

    def next_iteration(self) -> "ExecutionContext":
        """Move to next iteration.

        Returns:
            New ExecutionContext with incremented iteration.
        """
        return ExecutionContext(
            iteration=self.iteration + 1,
            max_iterations=self.max_iterations,
            messages=self.messages,
            tool_calls_made=self.tool_calls_made,
            start_time=self.start_time,
            reasoning_content=self.reasoning_content,
        )

    def with_reasoning(self, reasoning: str) -> "ExecutionContext":
        """Create new context with reasoning content.

        Args:
            reasoning: Reasoning content from model.

        Returns:
            New ExecutionContext with reasoning.
        """
        return ExecutionContext(
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            messages=self.messages,
            tool_calls_made=self.tool_calls_made,
            start_time=self.start_time,
            reasoning_content=reasoning,
        )
