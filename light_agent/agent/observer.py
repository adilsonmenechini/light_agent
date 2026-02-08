"""Observer pattern implementation for agent event system.

This module provides:
- AgentObserver: Interface for observers that receive agent events
- AgentEvent: Base class for all agent events
- AgentSubject: Observable that manages observers and emits events
- AsyncEventBus: Enhanced event bus supporting async subscribers
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import uuid4


class AgentEventType(Enum):
    """Types of events that agents can emit.

    Each event type represents a specific occurrence in the agent lifecycle,
    from task creation to completion or failure.
    """

    # Task lifecycle events
    TASK_STARTED = "task_started"
    """Emitted when a new task begins execution."""

    TASK_COMPLETED = "task_completed"
    """Emitted when a task finishes successfully."""

    TASK_FAILED = "task_failed"
    """Emitted when a task encounters an error and fails."""

    TASK_CANCELLED = "task_cancelled"
    """Emitted when a task is cancelled before completion."""

    # Tool events
    TOOL_CALLED = "tool_called"
    """Emitted when an agent calls a tool."""

    TOOL_STARTED = "tool_started"
    """Emitted when a tool starts executing."""

    TOOL_COMPLETED = "tool_completed"
    """Emitted when a tool finishes successfully."""

    TOOL_FAILED = "tool_failed"
    """Emitted when a tool encounters an error."""

    # LLM events
    LLM_REQUEST_STARTED = "llm_request_started"
    """Emitted when an LLM API request is initiated."""

    LLM_REQUEST_COMPLETED = "llm_request_completed"
    """Emitted when an LLM API request completes successfully."""

    LLM_REQUEST_FAILED = "llm_request_failed"
    """Emitted when an LLM API request fails."""

    # Agent events
    AGENT_STARTED = "agent_started"
    """Emitted when an agent instance starts."""

    AGENT_COMPLETED = "agent_completed"
    """Emitted when an agent completes its execution."""

    AGENT_ERROR = "agent_error"
    """Emitted when an agent encounters a critical error."""

    # Performance events
    PERFORMANCE_ALERT = "performance_alert"
    """Emitted when a performance threshold is exceeded."""

    RATE_LIMIT_WARNING = "rate_limit_warning"
    """Emitted when approaching rate limit thresholds."""

    # Custom events
    CUSTOM = "custom"
    """Reserved for custom event types defined by observers."""


@dataclass
class AgentEvent:
    """Base event class for all agent events.

    Attributes:
        event_id: Unique identifier for this event
        event_type: Type of the event
        timestamp: When the event occurred
        source: Name/ID of the agent that emitted this event
        data: Event-specific payload
        metadata: Additional context information
    """

    event_id: str = field(default_factory=lambda: str(uuid4())[:8])
    event_type: AgentEventType = AgentEventType.CUSTOM
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "agent"
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_error(self) -> bool:
        """Check if this is an error event."""
        return self.event_type in (
            AgentEventType.TASK_FAILED,
            AgentEventType.TOOL_FAILED,
            AgentEventType.LLM_REQUEST_FAILED,
            AgentEventType.AGENT_ERROR,
        )


# Type variable for generic observer
ObserverT = TypeVar("ObserverT", bound="AgentObserver")


class AgentObserver(ABC):
    """Abstract base class for agents that observe events.

    All observer agents must implement this interface to receive
    events from the AgentSubject.

    Usage:
        class MyObserver(AgentObserver):
            async def on_event(self, event: AgentEvent) -> None:
                if event.event_type == AgentEventType.TASK_COMPLETED:
                    print(f"Task completed: {event.data}")

        observer = MyObserver()
        subject.attach(observer)
    """

    @property
    @abstractmethod
    def observer_id(self) -> str:
        """Unique identifier for this observer."""
        pass

    @property
    @abstractmethod
    def observer_name(self) -> str:
        """Human-readable name for logging."""
        pass

    @abstractmethod
    async def on_event(self, event: AgentEvent) -> None:
        """Handle an incoming event.

        Args:
            event: The event to process
        """
        pass

    async def on_task_started(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """Handle task started event."""

    async def on_task_completed(self, task_id: str, result: Any) -> None:
        """Handle task completed event."""

    async def on_task_failed(self, task_id: str, error: str) -> None:
        """Handle task failed event."""

    async def on_tool_called(self, tool_name: str, args: Dict[str, Any]) -> None:
        """Handle tool called event."""

    async def on_tool_completed(self, tool_name: str, result: str) -> None:
        """Handle tool completed event."""

    async def on_tool_failed(self, tool_name: str, error: str) -> None:
        """Handle tool failed event."""

    async def on_llm_request_started(self, model: str, prompt: str) -> None:
        """Handle LLM request started event."""

    async def on_llm_request_completed(self, model: str, response: str) -> None:
        """Handle LLM request completed event."""

    async def on_llm_request_failed(self, model: str, error: str) -> None:
        """Handle LLM request failed event."""

    async def on_agent_error(self, error: str, context: Dict[str, Any]) -> None:
        """Handle agent error event."""

    async def on_performance_alert(self, metric: str, value: float, threshold: float) -> None:
        """Handle performance alert event."""

    async def on_rate_limit_warning(self, resource: str, current_usage: int, limit: int) -> None:
        """Handle rate limit warning event."""


class Subscription:
    """Represents a subscription to an event type."""

    def __init__(
        self,
        observer: AgentObserver,
        event_types: Optional[List[AgentEventType]] = None,
        filter_func: Optional[Callable[[AgentEvent], bool]] = None,
    ):
        self.observer = observer
        self.event_types = event_types
        self.filter_func = filter_func
        self.is_active = True

    def matches(self, event: AgentEvent) -> bool:
        """Check if this subscription matches the event."""
        if not self.is_active:
            return False
        if self.event_types and event.event_type not in self.event_types:
            return False
        if self.filter_func and not self.filter_func(event):
            return False
        return True


class AgentSubject:
    """Observable subject that manages observers and emits events.

    This class implements the Observer pattern for the agent system.
    Observers can subscribe to specific event types and receive notifications
    when those events occur.

    Usage:
        subject = AgentSubject()

        # Create observer
        class MyObserver(AgentObserver):
            @property
            def observer_id(self) -> str:
                return "my_observer"

            @property
            def observer_name(self) -> str:
                return "My Observer"

            async def on_event(self, event: AgentEvent) -> None:
                print(f"Received: {event.event_type}")

        # Subscribe observer
        observer = MyObserver()
        subject.attach(observer)

        # Emit events
        subject.emit(AgentEvent(
            event_type=AgentEventType.TASK_STARTED,
            source="agent_1",
            data={"task_id": "task_123"}
        ))

        # Detach when done
        subject.detach(observer)
    """

    def __init__(self, name: str = "AgentSubject"):
        self.name = name
        self._observers: Dict[str, Subscription] = {}
        self._event_history: List[AgentEvent] = []
        self._max_history = 1000
        self._is_emitting = False

    @property
    def observer_count(self) -> int:
        """Return the number of active observers."""
        return len(self._observers)

    @property
    def event_history(self) -> List[AgentEvent]:
        """Return recent event history."""
        return self._event_history[-self._max_history :]

    def attach(
        self,
        observer: AgentObserver,
        event_types: Optional[List[AgentEventType]] = None,
        filter_func: Optional[Callable[[AgentEvent], bool]] = None,
    ) -> str:
        """Subscribe an observer to receive events.

        Args:
            observer: The observer to subscribe
            event_types: Optional list of event types to subscribe to
            filter_func: Optional function to filter events

        Returns:
            Subscription ID
        """
        subscription = Subscription(observer, event_types, filter_func)
        self._observers[observer.observer_id] = subscription
        return observer.observer_id

    def detach(self, observer_id: str) -> bool:
        """Unsubscribe an observer.

        Args:
            observer_id: The observer ID to remove

        Returns:
            True if observer was found and removed
        """
        if observer_id in self._observers:
            self._observers[observer_id].is_active = False
            del self._observers[observer_id]
            return True
        return False

    def detach_all(self) -> int:
        """Detach all observers.

        Returns:
            Number of observers detached
        """
        count = len(self._observers)
        self._observers.clear()
        return count

    def get_observer(self, observer_id: str) -> Optional[AgentObserver]:
        """Get an observer by ID."""
        sub = self._observers.get(observer_id)
        return sub.observer if sub else None

    def get_all_observers(self) -> List[AgentObserver]:
        """Get all active observers."""
        return [sub.observer for sub in self._observers.values() if sub.is_active]

    def emit(self, event: AgentEvent) -> int:
        """Emit an event to all matching observers.

        Args:
            event: The event to emit

        Returns:
            Number of observers notified
        """
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Find matching observers
        matching = [sub.observer for sub in self._observers.values() if sub.matches(event)]

        # Notify synchronously (use AsyncAgentSubject for async)
        for observer in matching:
            try:
                # Route to specific handler if available
                handler_name = f"on_{event.event_type.value}"
                handler = getattr(observer, handler_name, None)
                if handler:
                    # Call with unpacked data - handlers can be async or sync
                    if callable(handler):
                        try:
                            result = handler(**event.data)
                            if asyncio.iscoroutine(result):
                                # Run async handlers in sync context
                                asyncio.get_event_loop().run_until_complete(result)
                        except Exception:
                            pass
                else:
                    # Fall back to generic handler
                    try:
                        result = observer.on_event(event)
                        if asyncio.iscoroutine(result):
                            asyncio.get_event_loop().run_until_complete(result)
                    except Exception:
                        pass
            except Exception:
                pass  # Don't let observer errors break the bus

        return len(matching)


class AsyncAgentSubject(AgentSubject):
    """Async version of AgentSubject that supports async observers.

    This class emits events asynchronously, allowing observers to perform
    async operations in their event handlers.
    """

    def __init__(self, name: str = "AsyncAgentSubject", max_concurrent: int = 100):
        super().__init__(name)
        self._max_concurrent = max_concurrent

    async def emit_async(self, event: AgentEvent) -> int:
        """Emit an event asynchronously to all matching observers.

        Args:
            event: The event to emit

        Returns:
            Number of observers notified
        """
        import asyncio

        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Find matching observers
        matching = [sub.observer for sub in self._observers.values() if sub.matches(event)]

        if not matching:
            return 0

        # Create tasks for all observers
        tasks = []
        for observer in matching:
            try:
                # Route to specific handler if available
                handler_name = f"on_{event.event_type.value}"
                handler = getattr(observer, handler_name, None)
                if handler:
                    task = asyncio.create_task(self._call_handler(handler, event))
                    tasks.append(task)
                else:
                    task = asyncio.create_task(observer.on_event(event))
                    tasks.append(task)
            except Exception:
                pass  # Don't let observer errors break the bus

        # Wait for all with limit
        if len(tasks) > self._max_concurrent:
            tasks = tasks[: self._max_concurrent]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return len(matching)

    async def _call_handler(self, handler: Callable, event: AgentEvent) -> None:
        """Call a handler with event data as kwargs."""
        await handler(**event.data)


class ObserverRegistry:
    """Registry for managing multiple observer subjects.

    Provides a central place to manage observers across different
    contexts or components.
    """

    def __init__(self):
        self._subjects: Dict[str, AgentSubject] = {}

    def get_or_create(self, name: str) -> AgentSubject:
        """Get or create a subject by name."""
        if name not in self._subjects:
            self._subjects[name] = AgentSubject(name=name)
        return self._subjects[name]

    def get(self, name: str) -> Optional[AgentSubject]:
        """Get a subject by name."""
        return self._subjects.get(name)

    def register_observer(
        self,
        subject_name: str,
        observer: AgentObserver,
        event_types: Optional[List[AgentEventType]] = None,
    ) -> bool:
        """Register an observer with a subject."""
        subject = self.get_or_create(subject_name)
        subject.attach(observer, event_types)
        return True

    def unregister_observer(self, subject_name: str, observer_id: str) -> bool:
        """Unregister an observer from a subject."""
        subject = self.get(subject_name)
        if subject:
            return subject.detach(observer_id)
        return False

    def emit(
        self,
        subject_name: str,
        event: AgentEvent,
    ) -> int:
        """Emit an event to a subject."""
        subject = self.get(subject_name)
        if subject:
            return subject.emit(event)
        return 0

    def list_subjects(self) -> List[str]:
        """List all subject names."""
        return list(self._subjects.keys())


# Global registry instance
observer_registry = ObserverRegistry()


# Convenience functions for common event emissions
def emit_task_started(
    source: str,
    task_id: str,
    task_type: str,
    **extra_data,
) -> AgentEvent:
    """Create and emit a task started event.

    Args:
        source: The agent or component emitting the event.
        task_id: Unique identifier for the task.
        task_type: Type/category of the task.
        **extra_data: Additional event data.

    Returns:
        The created AgentEvent instance.
    """
    event = AgentEvent(
        event_type=AgentEventType.TASK_STARTED,
        source=source,
        data={"task_id": task_id, "task_type": task_type, **extra_data},
    )
    return event


def emit_task_completed(source: str, task_id: str, result: Any, **extra_data) -> AgentEvent:
    """Create and emit a task completed event.

    Args:
        source: The agent or component emitting the event.
        task_id: Unique identifier for the completed task.
        result: The result of the task execution.
        **extra_data: Additional event data.

    Returns:
        The created AgentEvent instance.
    """
    event = AgentEvent(
        event_type=AgentEventType.TASK_COMPLETED,
        source=source,
        data={"task_id": task_id, "result": str(result)[:1000], **extra_data},
    )
    return event


def emit_task_failed(source: str, task_id: str, error: str, **extra_data) -> AgentEvent:
    """Create and emit a task failed event.

    Args:
        source: The agent or component emitting the event.
        task_id: Unique identifier for the failed task.
        error: Error message or description of the failure.
        **extra_data: Additional event data.

    Returns:
        The created AgentEvent instance.
    """
    event = AgentEvent(
        event_type=AgentEventType.TASK_FAILED,
        source=source,
        data={"task_id": task_id, "error": error, **extra_data},
    )
    return event


def emit_tool_called(source: str, tool_name: str, args: Dict[str, Any], **extra_data) -> AgentEvent:
    """Create and emit a tool called event.

    Args:
        source: The agent or component emitting the event.
        tool_name: Name of the tool being called.
        args: Arguments passed to the tool.
        **extra_data: Additional event data.

    Returns:
        The created AgentEvent instance.
    """
    event = AgentEvent(
        event_type=AgentEventType.TOOL_CALLED,
        source=source,
        data={"tool_name": tool_name, "args": args, **extra_data},
    )
    return event


def emit_tool_completed(source: str, tool_name: str, result: str, **extra_data) -> AgentEvent:
    """Create and emit a tool completed event.

    Args:
        source: The agent or component emitting the event.
        tool_name: Name of the tool that completed.
        result: The result returned by the tool.
        **extra_data: Additional event data.

    Returns:
        The created AgentEvent instance.
    """
    event = AgentEvent(
        event_type=AgentEventType.TOOL_COMPLETED,
        source=source,
        data={"tool_name": tool_name, "result": result[:1000], **extra_data},
    )
    return event


def emit_tool_failed(source: str, tool_name: str, error: str, **extra_data) -> AgentEvent:
    """Create and emit a tool failed event.

    Args:
        source: The agent or component emitting the event.
        tool_name: Name of the tool that failed.
        error: Error message from the tool.
        **extra_data: Additional event data.

    Returns:
        The created AgentEvent instance.
    """
    event = AgentEvent(
        event_type=AgentEventType.TOOL_FAILED,
        source=source,
        data={"tool_name": tool_name, "error": error, **extra_data},
    )
    return event


def emit_agent_error(source: str, error: str, **extra_data) -> AgentEvent:
    """Create and emit an agent error event.

    Args:
        source: The agent or component emitting the event.
        error: Error message describing the issue.
        **extra_data: Additional event data.

    Returns:
        The created AgentEvent instance.
    """
    event = AgentEvent(
        event_type=AgentEventType.AGENT_ERROR,
        source=source,
        data={"error": error, **extra_data},
    )
    return event


def emit_performance_alert(
    source: str, metric: str, value: float, threshold: float, **extra_data
) -> AgentEvent:
    """Create and emit a performance alert event.

    Args:
        source: The agent or component emitting the event.
        metric: Name of the performance metric (e.g., 'latency', 'memory').
        value: Current value of the metric.
        threshold: Threshold that was exceeded.
        **extra_data: Additional event data.

    Returns:
        The created AgentEvent instance.
    """
    event = AgentEvent(
        event_type=AgentEventType.PERFORMANCE_ALERT,
        source=source,
        data={"metric": metric, "value": value, "threshold": threshold, **extra_data},
    )
    return event
