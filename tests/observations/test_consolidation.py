"""Tests for memory consolidation."""

import pytest
import tempfile
from pathlib import Path
from lightagent.agent.observations import (
    MemoryEntry,
    ConsolidationConfig,
    MemoryConsolidator,
    create_memory_entry,
)


class TestMemoryEntry:
    """Tests for MemoryEntry class."""

    def test_to_markdown(self) -> None:
        """Should convert to markdown format."""
        entry = MemoryEntry(
            timestamp="2024-01-15T10:30:00",
            category="bug",
            insight="Found critical bug in auth",
            importance=0.9,
            source="grep",
            tags=["security", "auth"],
        )
        md = entry.to_markdown()
        assert "2024-01-15T10:30:00" in md
        assert "bug" in md
        assert "Found critical bug in auth" in md
        assert "0.90" in md
        assert "grep" in md
        assert "security" in md

    def test_to_dict(self) -> None:
        """Should convert to dictionary."""
        entry = MemoryEntry(
            timestamp="2024-01-15T10:30:00",
            category="config",
            insight="Database config updated",
            importance=0.7,
            source="read_file",
            tags=["database"],
        )
        data = entry.to_dict()
        assert data["timestamp"] == "2024-01-15T10:30:00"
        assert data["category"] == "config"
        assert data["insight"] == "Database config updated"
        assert data["importance"] == 0.7
        assert data["source"] == "read_file"
        assert data["tags"] == ["database"]

    def test_from_dict(self) -> None:
        """Should create from dictionary."""
        data = {
            "timestamp": "2024-01-15T10:30:00",
            "category": "config",
            "insight": "Updated settings",
            "importance": 0.6,
            "source": "edit",
            "tags": ["settings"],
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.timestamp == "2024-01-15T10:30:00"
        assert entry.category == "config"
        assert entry.importance == 0.6


class TestConsolidationConfig:
    """Tests for ConsolidationConfig."""

    def test_defaults(self) -> None:
        """Should have correct defaults."""
        config = ConsolidationConfig()
        assert config.memory_file_path == "workspace/memory/MEMORY.md"
        assert config.importance_threshold == 0.7
        assert config.max_entries == 100
        assert config.auto_consolidate is True
        assert config.format == "markdown"

    def test_custom_values(self) -> None:
        """Should accept custom values."""
        config = ConsolidationConfig(
            memory_file_path="/custom/path.md",
            importance_threshold=0.8,
            max_entries=50,
            format="json",
        )
        assert config.memory_file_path == "/custom/path.md"
        assert config.importance_threshold == 0.8
        assert config.max_entries == 50
        assert config.format == "json"


class TestMemoryConsolidator:
    """Tests for MemoryConsolidator class."""

    def test_should_consolidate_high_importance(self) -> None:
        """Should consolidate high importance observations."""
        consolidator = MemoryConsolidator()
        assert consolidator.should_consolidate(0.9, "bug") is True
        assert consolidator.should_consolidate(0.85, "security") is True

    def test_should_consolidate_above_threshold(self) -> None:
        """Should consolidate above threshold."""
        consolidator = MemoryConsolidator(ConsolidationConfig(importance_threshold=0.6))
        assert consolidator.should_consolidate(0.7, "info") is True

    def test_should_not_consolidate_below_threshold(self) -> None:
        """Should not consolidate below threshold."""
        consolidator = MemoryConsolidator()
        assert consolidator.should_consolidate(0.5, "info") is False
        assert consolidator.should_consolidate(0.3, "info") is False

    def test_consolidate_adds_entry(self) -> None:
        """Should add entry when consolidated."""
        consolidator = MemoryConsolidator()
        result = consolidator.consolidate(
            insight="Found bug in code",
            category="bug",
            importance=0.8,
            source="grep",
        )
        assert result is True
        assert consolidator.count() == 1

    def test_consolidate_skips_low_importance(self) -> None:
        """Should skip low importance entries."""
        consolidator = MemoryConsolidator()
        result = consolidator.consolidate(
            insight="Minor log message",
            category="info",
            importance=0.2,
            source="exec",
        )
        assert result is False
        assert consolidator.count() == 0

    def test_process_pending(self) -> None:
        """Should process pending entries."""
        consolidator = MemoryConsolidator()
        entry = create_memory_entry(
            insight="Important discovery",
            category="config",
            importance=0.75,
            source="read_file",
        )
        consolidator.add_for_consolidation(entry)
        consolidated = consolidator.process_pending()
        assert len(consolidated) == 1
        assert consolidator.count() == 1

    def test_get_all_entries(self) -> None:
        """Should return all entries sorted."""
        consolidator = MemoryConsolidator()
        consolidator.consolidate("Insight 1", "bug", 0.5, "exec")
        consolidator.consolidate("Insight 2", "config", 0.8, "read_file")
        consolidator.consolidate("Insight 3", "bug", 0.9, "grep")

        entries = consolidator.get_all_entries()
        assert len(entries) == 2  # Only high importance
        # Most important first
        assert entries[0].importance >= entries[1].importance

    def test_get_by_category(self) -> None:
        """Should filter by category."""
        consolidator = MemoryConsolidator(ConsolidationConfig(importance_threshold=0.1))
        consolidator.consolidate("Bug 1", "bug", 0.5, "exec")
        consolidator.consolidate("Config 1", "config", 0.5, "exec")
        consolidator.consolidate("Bug 2", "bug", 0.5, "exec")

        bugs = consolidator.get_by_category("bug")
        assert len(bugs) == 2

    def test_get_high_importance(self) -> None:
        """Should filter by importance threshold."""
        consolidator = MemoryConsolidator(ConsolidationConfig(importance_threshold=0.1))
        consolidator.consolidate("Low", "info", 0.2, "exec")
        consolidator.consolidate("High", "bug", 0.9, "exec")
        consolidator.consolidate("Medium", "config", 0.5, "exec")

        high = consolidator.get_high_importance(0.7)
        assert len(high) == 1
        assert high[0].insight == "High"

    def test_search(self) -> None:
        """Should search by content."""
        consolidator = MemoryConsolidator(ConsolidationConfig(importance_threshold=0.1))
        consolidator.consolidate("Database connection", "config", 0.5, "exec")
        consolidator.consolidate("API endpoint", "config", 0.5, "exec")
        consolidator.consolidate("User login", "security", 0.5, "exec")

        results = consolidator.search("database")
        assert len(results) == 1
        assert "Database" in results[0].insight

    def test_save_and_load_json(self) -> None:
        """Should save and load JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "memory.json"
            consolidator = MemoryConsolidator(
                ConsolidationConfig(memory_file_path=str(path), format="json")
            )
            consolidator.consolidate("Test insight", "bug", 0.8, "exec")
            consolidator.save_to_file()

            # Load in new consolidator
            new_consolidator = MemoryConsolidator(
                ConsolidationConfig(memory_file_path=str(path), format="json")
            )
            new_consolidator.load_from_file()

            assert new_consolidator.count() == 1
            entry = new_consolidator.get_all_entries()[0]
            assert entry.insight == "Test insight"

    def test_max_entries_limit(self) -> None:
        """Should limit entries when over max."""
        consolidator = MemoryConsolidator(
            ConsolidationConfig(max_entries=3, importance_threshold=0.1)
        )
        for i in range(5):
            consolidator.consolidate(f"Insight {i}", "bug", 0.5, "exec")

        assert consolidator.count() == 3

    def test_clear(self) -> None:
        """Should clear all entries."""
        consolidator = MemoryConsolidator()
        consolidator.consolidate("Test", "bug", 0.8, "exec")
        assert consolidator.count() == 1

        consolidator.clear()
        assert consolidator.count() == 0


class TestCreateMemoryEntry:
    """Tests for create_memory_entry helper."""

    def test_create_entry(self) -> None:
        """Should create a memory entry."""
        entry = create_memory_entry(
            insight="Test insight",
            category="config",
            importance=0.7,
            source="read_file",
            tags=["test"],
        )
        assert isinstance(entry, MemoryEntry)
        assert entry.insight == "Test insight"
        assert entry.category == "config"
        assert entry.importance == 0.7
        assert entry.source == "read_file"
        assert entry.tags == ["test"]

    def test_create_entry_without_tags(self) -> None:
        """Should create entry without tags."""
        entry = create_memory_entry(
            insight="No tags",
            category="info",
            importance=0.5,
            source="exec",
        )
        assert entry.tags is None or entry.tags == []
