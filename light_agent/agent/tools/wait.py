"""Wait tool for subagents."""

import json
from typing import TYPE_CHECKING, Any, List, Optional

from light_agent.agent.tools.base import Tool

if TYPE_CHECKING:
    from light_agent.agent.subagent import SubagentManager


class WaitSubagentsTool(Tool):
    """
    Tool to wait for specific or all subagents to complete.
    """

    def __init__(self, manager: "SubagentManager"):
        self._manager = manager

    @property
    def name(self) -> str:
        return "wait_subagents"

    @property
    def description(self) -> str:
        return (
            "Wait for specified subagents (by task_id) or all currently running subagents to complete. "
            "Returns the results of the subagents."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of task IDs to wait for. If omitted, waits for all.",
                },
            },
        }

    async def execute(self, task_ids: Optional[List[str]] = None, **kwargs: Any) -> str:
        """Wait for subagents and return results."""
        wait_result = await self._manager.wait_for(task_ids)
        
        output = [wait_result["summary"], ""]
        for res in wait_result["results"]:
            status_text = "OK" if res.get("status") == "ok" else "FAILED"
            output.append(f"--- Subagent {res.get('task_id')} ({res.get('label')}) [{status_text}] ---")
            output.append(f"Task: {res.get('task')}")
            output.append(f"Result:\n{res.get('result')}")
            output.append("-" * 40)
            
        return "\n".join(output)
