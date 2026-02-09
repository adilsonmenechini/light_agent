"""Thinking configuration and levels."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ThinkLevel(Enum):
    """Thinking levels for agent reasoning."""

    OFF = "off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ThinkingConfig:
    """Configuration for thinking behavior."""

    level: ThinkLevel = ThinkLevel.MEDIUM
    max_thought_length: int = 2000
    emit_thinking_events: bool = True
    store_thinking_history: bool = True
    max_history_entries: int = 50
    min_context_for_thinking: int = 5
    auto_escalate: bool = False
    escalation_threshold: int = 3


def default_thinking_config() -> ThinkingConfig:
    """Get default thinking configuration."""
    return ThinkingConfig()


def think_level_from_string(value: str) -> ThinkLevel:
    """Convert string to ThinkLevel."""
    value_lower = value.lower()
    for level in ThinkLevel:
        if level.value == value_lower:
            return level
    return ThinkLevel.MEDIUM


def get_level_description(level: ThinkLevel) -> str:
    """Get human-readable description of thinking level."""
    descriptions = {
        ThinkLevel.OFF: "Sem reasoning explícito. Respostas diretas.",
        ThinkLevel.LOW: "Reasoning mínimo. Respostas rápidas e concisas.",
        ThinkLevel.MEDIUM: "Reasoning balanceado. Explicações claras.",
        ThinkLevel.HIGH: "Reasoning extensivo. Análise profunda.",
    }
    return descriptions.get(level, "Nível desconhecido.")


def should_use_thinking(
    config: ThinkingConfig, context_length: int, is_complex_task: bool = False
) -> bool:
    """Determine if thinking should be used for current context.

    Args:
        config: Thinking configuration.
        context_length: Current context length in tokens/messages.
        is_complex_task: Whether the task is complex.

    Returns:
        True if thinking should be used.
    """
    if config.level == ThinkLevel.OFF:
        return False

    # If context is below minimum, only think if complex (for LOW/MEDIUM)
    if context_length < config.min_context_for_thinking:
        if config.level == ThinkLevel.LOW:
            return is_complex_task
        if config.level == ThinkLevel.MEDIUM:
            return is_complex_task
        return True  # HIGH always thinks

    # Above minimum context threshold
    if config.level == ThinkLevel.LOW:
        return is_complex_task

    if config.level == ThinkLevel.MEDIUM:
        return True

    return True  # HIGH always thinks


def estimate_thinking_effort(
    level: ThinkLevel, context_length: int, is_complex_task: bool = False
) -> str:
    """Estimate the thinking effort level.

    Args:
        level: The thinking level.
        context_length: Current context length.
        is_complex_task: Whether the task is complex.

    Returns:
        Effort description.
    """
    if level == ThinkLevel.OFF:
        return "none"

    if level == ThinkLevel.LOW:
        return "minimal" if not is_complex_task else "moderate"

    if level == ThinkLevel.MEDIUM:
        return "moderate" if context_length < 10 else "thorough"

    return "comprehensive"
