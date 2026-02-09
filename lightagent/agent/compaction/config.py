"""Configuration for session compaction."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CompactionStrategy(Enum):
    """Available compaction strategies."""

    SUMMARIZE = "summarize"  # Summarize old messages into a single summary
    PRUNE = "prune"  # Remove oldest messages
    MERGE = "merge"  # Merge similar consecutive messages
    SEMANTIC = "semantic"  # Use semantic analysis to preserve important content


@dataclass
class CompactionConfig:
    """Configuration for session compaction behavior.

    Attributes:
        enabled: Whether compaction is enabled.
        strategy: Compaction strategy to use.
        max_tokens: Maximum tokens before triggering compaction.
        target_tokens: Target token count after compaction.
        preserve_recent: Number of recent messages to always preserve.
        min_messages_preserve: Minimum messages to always keep.
        importance_threshold: Minimum importance score to preserve a message.
        summarize_prompt: Prompt template for summarization.
        auto_compact: Whether to automatically compact when threshold is reached.
        check_interval: How often to check for compaction needs (in messages).
    """

    enabled: bool = True
    strategy: CompactionStrategy = CompactionStrategy.SUMMARIZE
    max_tokens: int = 6000
    target_tokens: int = 4000
    preserve_recent: int = 3
    min_messages_preserve: int = 2
    importance_threshold: float = 0.3
    summarize_prompt: str = (
        "Summarize this conversation history into a concise paragraph. "
        "Preserve: key decisions, user preferences, important facts, and goals. "
        "Remove: redundant clarifications, obsolete details, and repetitive info.\n\n"
        "History:\n{content}"
    )
    auto_compact: bool = True
    check_interval: int = 5


def default_compaction_config() -> CompactionConfig:
    """Get default compaction configuration."""
    return CompactionConfig()
