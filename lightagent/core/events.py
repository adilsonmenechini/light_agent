"""Event Bus for agent thinking/status events."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EventType(Enum):
    """Types of events the agent can emit."""

    THINKING = "thinking"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOOL_ERROR = "tool_error"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"


@dataclass
class Event:
    """An event in the agent system."""

    type: EventType
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source: str = "agent"


class EventBus:
    """Simple publish/subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._all_subscribers: List[Callable[[Event], None]] = []
        self._enabled = True

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Subscribe to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def subscribe_all(self, callback: Callable[[Event], None]) -> None:
        """Subscribe to all events."""
        self._all_subscribers.append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def emit(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        if not self._enabled:
            return

        # Notify type-specific subscribers
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                try:
                    callback(event)
                except Exception:
                    pass  # Don't let subscriber errors break the bus

        # Notify all-subscribers
        for callback in self._all_subscribers:
            try:
                callback(event)
            except Exception:
                pass

    def disable(self) -> None:
        """Disable event emission."""
        self._enabled = False

    def enable(self) -> None:
        """Enable event emission."""
        self._enabled = True


# Global event bus instance
event_bus = EventBus()


def emit_thinking(message: str, agent: Optional[str] = None, tool: Optional[str] = None) -> None:
    """Emit a thinking event."""
    event = Event(type=EventType.THINKING, data={"message": message, "agent": agent, "tool": tool})
    event_bus.emit(event)


def emit_tool_start(name: str, args: Dict[str, Any]) -> None:
    """Emit tool start event."""
    event = Event(type=EventType.TOOL_START, data={"name": name, "args": args})
    event_bus.emit(event)


def emit_tool_end(name: str, result: str) -> None:
    """Emit tool end event."""
    event = Event(type=EventType.TOOL_END, data={"name": name, "result_preview": result[:100]})
    event_bus.emit(event)


def emit_tool_error(name: str, error: str) -> None:
    """Emit tool error event."""
    event = Event(type=EventType.TOOL_ERROR, data={"name": name, "error": error})
    event_bus.emit(event)


def emit_agent_start(name: str, task: str) -> None:
    """Emit agent start event."""
    event = Event(type=EventType.AGENT_START, data={"name": name, "task": task[:100]})
    event_bus.emit(event)


def emit_agent_end(name: str, result_preview: str = "") -> None:
    """Emit agent end event."""
    event = Event(
        type=EventType.AGENT_END,
        data={"name": name, "result_preview": result_preview[:100]},
    )
    event_bus.emit(event)


def emit_llm_call(model: str, message_count: int) -> None:
    """Emit LLM call event."""
    event = Event(type=EventType.LLM_CALL, data={"model": model, "message_count": message_count})
    event_bus.emit(event)


def emit_llm_response(model: str, response_preview: str) -> None:
    """Emit LLM response event."""
    event = Event(
        type=EventType.LLM_RESPONSE,
        data={"model": model, "response_preview": response_preview[:100]},
    )
    event_bus.emit(event)
