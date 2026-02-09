"""Subagent manager for background task execution."""

import asyncio
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from lightagent.agent.tools.filesystem import ListDirTool, ReadFileTool, WriteFileTool
from lightagent.agent.tools.registry import ToolRegistry
from lightagent.agent.tools.shell import ExecTool
from lightagent.agent.tools.web import WebFetchTool, WebSearchTool
from lightagent.config.settings import settings
from lightagent.providers.base import LLMProvider
from lightagent.session.manager import SessionManager


@dataclass
class ExecToolConfig:
    timeout: int = 60
    restrict_to_workspace: bool = False


class SubagentManager:
    """
    Manages background subagent execution.

    Subagents are lightweight agent instances that run in the background
    to handle specific tasks. They share the same LLM provider but have
    isolated context and a focused system prompt.
    """

    def __init__(
        self,
        provider: LLMProvider,
        workspace: Path,
        session_manager: SessionManager,
        model: str | None = None,
        exec_config: "ExecToolConfig | None" = None,
    ):
        self.provider = provider
        self.workspace = workspace
        self.session_manager = session_manager
        self.model = model or settings.REASONING_MODEL or provider.get_default_model()
        self.exec_config = exec_config or ExecToolConfig()
        self._running_tasks: dict[str, asyncio.Task[str]] = {}
        self._results: dict[str, dict[str, Any]] = {}

    async def spawn(
        self,
        task: str,
        label: str | None = None,
        model: str | None = None,
        origin_channel: str = "cli",
        origin_chat_id: str = "direct",
    ) -> str:
        """
        Spawn a subagent to execute a task in the background.

        Args:
            task: The task description for the subagent.
            label: Optional human-readable label for the task.
            origin_channel: The channel to announce results to.
            origin_chat_id: The chat ID to announce results to.

        Returns:
            Status message indicating the subagent was started.
        """
        task_id = str(uuid.uuid4())[:8]
        display_label = label or task[:30] + ("..." if len(task) > 30 else "")

        origin = {
            "channel": origin_channel,
            "chat_id": origin_chat_id,
        }

        # Create background task
        model_to_use = model or self.model
        bg_task = asyncio.create_task(
            self._run_subagent(task_id, task, display_label, origin, model_to_use)
        )
        self._running_tasks[task_id] = bg_task

        # Cleanup when done (but results are kept in self._results)
        def _cleanup(t: asyncio.Task[str]):
            self._running_tasks.pop(task_id, None)

        bg_task.add_done_callback(_cleanup)

        logger.info(f"Spawned subagent [{task_id}]: {display_label}")
        return f"Subagent [{display_label}] started (id: {task_id}). I'll notify you when it completes."

    async def _run_subagent(
        self,
        task_id: str,
        task: str,
        label: str,
        origin: dict[str, str],
        model: str,
    ) -> str:
        """Execute the subagent task and announce the result."""
        logger.info(f"Subagent [{task_id}] starting task: {label}")

        try:
            # Build subagent tools (no message tool, no spawn tool)
            tools = ToolRegistry()
            restrict_workspace = getattr(self.exec_config, "restrict_to_workspace", False)
            tools.register(
                ReadFileTool(workspace=self.workspace, restrict_to_workspace=restrict_workspace)
            )
            tools.register(
                WriteFileTool(workspace=self.workspace, restrict_to_workspace=restrict_workspace)
            )
            tools.register(
                ListDirTool(workspace=self.workspace, restrict_to_workspace=restrict_workspace)
            )
            tools.register(
                ExecTool(
                    working_dir=str(self.workspace),
                    timeout=self.exec_config.timeout,
                    restrict_to_workspace=self.exec_config.restrict_to_workspace,
                )
            )
            tools.register(WebSearchTool())
            tools.register(WebFetchTool())

            # Build messages with subagent-specific prompt
            system_prompt = self._build_subagent_prompt(task)
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task},
            ]

            # Run agent loop (limited iterations)
            max_iterations = 15
            iteration = 0
            final_result: str | None = None

            while iteration < max_iterations:
                iteration += 1

                response = await self.provider.generate(
                    messages=messages,
                    tools=tools.get_definitions(),
                    model=model,
                )

                if response.has_tool_calls and response.tool_calls:
                    # Add assistant message with tool calls
                    tool_call_dicts = []
                    for tc in response.tool_calls:
                        tool_call_dicts.append(
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                        )

                    messages.append(
                        {
                            "role": "assistant",
                            "content": response.content or "",
                            "tool_calls": tool_call_dicts,
                        }
                    )

                    # Execute tools
                    if response.tool_calls:
                        for tool_call in response.tool_calls:
                            args = json.loads(tool_call.function.arguments)
                            name = tool_call.function.name
                            logger.debug(
                                f"Subagent [{task_id}] executing: {name} with arguments: {args}"
                            )
                            result = await tools.execute(name, args)
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": name,
                                    "content": result,
                                }
                            )
                else:
                    final_result = response.content
                    break

            if final_result is None:
                final_result = "Task completed but no final response was generated."

            logger.info(f"Subagent [{task_id}] completed successfully")
            await self._record_result(task_id, label, task, final_result, origin, "ok")
            return final_result

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(f"Subagent [{task_id}] failed: {e}")
            await self._record_result(task_id, label, task, error_msg, origin, "error")
            return error_msg

    async def _record_result(
        self,
        task_id: str,
        label: str,
        task: str,
        result: str,
        origin: dict[str, str],
        status: str,
    ) -> None:
        """Record the subagent result to the session and internal storage."""
        status_text = "completed successfully" if status == "ok" else "failed"

        announce_content = f"""[Subagent '{label}' {status_text}]

Task: {task}

Result:
{result}"""

        # Record to internal storage
        self._results[task_id] = {
            "task_id": task_id,
            "label": label,
            "task": task,
            "result": result,
            "status": status,
        }

        # Record to session
        # origin key is generic, usually channel:chat_id
        # We need to construct the key properly
        key = f"{origin['channel']}:{origin['chat_id']}"
        session = self.session_manager.get_or_create(key)
        session.add_message("system", announce_content)
        self.session_manager.save(session)

        logger.debug(f"Subagent [{task_id}] recorded result to {key}")

    async def wait_for(self, task_ids: list[str] | None = None) -> dict[str, Any]:
        """
        Wait for specific subagents to complete.
        If task_ids is None, waits for all currently running subagents.
        """
        if task_ids is None:
            ids_to_wait = list(self._running_tasks.keys())
        else:
            ids_to_wait = [tid for tid in task_ids if tid in self._running_tasks]

        if not ids_to_wait:
            return {"results": [], "summary": "No running subagents to wait for."}

        tasks = [self._running_tasks[tid] for tid in ids_to_wait]
        await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for tid in ids_to_wait:
            if tid in self._results:
                results.append(self._results[tid])
            else:
                results.append(
                    {"task_id": tid, "status": "unknown", "result": "Result not found after wait."}
                )

        summary = f"Waited for {len(ids_to_wait)} subagent(s)."
        return {"results": results, "summary": summary}

    def _build_subagent_prompt(self, task: str) -> str:
        """Build a focused system prompt for the subagent."""
        return f"""# Subagent

You are a subagent spawned by the main agent to complete a specific task.

## Your Task
{task}

## Rules
1. Stay focused - complete only the assigned task, nothing else
2. Your final response will be reported back to the main agent
3. Do not initiate conversations or take on side tasks
4. Be concise but informative in your findings

## What You Can Do
- Read and write files in the workspace
- Execute shell commands
- Search the web and fetch web pages
- Complete the task thoroughly

## What You Cannot Do
- Send messages directly to users (no message tool available)
- Spawn other subagents
- Access the main agent's conversation history

## Workspace
Your workspace is at: {self.workspace}

When you have completed the task, provide a clear summary of your findings or actions."""

    def get_running_count(self) -> int:
        """Return the number of currently running subagents."""
        return len(self._running_tasks)

    def get_result(self, task_id: str) -> dict[str, Any] | None:
        """Retrieve a result by task ID."""
        return self._results.get(task_id)

    def list_results(self) -> list[dict[str, Any]]:
        """List all completed subagent results."""
        return list(self._results.values())
