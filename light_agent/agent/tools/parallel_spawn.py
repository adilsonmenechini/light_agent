"""Parallel spawn tool for creating multiple background subagents."""

from typing import TYPE_CHECKING, Any, List

from light_agent.agent.tools.base import Tool

if TYPE_CHECKING:
    from light_agent.agent.subagent import SubagentManager


class ParallelSpawnTool(Tool):
    """
    Tool to spawn multiple subagents for background task execution in parallel.
    """

    def __init__(self, manager: "SubagentManager"):
        self._manager = manager
        self._origin_channel = "cli"
        self._origin_chat_id = "direct"

    def set_context(self, channel: str, chat_id: str) -> None:
        """Set the origin context for subagent announcements."""
        self._origin_channel = channel
        self._origin_chat_id = chat_id

    @property
    def name(self) -> str:
        return "parallel_spawn"

    @property
    def description(self) -> str:
        return (
            "Spawn multiple subagents to handle tasks in the background concurrently. "
            "Use this when you have several independent subtasks. "
            "Returns a list of status messages with task IDs."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string", "description": "The task for the subagent"},
                            "label": {"type": "string", "description": "Optional label for the task"},
                        },
                        "required": ["task"],
                    },
                    "description": "List of tasks to spawn",
                },
            },
            "required": ["tasks"],
        }

    async def execute(self, tasks: List[dict[str, Any]], **kwargs: Any) -> str:
        """Spawn multiple subagents."""
        results = []
        for task_info in tasks:
            task = task_info["task"]
            label = task_info.get("label")
            status = await self._manager.spawn(
                task=task,
                label=label,
                origin_channel=self._origin_channel,
                origin_chat_id=self._origin_chat_id,
            )
            results.append(status)
        
        return "\n".join(results)
