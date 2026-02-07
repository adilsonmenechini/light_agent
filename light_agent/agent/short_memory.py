"""Short-Term Memory module for Light Agent.

Provides in-memory context for the current session, including:
- Message window (recent conversation history)
- Task state (intermediate task data)
- Tool observations (temporary insights)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """Represents a single message in the conversation."""

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TaskState:
    """Represents intermediate state for complex tasks."""

    task_id: str
    name: str
    state: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ToolObservation:
    """Represents a temporary tool observation."""

    tool_name: str
    insight: str
    tool_input: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class ShortTermMemory:
    """In-memory storage for session-level context.

    Provides fast access to:
    - Recent message history (sliding window)
    - Task intermediate states
    - Temporary tool observations
    """

    def __init__(
        self,
        max_messages: int = 10,
        max_observations: int = 20,
    ) -> None:
        """Initialize short-term memory.

        Args:
            max_messages: Maximum number of messages to keep in window.
            max_observations: Maximum number of temporary observations.
        """
        self.max_messages = max_messages
        self.max_observations = max_observations
        self._messages: List[Message] = []
        self._task_states: Dict[str, TaskState] = {}
        self._observations: List[ToolObservation] = []

    @property
    def message_count(self) -> int:
        """Return current message count (excluding system)."""
        return len(self._messages)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the sliding window.

        Args:
            role: Message role (user, assistant, tool).
            content: Message content.
        """
        self._messages.append(Message(role=role, content=content))

        # Maintain sliding window
        if len(self._messages) > self.max_messages:
            self._messages.pop(0)

    def get_recent_messages(
        self,
        count: Optional[int] = None,
        include_system: bool = False,
    ) -> List[Message]:
        """Get recent messages.

        Args:
            count: Number of messages to return. Defaults to max_messages.
            include_system: Whether to include system messages.

        Returns:
            List of recent messages.
        """
        if count is None:
            count = self.max_messages

        messages = self._messages[-count:]

        if not include_system:
            messages = [m for m in messages if m.role != "system"]

        return messages

    def get_message_window(self) -> str:
        """Get formatted message window for LLM context.

        Returns:
            Formatted string of recent messages.
        """
        if not self._messages:
            return "No messages in current session."

        parts = ["## Session Message Window"]
        for msg in self._messages:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            parts.append(f"[{timestamp}] **{msg.role}**: {msg.content}")

        return "\n".join(parts)

    def clear_messages(self) -> None:
        """Clear all messages from short-term memory."""
        self._messages = []

    # Task State Management

    def set_task_state(self, task_id: str, name: str, state: Dict[str, Any]) -> None:
        """Set or update task state.

        Args:
            task_id: Unique task identifier.
            name: Human-readable task name.
            state: Task state data.
        """
        self._task_states[task_id] = TaskState(
            task_id=task_id,
            name=name,
            state=state,
            updated_at=datetime.utcnow(),
        )

    def get_task_state(self, task_id: str) -> Optional[TaskState]:
        """Get task state by ID.

        Args:
            task_id: Task identifier.

        Returns:
            TaskState or None if not found.
        """
        return self._task_states.get(task_id)

    def update_task_state(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in task state.

        Args:
            task_id: Task identifier.
            updates: Fields to update.

        Returns:
            True if task existed and was updated.
        """
        task = self._task_states.get(task_id)
        if not task:
            return False

        task.state.update(updates)
        task.updated_at = datetime.utcnow()
        return True

    def remove_task_state(self, task_id: str) -> bool:
        """Remove task state.

        Args:
            task_id: Task identifier.

        Returns:
            True if task was removed.
        """
        if task_id in self._task_states:
            del self._task_states[task_id]
            return True
        return False

    def get_all_task_states(self) -> List[TaskState]:
        """Get all current task states.

        Returns:
            List of all task states.
        """
        return list(self._task_states.values())

    def clear_task_states(self) -> None:
        """Clear all task states."""
        self._task_states.clear()

    # Temporary Observations

    def add_observation(
        self,
        tool_name: str,
        insight: str,
        tool_input: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a temporary tool observation.

        Args:
            tool_name: Name of the tool.
            insight: Observed insight.
            tool_input: Tool input parameters.
        """
        self._observations.append(
            ToolObservation(
                tool_name=tool_name,
                insight=insight,
                tool_input=tool_input or {},
            )
        )

        # Maintain max observations limit
        if len(self._observations) > self.max_observations:
            self._observations.pop(0)

    def get_observations(self, limit: Optional[int] = None) -> List[ToolObservation]:
        """Get recent observations.

        Args:
            limit: Maximum observations to return.

        Returns:
            List of recent observations.
        """
        if limit is None:
            limit = self.max_observations
        return self._observations[-limit:]

    def get_observations_summary(self) -> str:
        """Get formatted summary of observations.

        Returns:
            Formatted string of recent observations.
        """
        if not self._observations:
            return "No temporary observations in current session."

        parts = ["## Temporary Observations (Session)"]
        for obs in self._observations:
            timestamp = obs.created_at.strftime("%H:%M:%S")
            parts.append(f"[{timestamp}] **{obs.tool_name}**: {obs.insight}")

        return "\n".join(parts)

    def clear_observations(self) -> None:
        """Clear all temporary observations."""
        self._observations.clear()

    # Full Session Clear

    def clear_all(self) -> None:
        """Clear all short-term memory (messages, tasks, observations)."""
        self.clear_messages()
        self.clear_task_states()
        self.clear_observations()

    # Export for Persistence

    def export_session_data(self) -> Dict[str, Any]:
        """Export current session data for potential persistence.

        Returns:
            Dictionary containing all session data.
        """
        return {
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
                for m in self._messages
            ],
            "task_states": {
                tid: {
                    "task_id": ts.task_id,
                    "name": ts.name,
                    "state": ts.state,
                    "created_at": ts.created_at.isoformat(),
                    "updated_at": ts.updated_at.isoformat(),
                }
                for tid, ts in self._task_states.items()
            },
            "observations": [
                {
                    "tool_name": obs.tool_name,
                    "insight": obs.insight,
                    "tool_input": obs.tool_input,
                    "created_at": obs.created_at.isoformat(),
                }
                for obs in self._observations
            ],
        }

    def import_session_data(self, data: Dict[str, Any]) -> None:
        """Import session data from previous session.

        Args:
            data: Session data dictionary.
        """
        # Import messages
        if "messages" in data:
            self._messages = [
                Message(
                    role=m["role"],
                    content=m["content"],
                    timestamp=datetime.fromisoformat(m["timestamp"]),
                )
                for m in data["messages"]
            ]

        # Import task states
        if "task_states" in data:
            self._task_states = {
                tid: TaskState(
                    task_id=ts["task_id"],
                    name=ts["name"],
                    state=ts["state"],
                    created_at=datetime.fromisoformat(ts["created_at"]),
                    updated_at=datetime.fromisoformat(ts["updated_at"]),
                )
                for tid, ts in data["task_states"].items()
            }

        # Import observations
        if "observations" in data:
            self._observations = [
                ToolObservation(
                    tool_name=obs["tool_name"],
                    insight=obs["insight"],
                    tool_input=obs["tool_input"],
                    created_at=datetime.fromisoformat(obs["created_at"]),
                )
                for obs in data["observations"]
            ]
