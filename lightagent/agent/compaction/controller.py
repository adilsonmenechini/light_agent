"""Session compaction controller for managing context optimization."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .config import CompactionConfig, CompactionStrategy, default_compaction_config
from .strategies import (
    CompactionResult,
    CompactionStrategyBase,
    MergeStrategy,
    PruneStrategy,
    SemanticCompactionStrategy,
    SummarizeStrategy,
)


@dataclass
class CompactionStats:
    """Statistics for compaction operations."""

    total_compactions: int = 0
    total_tokens_saved: int = 0
    total_messages_compacted: int = 0
    last_compaction_size: int = 0
    last_compaction_time: Optional[str] = None


class SessionCompactor:
    """Controller for automatic session compaction.

    Monitors token usage and applies compaction strategies when needed
    to keep context within limits while preserving important information.
    """

    def __init__(
        self,
        config: Optional[CompactionConfig] = None,
        strategy: Optional[CompactionStrategyBase] = None,
    ):
        """Initialize the session compactor.

        Args:
            config: Compaction configuration.
            strategy: Compaction strategy to use.
        """
        self.config = config or default_compaction_config()
        self._strategy = strategy or self._get_strategy(self.config.strategy)
        self._message_count = 0
        self._stats = CompactionStats()

    def _get_strategy(self, strategy_type: CompactionStrategy) -> CompactionStrategyBase:
        """Get strategy instance from type.

        Args:
            strategy_type: Strategy type enum.

        Returns:
            Strategy instance.
        """
        strategies = {
            CompactionStrategy.SUMMARIZE: SummarizeStrategy(),
            CompactionStrategy.PRUNE: PruneStrategy(),
            CompactionStrategy.MERGE: MergeStrategy(),
            CompactionStrategy.SEMANTIC: SemanticCompactionStrategy(),
        }
        return strategies.get(strategy_type, SummarizeStrategy())

    @property
    def stats(self) -> CompactionStats:
        """Get compaction statistics."""
        return self._stats

    def check_needs_compaction(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int,
    ) -> bool:
        """Check if compaction is needed.

        Args:
            messages: Current messages.
            current_tokens: Current token count.

        Returns:
            True if compaction should be triggered.
        """
        if not self.config.enabled:
            return False

        # Check if over token limit
        if current_tokens >= self.config.max_tokens:
            return True

        # Check message count interval
        self._message_count += 1
        if self._message_count >= self.config.check_interval:
            self._message_count = 0
            # Check if approaching limit
            if current_tokens >= self.config.max_tokens * 0.8:
                return True

        return False

    def compact(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int,
    ) -> CompactionResult:
        """Compact messages to reduce token usage.

        Args:
            messages: Messages to compact.
            current_tokens: Current token count.

        Returns:
            CompactionResult with details.
        """
        if not self.config.enabled:
            return CompactionResult(
                success=True,
                original_count=len(messages),
                compacted_count=len(messages),
                tokens_saved=0,
                summary="Compaction disabled",
                preserved_indices=list(range(len(messages))),
            )

        # Ensure we have enough messages to compact
        if len(messages) < self.config.min_messages_preserve * 2:
            return CompactionResult(
                success=True,
                original_count=len(messages),
                compacted_count=len(messages),
                tokens_saved=0,
                summary="Not enough messages to compact",
                preserved_indices=list(range(len(messages))),
            )

        # Perform compaction
        result = self._strategy.compact(
            messages=messages,
            preserve_recent=self.config.preserve_recent,
            importance_threshold=self.config.importance_threshold,
        )

        # Update statistics
        if result.success:
            self._stats.total_compactions += 1
            self._stats.total_tokens_saved += result.tokens_saved
            self._stats.total_messages_compacted += result.original_count - result.compacted_count
            self._stats.last_compaction_size = result.compacted_count

        return result

    def should_compact(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int,
    ) -> bool:
        """Determine if compaction should run (for auto mode).

        Args:
            messages: Current messages.
            current_tokens: Current token count.

        Returns:
            True if compaction is recommended.
        """
        if not self.config.auto_compact:
            return False

        return self.check_needs_compaction(messages, current_tokens)

    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about current strategy.

        Returns:
            Dictionary with strategy details.
        """
        return {
            "strategy": self.config.strategy.value,
            "enabled": self.config.enabled,
            "max_tokens": self.config.max_tokens,
            "target_tokens": self.config.target_tokens,
            "preserve_recent": self.config.preserve_recent,
        }

    def estimate_tokens_for_messages(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate total tokens for messages.

        Args:
            messages: Messages to estimate.

        Returns:
            Total estimated token count.
        """
        return self._strategy.estimate_tokens("\n".join(m.get("content", "") for m in messages))

    def reset(self) -> None:
        """Reset compactor state."""
        self._message_count = 0

    def update_config(self, **kwargs: Any) -> None:
        """Update configuration.

        Args:
            **kwargs: Configuration fields to update.
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Update strategy if strategy type changed
        if "strategy" in kwargs:
            self._strategy = self._get_strategy(kwargs["strategy"])
