"""Compaction strategies for session optimization."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class CompactionResult:
    """Result of a compaction operation."""

    success: bool
    original_count: int
    compacted_count: int
    tokens_saved: int
    summary: str
    preserved_indices: List[int]


class CompactionStrategyBase(ABC):
    """Base class for compaction strategies."""

    @abstractmethod
    def compact(
        self,
        messages: List[Dict[str, Any]],
        preserve_recent: int = 3,
        importance_threshold: float = 0.3,
    ) -> CompactionResult:
        """Compact messages using this strategy.

        Args:
            messages: List of messages to compact.
            preserve_recent: Number of recent messages to always keep.
            importance_threshold: Minimum importance to preserve.

        Returns:
            CompactionResult with details.
        """
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Text to estimate.

        Returns:
            Estimated token count.
        """
        pass

    def _calculate_importance(self, message: Dict[str, Any]) -> float:
        """Calculate importance score for a message.

        Args:
            message: Message to evaluate.

        Returns:
            Importance score between 0 and 1.
        """
        role = message.get("role", "")
        content = message.get("content", "")

        importance = 0.5  # Base importance

        # System messages are always important
        if role == "system":
            importance = 1.0

        # User requests are important
        elif role == "user":
            importance = 0.8
            # Check for key decision words
            if any(
                word in content.lower() for word in ["important", "remember", "always", "don't"]
            ):
                importance = 0.95

        # Assistant messages
        elif role == "assistant":
            importance = 0.6
            # Tool calls/results might be important
            if "tool_calls" in message or "tool_results" in message:
                importance = 0.7

        # Tool messages are less important if old
        elif role == "tool":
            importance = 0.4

        # Content length factor (very short messages are less important)
        if len(content) < 20:
            importance -= 0.1

        return max(0.0, min(1.0, importance))


class SummarizeStrategy(CompactionStrategyBase):
    """Strategy that summarizes old messages into a concise summary.

    Preserves recent messages and summarizes everything before them.
    """

    def compact(
        self,
        messages: List[Dict[str, Any]],
        preserve_recent: int = 3,
        importance_threshold: float = 0.3,
    ) -> CompactionResult:
        """Compact by summarizing old messages."""
        if len(messages) <= preserve_recent:
            return CompactionResult(
                success=True,
                original_count=len(messages),
                compacted_count=len(messages),
                tokens_saved=0,
                summary="No compaction needed - within limits",
                preserved_indices=list(range(len(messages))),
            )

        recent_messages = messages[-preserve_recent:]
        old_messages = messages[:-preserve_recent]

        # Create summary of old messages
        summary_content = self._create_summary(old_messages)

        # Create summary message
        summary_message = {
            "role": "system",
            "content": f"[COMPACTED HISTORY SUMMARY]\n{summary_content}\n[/COMPACTED HISTORY SUMMARY]",
            "_compacted": True,
            "_original_count": len(old_messages),
        }

        compacted = [summary_message] + recent_messages

        original_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in messages)
        new_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in compacted)

        return CompactionResult(
            success=True,
            original_count=len(messages),
            compacted_count=len(compacted),
            tokens_saved=original_tokens - new_tokens,
            summary=f"Summarized {len(old_messages)} messages into one summary",
            preserved_indices=[0] + list(range(len(messages) - preserve_recent, len(messages))),
        )

    def _create_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Create a summary of messages.

        Args:
            messages: Messages to summarize.

        Returns:
            Summary string.
        """
        if not messages:
            return "No previous conversation."

        # Extract key information
        user_requests = []
        decisions = []
        tools_used = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                # Get first 100 chars as preview
                preview = content[:100] + ("..." if len(content) > 100 else "")
                user_requests.append(preview)

            elif role == "assistant" and any(
                word in content.lower() for word in ["decided", "concluded", "agreed", "will"]
            ):
                decisions.append(content[:150])

            elif role == "tool":
                tool_name = msg.get("tool_name", "unknown")
                tools_used.append(tool_name)

        parts = []

        if user_requests:
            parts.append(f"User requests: {'; '.join(user_requests[:3])}")

        if decisions:
            parts.append(f"Decisions made: {'; '.join(decisions[:2])}")

        if tools_used:
            unique_tools = list(set(tools_used))
            parts.append(f"Tools used: {', '.join(unique_tools[:5])}")

        return " | ".join(parts) if parts else "General conversation."

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using simple word-based approximation."""
        if not text:
            return 0
        # Rough estimate: 4 chars per token on average
        return len(text) // 4


class PruneStrategy(CompactionStrategyBase):
    """Strategy that removes oldest messages while preserving recent ones.

    Simply drops messages from the beginning until within limits.
    """

    def compact(
        self,
        messages: List[Dict[str, Any]],
        preserve_recent: int = 3,
        importance_threshold: float = 0.3,
    ) -> CompactionResult:
        """Compact by pruning oldest messages."""
        if len(messages) <= preserve_recent:
            return CompactionResult(
                success=True,
                original_count=len(messages),
                compacted_count=len(messages),
                tokens_saved=0,
                summary="No compaction needed - within limits",
                preserved_indices=list(range(len(messages))),
            )

        # Remove oldest messages while respecting importance threshold
        compacted = list(messages)
        preserved_indices = list(range(len(messages)))

        for i, msg in enumerate(messages):
            if len(compacted) <= preserve_recent:
                break

            importance = self._calculate_importance(msg)

            if importance < importance_threshold:
                # Remove this message
                compacted.pop(0)
                preserved_indices.pop(0)

        # If still too many, remove oldest regardless
        while len(compacted) > preserve_recent * 2:
            compacted.pop(0)
            preserved_indices.pop(0)

        original_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in messages)
        new_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in compacted)

        return CompactionResult(
            success=True,
            original_count=len(messages),
            compacted_count=len(compacted),
            tokens_saved=original_tokens - new_tokens,
            summary=f"Pruned {len(messages) - len(compacted)} messages",
            preserved_indices=preserved_indices,
        )

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        return len(text) // 4 if text else 0


class MergeStrategy(CompactionStrategyBase):
    """Strategy that merges similar consecutive messages.

    Combines redundant or related messages into single entries.
    """

    def compact(
        self,
        messages: List[Dict[str, Any]],
        preserve_recent: int = 3,
        importance_threshold: float = 0.3,
    ) -> CompactionResult:
        """Compact by merging similar messages."""
        if len(messages) <= preserve_recent:
            return CompactionResult(
                success=True,
                original_count=len(messages),
                compacted_count=len(messages),
                tokens_saved=0,
                summary="No compaction needed - within limits",
                preserved_indices=list(range(len(messages))),
            )

        recent_messages = messages[-preserve_recent:]
        old_messages = messages[:-preserve_recent]

        merged = self._merge_messages(old_messages)
        compacted = merged + recent_messages

        original_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in messages)
        new_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in compacted)

        return CompactionResult(
            success=True,
            original_count=len(messages),
            compacted_count=len(compacted),
            tokens_saved=original_tokens - new_tokens,
            summary=f"Merged {len(old_messages)} messages into {len(merged)}",
            preserved_indices=list(range(len(merged), len(merged) + preserve_recent)),
        )

    def _merge_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge similar consecutive messages.

        Args:
            messages: Messages to merge.

        Returns:
            Merged messages.
        """
        if not messages:
            return []

        merged = []
        current_group = []
        current_role = None

        for msg in messages:
            role = msg.get("role", "")

            if role == current_role and len(current_group) < 3:
                # Same role, add to group
                current_group.append(msg)
            else:
                # Different role or group too large, flush current
                if current_group:
                    merged.append(self._combine_group(current_group))
                current_group = [msg]
                current_role = role

        # Flush remaining
        if current_group:
            merged.append(self._combine_group(current_group))

        return merged

    def _combine_group(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine a group of similar messages.

        Args:
            messages: Messages to combine.

        Returns:
            Combined message.
        """
        role = messages[0].get("role", "assistant")

        # Concatenate contents
        contents = []
        for msg in messages:
            content = msg.get("content", "")
            if content:
                contents.append(content)

        combined_content = "\n---\n".join(contents)

        return {
            "role": role,
            "content": f"[MERGED {len(messages)} messages]\n{combined_content}\n[/MERGED]",
            "_merged": True,
            "_original_count": len(messages),
        }

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        return len(text) // 4 if text else 0


class SemanticCompactionStrategy(CompactionStrategyBase):
    """Strategy that uses semantic analysis to preserve important content.

    Analyzes content to determine what information is critical vs redundant.
    """

    def compact(
        self,
        messages: List[Dict[str, Any]],
        preserve_recent: int = 3,
        importance_threshold: float = 0.3,
    ) -> CompactionResult:
        """Compact using semantic importance analysis."""
        if len(messages) <= preserve_recent:
            return CompactionResult(
                success=True,
                original_count=len(messages),
                compacted_count=len(messages),
                tokens_saved=0,
                summary="No compaction needed - within limits",
                preserved_indices=list(range(len(messages))),
            )

        # Calculate importance for each message
        scored_messages = []
        for i, msg in enumerate(messages):
            importance = self._calculate_importance(msg)
            scored_messages.append((i, msg, importance))

        # Separate recent and old
        recent = scored_messages[-preserve_recent:]
        old = scored_messages[:-preserve_recent]

        # For old messages, filter by importance
        important_old = [(i, msg, imp) for i, msg, imp in old if imp >= importance_threshold]

        # Combine high-importance old messages
        if important_old:
            summary = self._create_semantic_summary([msg for _, msg, _ in important_old])
            summary_msg = {
                "role": "system",
                "content": f"[PRESERVED IMPORTANT CONTENT]\n{summary}\n[/PRESERVED IMPORTANT CONTENT]",
                "_compacted": True,
                "_preserved_count": len(important_old),
            }
            compacted = [summary_msg] + [msg for _, msg, _ in recent]
        else:
            compacted = [msg for _, msg, _ in recent]

        original_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in messages)
        new_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in compacted)

        return CompactionResult(
            success=True,
            original_count=len(messages),
            compacted_count=len(compacted),
            tokens_saved=original_tokens - new_tokens,
            summary=f"Preserved {len(important_old)} important messages from history",
            preserved_indices=[
                len(compacted) - preserve_recent + i for i in range(preserve_recent)
            ],
        )

    def _create_semantic_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Create semantic summary preserving key information.

        Args:
            messages: Messages to summarize.

        Returns:
            Semantic summary.
        """
        key_points = []
        entities = set()
        actions = []

        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "")

            # Extract key points
            if role == "user":
                # First line is usually the main request
                lines = content.split("\n")
                if lines:
                    key_points.append(f"User requested: {lines[0][:100]}")
            elif role == "assistant":
                if any(word in content.lower() for word in ["here's", "i'll", "i have"]):
                    actions.append(content[:100])
            elif role == "tool":
                tool_name = msg.get("tool_name", "tool")
                actions.append(f"Used {tool_name}")

        parts = []
        if key_points:
            parts.append(" | ".join(key_points[:2]))
        if actions:
            parts.append("Actions: " + ", ".join(actions[:3]))

        return " | ".join(parts) if parts else "Previous context"

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        return len(text) // 4 if text else 0
