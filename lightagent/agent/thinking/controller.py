"""Thinking controller for managing agent reasoning."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json

from .config import (
    ThinkLevel,
    ThinkingConfig,
    default_thinking_config,
    should_use_thinking,
    estimate_thinking_effort,
    get_level_description,
)


class ThinkingState(Enum):
    """State of thinking process."""

    IDLE = "idle"
    THINKING = "thinking"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class ThinkingEvent:
    """Represents a thinking event."""

    event_type: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    level: Optional[ThinkLevel] = None
    thought: Optional[str] = None
    context_length: int = 0
    duration_ms: Optional[int] = None
    metadata: dict = field(default_factory=dict)


class ThinkingController:
    """Controller for managing agent thinking process."""

    def __init__(self, config: Optional[ThinkingConfig] = None, emit_events: bool = True):
        """Initialize the thinking controller.

        Args:
            config: Thinking configuration.
            emit_events: Whether to emit thinking events.
        """
        self.config = config or default_thinking_config()
        self.emit_events = emit_events
        self.state = ThinkingState.IDLE
        self._current_thought: Optional[str] = None
        self._thought_history: list[ThinkingEvent] = []
        self._start_time: Optional[datetime] = None
        self._complexity_score: float = 0.0

    @property
    def level(self) -> ThinkLevel:
        """Get current thinking level."""
        return self.config.level

    @property
    def is_thinking(self) -> bool:
        """Check if currently thinking."""
        return self.state == ThinkingState.THINKING

    @property
    def thought_history(self) -> list[ThinkingEvent]:
        """Get thinking history."""
        return list(self._thought_history)

    def set_level(self, level: ThinkLevel) -> None:
        """Set thinking level.

        Args:
            level: New thinking level.
        """
        old_level = self.config.level
        self.config.level = level

        if self.emit_events:
            self._emit_event(
                ThinkingEvent(
                    event_type="level_changed",
                    level=level,
                    metadata={"old_level": old_level.value, "new_level": level.value},
                )
            )

    def start_thinking(
        self, context_length: int = 0, is_complex: bool = False, task_type: Optional[str] = None
    ) -> bool:
        """Start thinking process.

        Args:
            context_length: Current context length.
            is_complex: Whether the task is complex.
            task_type: Type of task being performed.

        Returns:
            True if thinking started.
        """
        if not should_use_thinking(self.config, context_length, is_complex):
            self.state = ThinkingState.IDLE
            return False

        self.state = ThinkingState.THINKING
        self._start_time = datetime.now()
        self._complexity_score = self._calculate_complexity(context_length, is_complex, task_type)

        if self.emit_events:
            self._emit_event(
                ThinkingEvent(
                    event_type="started",
                    level=self.config.level,
                    context_length=context_length,
                    metadata={"complexity_score": self._complexity_score, "task_type": task_type},
                )
            )

        return True

    def pause_thinking(self) -> None:
        """Pause thinking process."""
        if self.state == ThinkingState.THINKING:
            self.state = ThinkingState.PAUSED

            if self.emit_events:
                self._emit_event(ThinkingEvent(event_type="paused", level=self.config.level))

    def resume_thinking(self) -> None:
        """Resume thinking process."""
        if self.state == ThinkingState.PAUSED:
            self.state = ThinkingState.THINKING

            if self.emit_events:
                self._emit_event(ThinkingEvent(event_type="resumed", level=self.config.level))

    def complete_thinking(self, final_thought: Optional[str] = None) -> Optional[ThinkingEvent]:
        """Complete thinking process.

        Args:
            final_thought: Final thought summary.

        Returns:
            The completed thinking event.
        """
        if self.state not in (ThinkingState.THINKING, ThinkingState.PAUSED):
            return None

        duration_ms = None
        if self._start_time:
            duration_ms = int((datetime.now() - self._start_time).total_seconds() * 1000)

        self._current_thought = final_thought

        event = ThinkingEvent(
            event_type="completed",
            level=self.config.level,
            thought=final_thought,
            context_length=len(self._thought_history),
            duration_ms=duration_ms,
            metadata={"complexity_score": self._complexity_score},
        )

        self._thought_history.append(event)

        if self.config.store_thinking_history:
            self._trim_history()

        self.state = ThinkingState.COMPLETED
        self._start_time = None

        if self.emit_events:
            self._emit_event(event)

        return event

    def add_thought(self, thought: str) -> None:
        """Add intermediate thought.

        Args:
            thought: The thought to add.
        """
        if self.state != ThinkingState.THINKING:
            return

        event = ThinkingEvent(
            event_type="thought",
            level=self.config.level,
            thought=thought,
            metadata={"position": len(self._thought_history)},
        )

        self._thought_history.append(event)

        if self.emit_events:
            self._emit_event(event)

    def get_effort_description(self, context_length: int = 0) -> str:
        """Get effort description for current level.

        Args:
            context_length: Current context length.

        Returns:
            Effort description.
        """
        return estimate_thinking_effort(
            self.config.level, context_length, self._complexity_score > 0.5
        )

    def should_emit_detailed_thinking(self) -> bool:
        """Check if detailed thinking should be emitted.

        Returns:
            True if detailed thinking should be emitted.
        """
        return self.config.emit_thinking_events and self.config.level in (
            ThinkLevel.MEDIUM,
            ThinkLevel.HIGH,
        )

    def should_emit_summary_only(self) -> bool:
        """Check if only summary should be emitted.

        Returns:
            True if only summary should be emitted.
        """
        return self.config.emit_thinking_events and self.config.level == ThinkLevel.LOW

    def reset(self) -> None:
        """Reset thinking state."""
        self.state = ThinkingState.IDLE
        self._current_thought = None
        self._start_time = None
        self._complexity_score = 0.0

        if self.emit_events:
            self._emit_event(ThinkingEvent(event_type="reset"))

    def get_level_description(self) -> str:
        """Get description of current level."""
        return get_level_description(self.config.level)

    def _calculate_complexity(
        self, context_length: int, is_complex: bool, task_type: Optional[str]
    ) -> float:
        """Calculate complexity score.

        Args:
            context_length: Current context length.
            is_complex: Whether task is complex.
            task_type: Type of task.

        Returns:
            Complexity score between 0 and 1.
        """
        score = 0.0

        # Context contribution
        if context_length > 20:
            score += 0.4
        elif context_length > 10:
            score += 0.2
        elif context_length > 5:
            score += 0.1

        # Complexity flag
        if is_complex:
            score += 0.3

        # Task type contribution
        complex_tasks = {"refactor", "debug", "analyze", "design", "architect"}
        if task_type and task_type.lower() in complex_tasks:
            score += 0.3

        return min(1.0, score)

    def _trim_history(self) -> None:
        """Trim history to max entries."""
        max_entries = self.config.max_history_entries
        if len(self._thought_history) > max_entries:
            self._thought_history = self._thought_history[-max_entries:]

    def _emit_event(self, event: ThinkingEvent) -> None:
        """Emit thinking event.

        Args:
            event: The event to emit.
        """
        # Import here to avoid circular imports
        try:
            from lightagent.core import emit_thinking

            emit_thinking(message=event.thought or "", agent="thinking_controller", tool=None)
        except ImportError:
            pass  # Core module not available in tests

    def get_state_summary(self) -> dict:
        """Get current state summary.

        Returns:
            State summary dictionary.
        """
        return {
            "state": self.state.value,
            "level": self.config.level.value,
            "is_thinking": self.is_thinking,
            "history_count": len(self._thought_history),
            "level_description": self.get_level_description(),
            "effort": self.get_effort_description(),
        }

    def to_json(self) -> str:
        """Serialize controller state to JSON.

        Returns:
            JSON string representation.
        """
        return json.dumps(
            {
                "config": {
                    "level": self.config.level.value,
                    "max_thought_length": self.config.max_thought_length,
                    "emit_thinking_events": self.config.emit_thinking_events,
                    "store_thinking_history": self.config.store_thinking_history,
                    "max_history_entries": self.config.max_history_entries,
                },
                "state": self.state.value,
                "history_count": len(self._thought_history),
            },
            indent=2,
        )
