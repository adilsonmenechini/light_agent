"""Reducer pattern for stateless agent state transitions."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ThreadState:
    """Immutable thread state for reducer pattern."""

    thread_id: str
    version: int
    created_at: datetime
    updated_at: datetime
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]

    @classmethod
    def create(cls, thread_id: str, metadata: Optional[Dict[str, Any]] = None) -> "ThreadState":
        """Create initial thread state."""
        now = datetime.utcnow()
        return cls(
            thread_id=thread_id,
            version=1,
            created_at=now,
            updated_at=now,
            messages=[],
            metadata=metadata or {},
        )

    def add_message(self, role: str, content: Any) -> "ThreadState":
        """Return new state with message added."""
        new_message = {"role": role, "content": content, "timestamp": datetime.utcnow().isoformat()}
        return ThreadState(
            thread_id=self.thread_id,
            version=self.version + 1,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            messages=self.messages + [new_message],
            metadata=self.metadata.copy(),
        )

    def with_metadata(self, key: str, value: Any) -> "ThreadState":
        """Return new state with metadata updated."""
        new_metadata = self.metadata.copy()
        new_metadata[key] = value
        return ThreadState(
            thread_id=self.thread_id,
            version=self.version + 1,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            messages=self.messages.copy(),
            metadata=new_metadata,
        )


class AgentReducer:
    """Pure reducer for agent state transitions."""

    def reduce(
        self, state: ThreadState, event: Dict[str, Any]
    ) -> Tuple[ThreadState, Optional[Dict[str, Any]]]:
        """Apply event to state, returning new state and agent response.

        Args:
            state: Current thread state
            event: Event to apply (e.g., {"role": "user", "content": "..."})

        Returns:
            Tuple of (new_state, agent_response or None)
        """
        event_type = event.get("type", "message")
        role = event.get("role", "user")
        content = event.get("content", "")

        if event_type == "message":
            new_state = state.add_message(role, content)
            response = self._generate_response(new_state)
            return new_state, response

        elif event_type == "metadata":
            new_state = state.with_metadata(event.get("key", ""), event.get("value", ""))
            return new_state, None

        elif event_type == "fork":
            return self._fork(state, event)

        elif event_type == "checkpoint":
            return state.with_metadata("checkpoint", event.get("checkpoint_id", "")), None

        return state, None

    def _generate_response(self, state: ThreadState) -> Optional[Dict[str, Any]]:
        """Generate agent response based on current state.

        In a full implementation, this would call the LLM.
        For now, returns a placeholder.
        """
        return {"type": "thought", "content": f"Processing message {len(state.messages)}"}

    def _fork(
        self, state: ThreadState, event: Dict[str, Any]
    ) -> Tuple[ThreadState, Optional[Dict[str, Any]]]:
        """Fork state to create a branch."""
        branch_id = event.get("branch_id", f"branch_{datetime.utcnow().strftime('%H%M%S')}")
        forked_state = state.with_metadata("parent_branch", state.thread_id)
        forked_state = ThreadState(
            thread_id=branch_id,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            messages=forked_state.messages.copy(),
            metadata={
                **forked_state.metadata,
                "branched_from": state.thread_id,
                "branch_type": event.get("branch_type", "exploration"),
            },
        )
        return forked_state, {
            "type": "fork_created",
            "branch_id": branch_id,
            "parent_thread_id": state.thread_id,
        }


def serialize_state(state: ThreadState) -> Dict[str, Any]:
    """Convert thread state to JSON-serializable dict."""
    return {
        "thread_id": state.thread_id,
        "version": state.version,
        "created_at": state.created_at.isoformat(),
        "updated_at": state.updated_at.isoformat(),
        "messages": state.messages,
        "metadata": state.metadata,
    }


def deserialize_state(data: Dict[str, Any]) -> ThreadState:
    """Create ThreadState from dict."""
    return ThreadState(
        thread_id=data["thread_id"],
        version=data["version"],
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        messages=data["messages"],
        metadata=data["metadata"],
    )
