"""Tests for context awareness."""

import pytest
from datetime import datetime, timedelta
from lightagent.agent.observations import (
    Observation,
    ContextMatch,
    ContextAwareObservationStore,
    extract_context_tags,
    detect_temporal_relation,
    detect_causal_relation,
    are_related,
)


class TestExtractContextTags:
    """Tests for extract_context_tags function."""

    def test_extract_file_paths(self) -> None:
        """Should detect file path references."""
        text = "Read file: /Users/test/config.yaml and src/main.py"
        tags = extract_context_tags(text)
        assert "file_references" in tags

    def test_extract_error_types(self) -> None:
        """Should detect error type references."""
        text = "ValueError: invalid argument at line 42"
        tags = extract_context_tags(text)
        assert "has_error" in tags

    def test_extract_config_keys(self) -> None:
        """Should detect configuration keys."""
        text = "Set timeout=30, max_retries=3, database_url=postgres://..."
        tags = extract_context_tags(text)
        assert "has_config" in tags

    def test_extract_function_refs(self) -> None:
        """Should detect function references."""
        text = "def hello(): print('world')"
        tags = extract_context_tags(text)
        assert "has_function_ref" in tags

    def test_extract_line_refs(self) -> None:
        """Should detect line number references."""
        text = "Error at line 42:42"
        tags = extract_context_tags(text)
        assert "line_references" in tags

    def test_empty_text(self) -> None:
        """Should handle empty text."""
        tags = extract_context_tags("")
        assert len(tags) == 0

    def test_multiple_tags(self) -> None:
        """Should extract multiple tags."""
        text = "ValueError in config.yaml at line 10: timeout=30"
        tags = extract_context_tags(text)
        assert len(tags) >= 3
        assert "has_error" in tags
        assert "file_references" in tags
        assert "has_config" in tags


class TestDetectTemporalRelation:
    """Tests for detect_temporal_relation function."""

    def test_before_relation(self) -> None:
        """Should detect 'before' relation."""
        assert detect_temporal_relation("This was before the crash") == "before"
        assert detect_temporal_relation("I checked earlier") == "before"
        assert detect_temporal_relation("Previously we had") == "before"

    def test_after_relation(self) -> None:
        """Should detect 'after' relation."""
        assert detect_temporal_relation("After the update") == "after"
        assert detect_temporal_relation("Later we found") == "after"
        assert detect_temporal_relation("Next step is") == "after"

    def test_simultaneous_relation(self) -> None:
        """Should detect simultaneous relation."""
        assert detect_temporal_relation("Currently processing") == "simultaneous"
        assert detect_temporal_relation("Now executing") == "simultaneous"

    def test_no_relation(self) -> None:
        """Should return None when no relation."""
        assert detect_temporal_relation("The file is missing") is None


class TestDetectCausalRelation:
    """Tests for detect_causal_relation function."""

    def test_causal_relation(self) -> None:
        """Should detect causal relations."""
        assert detect_causal_relation("This happened because of X") == "causal"
        assert detect_causal_relation("The error resulted in") == "causal"
        assert detect_causal_relation("Therefore we conclude") == "causal"

    def test_contrast_relation(self) -> None:
        """Should detect contrast relations."""
        assert detect_causal_relation("But this failed") == "contrast"
        assert detect_causal_relation("However the test passed") == "contrast"
        assert detect_causal_relation("Although we tried") == "contrast"

    def test_no_relation(self) -> None:
        """Should return None when no relation."""
        assert detect_causal_relation("The file was read") is None


class TestAreRelated:
    """Tests for are_related function."""

    def test_temporal_proximity(self) -> None:
        """Should detect temporal proximity."""
        obs1 = Observation(
            id="1",
            insight="Test 1",
            category="test",
            importance=0.5,
            timestamp=datetime.now(),
            tool_name="exec",
        )
        obs2 = Observation(
            id="2",
            insight="Test 2",
            category="test",
            importance=0.5,
            timestamp=datetime.now() - timedelta(hours=1),
            tool_name="exec",
        )
        matches = are_related(obs1, obs2, time_window_hours=24.0)
        assert len(matches) >= 1
        temporal = [m for m in matches if m.match_type == "temporal"]
        assert len(temporal) == 1

    def test_same_category(self) -> None:
        """Should detect same category."""
        obs1 = Observation(
            id="1",
            insight="Test",
            category="bug",
            importance=0.5,
            timestamp=datetime.now(),
            tool_name="exec",
        )
        obs2 = Observation(
            id="2",
            insight="Test",
            category="bug",
            importance=0.5,
            timestamp=datetime.now(),
            tool_name="exec",
        )
        matches = are_related(obs1, obs2)
        category = [m for m in matches if m.match_type == "category"]
        assert len(category) == 1

    def test_different_category(self) -> None:
        """Should not match different categories."""
        obs1 = Observation(
            id="1",
            insight="Test",
            category="bug",
            importance=0.5,
            timestamp=datetime.now(),
            tool_name="exec",
        )
        obs2 = Observation(
            id="2",
            insight="Test",
            category="info",
            importance=0.5,
            timestamp=datetime.now(),
            tool_name="exec",
        )
        matches = are_related(obs1, obs2)
        category = [m for m in matches if m.match_type == "category"]
        assert len(category) == 0

    def test_same_tool(self) -> None:
        """Should detect same tool."""
        obs1 = Observation(
            id="1",
            insight="Test",
            category="info",
            importance=0.5,
            timestamp=datetime.now(),
            tool_name="read_file",
        )
        obs2 = Observation(
            id="2",
            insight="Test",
            category="info",
            importance=0.5,
            timestamp=datetime.now(),
            tool_name="read_file",
        )
        matches = are_related(obs1, obs2)
        tool = [m for m in matches if m.match_type == "tool"]
        assert len(tool) == 1

    def test_context_tags(self) -> None:
        """Should detect common context tags."""
        obs1 = Observation(
            id="1",
            insight="Error in config.yaml",
            category="bug",
            importance=0.8,
            timestamp=datetime.now(),
            tool_name="exec",
            context_tags=["file_references", "has_error"],
        )
        obs2 = Observation(
            id="2",
            insight="Fix config.yaml",
            category="config",
            importance=0.5,
            timestamp=datetime.now(),
            tool_name="write_file",
            context_tags=["file_references"],
        )
        matches = are_related(obs1, obs2)
        context = [m for m in matches if m.match_type == "context"]
        assert len(context) == 1


class TestContextAwareObservationStore:
    """Tests for ContextAwareObservationStore class."""

    def test_add_observation(self) -> None:
        """Should add observation and find related ones."""
        store = ContextAwareObservationStore()
        obs = Observation(
            id="1",
            insight="Found bug in main.py",
            category="bug",
            importance=0.8,
            timestamp=datetime.now(),
            tool_name="grep",
        )
        store.add(obs)
        assert store.count() == 1

    def test_get_related(self) -> None:
        """Should return related observations."""
        store = ContextAwareObservationStore()
        obs1 = Observation(
            id="1",
            insight="Error in config.yaml",
            category="bug",
            importance=0.8,
            timestamp=datetime.now(),
            tool_name="grep",
            context_tags=["file_references"],
        )
        obs2 = Observation(
            id="2",
            insight="Fixed config.yaml",
            category="config",
            importance=0.6,
            timestamp=datetime.now(),
            tool_name="edit",
            context_tags=["file_references"],
        )
        store.add(obs1)
        store.add(obs2)

        related = store.get_related("1")
        assert len(related) >= 1

    def test_get_by_category(self) -> None:
        """Should filter by category."""
        store = ContextAwareObservationStore()
        store.add(
            Observation(
                id="1",
                insight="Bug 1",
                category="bug",
                importance=0.5,
                timestamp=datetime.now(),
                tool_name="exec",
            )
        )
        store.add(
            Observation(
                id="2",
                insight="Bug 2",
                category="bug",
                importance=0.5,
                timestamp=datetime.now(),
                tool_name="exec",
            )
        )
        store.add(
            Observation(
                id="3",
                insight="Info 1",
                category="info",
                importance=0.5,
                timestamp=datetime.now(),
                tool_name="exec",
            )
        )

        bugs = store.get_by_category("bug")
        assert len(bugs) == 2

    def test_get_high_importance(self) -> None:
        """Should filter by importance."""
        store = ContextAwareObservationStore()
        store.add(
            Observation(
                id="1",
                insight="High",
                category="bug",
                importance=0.9,
                timestamp=datetime.now(),
                tool_name="exec",
            )
        )
        store.add(
            Observation(
                id="2",
                insight="Low",
                category="info",
                importance=0.2,
                timestamp=datetime.now(),
                tool_name="exec",
            )
        )

        high = store.get_high_importance(threshold=0.7)
        assert len(high) == 1
        assert high[0].id == "1"

    def test_clear(self) -> None:
        """Should clear all observations."""
        store = ContextAwareObservationStore()
        store.add(
            Observation(
                id="1",
                insight="Test",
                category="info",
                importance=0.5,
                timestamp=datetime.now(),
                tool_name="exec",
            )
        )
        store.clear()
        assert store.count() == 0
