"""Memory consolidation for promoting insights to long-term memory."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
import os


@dataclass
class MemoryEntry:
    """Represents an entry in long-term memory."""

    timestamp: str
    category: str
    insight: str
    importance: float
    source: str  # tool_name that created it
    tags: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Convert to markdown format."""
        tags_str = ", ".join(self.tags) if self.tags else ""
        return f"""## {self.timestamp} - {self.category}

**Importance:** {self.importance:.2f}

**Insight:** {self.insight}

**Source:** {self.source}

**Tags:** {tags_str}
"""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "category": self.category,
            "insight": self.insight,
            "importance": self.importance,
            "source": self.source,
            "tags": self.tags or [],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            category=data["category"],
            insight=data["insight"],
            importance=data["importance"],
            source=data["source"],
            tags=data.get("tags", []),
        )


@dataclass
class ConsolidationConfig:
    """Configuration for memory consolidation."""

    memory_file_path: str = "workspace/memory/MEMORY.md"
    importance_threshold: float = 0.7
    max_entries: int = 100
    auto_consolidate: bool = True
    format: str = "markdown"  # markdown or json


class MemoryConsolidator:
    """Consolidates important observations to long-term memory."""

    def __init__(self, config: Optional[ConsolidationConfig] = None):
        """Initialize the consolidator.

        Args:
            config: Configuration for consolidation.
        """
        self.config = config or ConsolidationConfig()
        self._entries: list[MemoryEntry] = []
        self._pending: list[MemoryEntry] = []

    def should_consolidate(self, importance: float, category: str) -> bool:
        """Check if an observation should be consolidated.

        Args:
            importance: The importance score (0-1).
            category: The observation category.

        Returns:
            True if should be consolidated.
        """
        # Always consolidate critical or high importance
        if importance >= 0.8:
            return True

        # Consolidate above threshold
        return importance >= self.config.importance_threshold

    def add_for_consolidation(self, entry: MemoryEntry) -> None:
        """Add an entry to the pending consolidation queue.

        Args:
            entry: The memory entry to add.
        """
        self._pending.append(entry)

    def process_pending(self) -> list[MemoryEntry]:
        """Process pending entries and return consolidated ones.

        Returns:
            List of entries that were consolidated.
        """
        consolidated: list[MemoryEntry] = []

        for entry in self._pending:
            if self.should_consolidate(entry.importance, entry.category):
                self._entries.append(entry)
                consolidated.append(entry)

        # Clear pending
        self._pending = []

        # Trim old entries if over limit
        if len(self._entries) > self.config.max_entries:
            # Keep most important entries
            self._entries.sort(key=lambda x: x.importance, reverse=True)
            self._entries = self._entries[: self.config.max_entries]

        return consolidated

    def consolidate(
        self,
        insight: str,
        category: str,
        importance: float,
        source: str,
        tags: Optional[list[str]] = None,
    ) -> bool:
        """Consolidate an observation to memory.

        Args:
            insight: The observation insight.
            category: The category.
            importance: The importance score (0-1).
            source: The tool that created this.
            tags: Optional tags.

        Returns:
            True if consolidated, False if skipped.
        """
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            category=category,
            insight=insight,
            importance=importance,
            source=source,
            tags=tags or [],
        )

        if self.should_consolidate(importance, category):
            self._entries.append(entry)
            # Trim if over limit
            if len(self._entries) > self.config.max_entries:
                # Keep most important entries
                self._entries.sort(key=lambda x: x.importance, reverse=True)
                self._entries = self._entries[: self.config.max_entries]
            return True

        return False

    def save_to_file(self, base_path: Optional[str] = None) -> None:
        """Save consolidated memory to file.

        Args:
            base_path: Base path for the memory file.
        """
        if not self._entries:
            return

        path = Path(base_path or self.config.memory_file_path)

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        if self.config.format == "markdown":
            self._save_markdown(path)
        else:
            self._save_json(path)

    def _save_markdown(self, path: Path) -> None:
        """Save entries in markdown format."""
        # Sort by timestamp, newest first
        sorted_entries = sorted(self._entries, key=lambda x: x.timestamp, reverse=True)

        lines = [
            "# Memory",
            "",
            f"Last updated: {datetime.now().isoformat()}",
            "",
            f"Total entries: {len(sorted_entries)}",
            "",
            "---",
            "",
        ]

        for entry in sorted_entries:
            lines.append(entry.to_markdown())
            lines.append("")

        path.write_text("\n".join(lines))

    def _save_json(self, path: Path) -> None:
        """Save entries in JSON format."""
        data = {
            "last_updated": datetime.now().isoformat(),
            "total_entries": len(self._entries),
            "entries": [e.to_dict() for e in self._entries],
        }
        path.write_text(json.dumps(data, indent=2))

    def load_from_file(self, base_path: Optional[str] = None) -> None:
        """Load entries from file.

        Args:
            base_path: Base path for the memory file.
        """
        path = Path(base_path or self.config.memory_file_path)

        if not path.exists():
            return

        if path.suffix == ".json":
            self._load_json(path)
        else:
            self._load_markdown(path)

    def _load_json(self, path: Path) -> None:
        """Load entries from JSON."""
        try:
            data = json.loads(path.read_text())
            self._entries = [MemoryEntry.from_dict(e) for e in data.get("entries", [])]
        except (json.JSONDecodeError, KeyError):
            pass

    def _load_markdown(self, path: Path) -> None:
        """Load entries from markdown."""
        # Simplified: just clear entries for now
        # A full parser would extract entries from the markdown
        self._entries = []

    def get_all_entries(self) -> list[MemoryEntry]:
        """Get all consolidated entries."""
        return sorted(self._entries, key=lambda x: x.timestamp, reverse=True)

    def get_by_category(self, category: str) -> list[MemoryEntry]:
        """Get entries by category."""
        return [e for e in self._entries if e.category == category]

    def get_high_importance(self, threshold: float = 0.7) -> list[MemoryEntry]:
        """Get high importance entries."""
        return [e for e in self._entries if e.importance >= threshold]

    def search(self, query: str) -> list[MemoryEntry]:
        """Search entries by insight content."""
        query_lower = query.lower()
        return [e for e in self._entries if query_lower in e.insight.lower()]

    def count(self) -> int:
        """Get total entry count."""
        return len(self._entries)

    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()
        self._pending.clear()


def create_memory_entry(
    insight: str, category: str, importance: float, source: str, tags: Optional[list[str]] = None
) -> MemoryEntry:
    """Helper to create a memory entry.

    Args:
        insight: The observation insight.
        category: The category.
        importance: The importance score (0-1).
        source: The tool that created this.
        tags: Optional tags.

    Returns:
        A new MemoryEntry.
    """
    return MemoryEntry(
        timestamp=datetime.now().isoformat(),
        category=category,
        insight=insight,
        importance=importance,
        source=source,
        tags=tags or [],
    )
