"""Thread state management for 12-Factor Agents."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ThreadStatus(Enum):
    """Status of an agent thread."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ThreadState(BaseModel):
    """Unified state representation for agent thread."""

    thread_id: str
    version: int = 1
    created_at: datetime
    updated_at: datetime
    messages: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

    @classmethod
    def create(cls, thread_id: str, metadata: Optional[Dict[str, Any]] = None) -> "ThreadState":
        """Create a new thread with default values."""
        now = datetime.utcnow()
        return cls(
            thread_id=thread_id,
            created_at=now,
            updated_at=now,
            messages=[],
            metadata=metadata or {},
        )

    def add_message(self, role: str, content: Any) -> None:
        """Add a message to the thread."""
        self.messages.append(
            {"role": role, "content": content, "timestamp": datetime.utcnow().isoformat()}
        )
        self.updated_at = datetime.utcnow()

    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """Get the last message in the thread."""
        return self.messages[-1] if self.messages else None
