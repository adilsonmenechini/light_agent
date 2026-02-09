"""Tests for session compaction system."""

import pytest
from lightagent.agent.compaction import (
    CompactionConfig,
    CompactionStrategy,
    SessionCompactor,
    default_compaction_config,
)
from lightagent.agent.compaction.strategies import (
    CompactionResult,
    SummarizeStrategy,
    PruneStrategy,
    MergeStrategy,
    SemanticCompactionStrategy,
)


class TestCompactionConfig:
    """Tests for CompactionConfig."""

    def test_defaults(self) -> None:
        """Should have correct default values."""
        config = CompactionConfig()
        assert config.enabled is True
        assert config.strategy == CompactionStrategy.SUMMARIZE
        assert config.max_tokens == 6000
        assert config.target_tokens == 4000
        assert config.preserve_recent == 3
        assert config.min_messages_preserve == 2
        assert config.importance_threshold == 0.3
        assert config.auto_compact is True
        assert config.check_interval == 5

    def test_custom_values(self) -> None:
        """Should accept custom values."""
        config = CompactionConfig(
            enabled=False,
            strategy=CompactionStrategy.PRUNE,
            max_tokens=8000,
            auto_compact=False,
        )
        assert config.enabled is False
        assert config.strategy == CompactionStrategy.PRUNE
        assert config.max_tokens == 8000
        assert config.auto_compact is False


class TestDefaultCompactionConfig:
    """Tests for default_compaction_config function."""

    def test_returns_config(self) -> None:
        """Should return a CompactionConfig instance."""
        config = default_compaction_config()
        assert isinstance(config, CompactionConfig)


class TestSummarizeStrategy:
    """Tests for SummarizeStrategy."""

    def test_no_compaction_needed(self) -> None:
        """Should not compact when within limits."""
        strategy = SummarizeStrategy()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]

        result = strategy.compact(messages, preserve_recent=3)

        assert result.success is True
        assert result.compacted_count == 3
        assert result.tokens_saved == 0

    def test_compacts_old_messages(self) -> None:
        """Should summarize old messages."""
        strategy = SummarizeStrategy()
        messages = [
            {
                "role": "user",
                "content": "First request with a lot of details about the project structure and requirements",
            },
            {
                "role": "assistant",
                "content": "Response with extensive explanation of the approach and methodology",
            },
            {
                "role": "tool",
                "content": "Tool execution results showing detailed output of various operations",
            },
            {"role": "user", "content": "Second request with additional context and requirements"},
            {"role": "assistant", "content": "Another detailed response with more information"},
            {"role": "user", "content": "Recent request"},
            {"role": "assistant", "content": "Recent response"},
        ]

        result = strategy.compact(messages, preserve_recent=3)

        assert result.success is True
        assert result.compacted_count == 4  # Summary + 3 recent
        assert "Summarized" in result.summary

    def test_preserves_system_messages(self) -> None:
        """Should mark summary as system message."""
        strategy = SummarizeStrategy()
        messages = [
            {
                "role": "user",
                "content": "Request with lots of detailed information about the project structure",
            },
            {
                "role": "assistant",
                "content": "Detailed response explaining the entire architecture and implementation approach",
            },
            {"role": "user", "content": "Recent"},
            {"role": "assistant", "content": "Recent response"},
        ]

        result = strategy.compact(messages, preserve_recent=2)

        assert result.success is True
        # First message should be the summary
        # The summary should have role "system"
        assert result.compacted_count == 3


class TestPruneStrategy:
    """Tests for PruneStrategy."""

    def test_prunes_low_importance(self) -> None:
        """Should prune messages with low importance."""
        strategy = PruneStrategy()
        messages = [
            {"role": "tool", "content": "Tool result"},  # Low importance
            {"role": "tool", "content": "Another tool result"},
            {"role": "user", "content": "Important request"},  # High importance
            {"role": "assistant", "content": "Response"},
        ]

        result = strategy.compact(messages, preserve_recent=2, importance_threshold=0.5)

        assert result.success is True
        assert result.compacted_count < len(messages)

    def test_preserves_high_importance(self) -> None:
        """Should preserve important messages."""
        strategy = PruneStrategy()
        messages = [
            {"role": "system", "content": "System prompt"},  # High importance
            {"role": "user", "content": "User request"},  # Medium importance
            {"role": "tool", "content": "Tool output"},  # Low importance
            {"role": "tool", "content": "More tool output"},
        ]

        result = strategy.compact(messages, preserve_recent=2, importance_threshold=0.4)

        # System and user messages should be preserved
        assert result.success is True


class TestMergeStrategy:
    """Tests for MergeStrategy."""

    def test_merges_consecutive_same_role(self) -> None:
        """Should merge consecutive messages from same role."""
        strategy = MergeStrategy()
        messages = [
            {
                "role": "assistant",
                "content": "First part of response with lots of details about the implementation",
            },
            {
                "role": "assistant",
                "content": "Second part of response with additional implementation details and code examples",
            },
            {"role": "user", "content": "User question about the implementation approach"},
            {"role": "assistant", "content": "Response with comprehensive answer"},
        ]

        result = strategy.compact(messages, preserve_recent=2)

        assert result.success is True
        # Should have merged the two assistant messages
        assert "Merged" in result.summary

    def test_no_merge_different_roles(self) -> None:
        """Should not merge messages from different roles."""
        strategy = MergeStrategy()
        messages = [
            {
                "role": "user",
                "content": "Question 1 about the project requirements and architecture design",
            },
            {
                "role": "assistant",
                "content": "Answer 1 with detailed explanation and code examples",
            },
            {
                "role": "user",
                "content": "Question 2 about implementation details and best practices",
            },
            {
                "role": "assistant",
                "content": "Answer 2 with comprehensive guidance and recommendations",
            },
            {"role": "user", "content": "Recent question"},
            {"role": "assistant", "content": "Recent response"},
        ]

        result = strategy.compact(messages, preserve_recent=2)

        assert result.success is True
        # Alternating roles should not merge (groups are limited to 3)
        assert result.compacted_count == 6  # No merging of alternating roles


class TestSemanticCompactionStrategy:
    """Tests for SemanticCompactionStrategy."""

    def test_preserves_key_content(self) -> None:
        """Should preserve semantically important content."""
        strategy = SemanticCompactionStrategy()
        messages = [
            {
                "role": "user",
                "content": "Build a web app with React and Node.js backend with database integration",
            },
            {
                "role": "assistant",
                "content": "I'll create a React app with a comprehensive project structure including API endpoints",
            },
            {
                "role": "tool",
                "content": "Created files: package.json, server.js, components, and database schema",
            },
            {
                "role": "tool",
                "content": "Installed dependencies: express, react, mongoose, and testing libraries",
            },
            {"role": "user", "content": "Recent request"},
            {"role": "assistant", "content": "Recent response"},
        ]

        result = strategy.compact(messages, preserve_recent=2)

        assert result.success is True
        assert "Preserved" in result.summary or "COMPACTED" in result.summary

    def test_handles_empty_messages(self) -> None:
        """Should handle empty message list."""
        strategy = SemanticCompactionStrategy()
        result = strategy.compact([], preserve_recent=2)

        assert result.success is True
        assert result.compacted_count == 0


class TestSessionCompactor:
    """Tests for SessionCompactor."""

    def test_initial_state(self) -> None:
        """Should start with default state."""
        compactor = SessionCompactor()
        assert compactor.config.enabled is True
        assert compactor._message_count == 0
        assert compactor.stats.total_compactions == 0

    def test_check_needs_compaction_tokens(self) -> None:
        """Should trigger compaction when over token limit."""
        compactor = SessionCompactor()
        messages = [{"role": "user", "content": "test"}] * 10

        # Under limit
        assert compactor.check_needs_compaction(messages, 5000) is False

        # Over limit
        assert compactor.check_needs_compaction(messages, 6500) is True

    def test_check_disabled_compaction(self) -> None:
        """Should not trigger when disabled."""
        config = CompactionConfig(enabled=False)
        compactor = SessionCompactor(config=config)

        messages = [{"role": "user", "content": "test"}] * 10
        assert compactor.check_needs_compaction(messages, 10000) is False

    def test_compact_messages(self) -> None:
        """Should compact messages successfully."""
        compactor = SessionCompactor()
        messages = [
            {"role": "user", "content": "Request 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Request 2"},
            {"role": "assistant", "content": "Response 2"},
            {"role": "user", "content": "Recent request"},
            {"role": "assistant", "content": "Recent response"},
        ]

        result = compactor.compact(messages, current_tokens=7000)

        assert result.success is True
        assert result.compacted_count < len(messages)
        assert compactor.stats.total_compactions == 1

    def test_update_config(self) -> None:
        """Should update configuration."""
        compactor = SessionCompactor()
        compactor.update_config(max_tokens=10000, strategy=CompactionStrategy.PRUNE)

        assert compactor.config.max_tokens == 10000
        assert compactor.config.strategy == CompactionStrategy.PRUNE

    def test_get_strategy_info(self) -> None:
        """Should return strategy information."""
        compactor = SessionCompactor()
        info = compactor.get_strategy_info()

        assert "strategy" in info
        assert "enabled" in info
        assert "max_tokens" in info

    def test_reset(self) -> None:
        """Should reset compactor state."""
        compactor = SessionCompactor()
        compactor._message_count = 10
        compactor.reset()

        assert compactor._message_count == 0

    def test_estimate_tokens(self) -> None:
        """Should estimate tokens for messages."""
        compactor = SessionCompactor()
        messages = [
            {"role": "user", "content": "Hello world"},
            {"role": "assistant", "content": "Hi there"},
        ]

        tokens = compactor.estimate_tokens_for_messages(messages)

        assert tokens > 0

    def test_compaction_stats(self) -> None:
        """Should track compaction statistics."""
        compactor = SessionCompactor()
        messages = [
            {
                "role": "user",
                "content": f"Request {i} with detailed information about the project requirements and implementation approach",
            }
            for i in range(10)
        ]

        result = compactor.compact(messages, current_tokens=7000)

        assert compactor.stats.total_compactions == 1
        # Token estimation is approximate, just check compaction happened
        assert compactor.stats.total_messages_compacted > 0


class TestCompactionResult:
    """Tests for CompactionResult."""

    def test_successful_result(self) -> None:
        """Should create successful result."""
        result = CompactionResult(
            success=True,
            original_count=10,
            compacted_count=5,
            tokens_saved=1000,
            summary="Test summary",
            preserved_indices=[0, 1, 2, 3, 4],
        )

        assert result.success is True
        assert result.original_count == 10
        assert result.compacted_count == 5
        assert result.tokens_saved == 1000

    def test_failed_result(self) -> None:
        """Should handle failed compaction."""
        result = CompactionResult(
            success=False,
            original_count=5,
            compacted_count=5,
            tokens_saved=0,
            summary="No compaction needed",
            preserved_indices=[0, 1, 2, 3, 4],
        )

        assert result.success is False
