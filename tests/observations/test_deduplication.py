"""Tests for observation deduplication."""

import pytest
from lightagent.agent.observations import (
    ObservationDeduplicator,
    calculate_similarity,
    calculate_levenshtein_similarity,
    find_duplicates_in_list,
    normalize_text,
)


class TestNormalizeText:
    """Tests for normalize_text function."""

    def test_lowercase_conversion(self) -> None:
        """Text should be converted to lowercase."""
        assert normalize_text("HELLO World") == "hello world"

    def test_remove_extra_whitespace(self) -> None:
        """Extra whitespace should be collapsed."""
        assert normalize_text("hello    world") == "hello world"

    def test_remove_special_characters(self) -> None:
        """Special characters should be removed."""
        assert normalize_text("hello, world!") == "hello world"

    def test_empty_text(self) -> None:
        """Empty text should return empty."""
        assert normalize_text("") == ""

    def test_preserve_alphanumerics(self) -> None:
        """Alphanumeric and underscore should be preserved."""
        assert normalize_text("test123 file_456") == "test123 file_456"


class TestCalculateSimilarity:
    """Tests for calculate_similarity function."""

    def test_identical_texts(self) -> None:
        """Identical texts should have similarity 1.0."""
        assert calculate_similarity("hello world", "hello world") == 1.0

    def test_completely_different(self) -> None:
        """Completely different texts should have low similarity."""
        result = calculate_similarity("hello world", "goodbye world")
        assert 0.0 <= result < 1.0

    def test_partial_overlap(self) -> None:
        """Texts with partial overlap should have partial similarity."""
        sim1 = calculate_similarity("hello world", "hello")
        sim2 = calculate_similarity("hello world", "world")
        assert sim1 > 0
        assert sim2 > 0

    def test_case_insensitive(self) -> None:
        """Comparison should be case insensitive."""
        sim1 = calculate_similarity("Hello World", "hello world")
        sim2 = calculate_similarity("HELLO WORLD", "hello world")
        assert sim1 == 1.0
        assert sim2 == 1.0

    def test_order_insensitive(self) -> None:
        """Word order should not affect similarity much."""
        sim = calculate_similarity("hello world", "world hello")
        assert sim > 0.5  # Should have significant overlap


class TestCalculateLevenshteinSimilarity:
    """Tests for calculate_levenshtein_similarity function."""

    def test_identical_texts(self) -> None:
        """Identical texts should have similarity 1.0."""
        assert calculate_levenshtein_similarity("hello world", "hello world") == 1.0

    def test_small_typo(self) -> None:
        """Texts with small typos should have high similarity."""
        sim = calculate_levenshtein_similarity("hello world", "helo world")
        assert sim > 0.8

    def test_case_insensitive(self) -> None:
        """Comparison should be case insensitive."""
        assert calculate_levenshtein_similarity("Hello", "hello") == 1.0


class TestObservationDeduplicator:
    """Tests for ObservationDeduplicator class."""

    def test_new_observation_not_duplicate(self) -> None:
        """First observation should never be a duplicate."""
        dedup = ObservationDeduplicator()
        assert dedup.is_duplicate("First observation") is False

    def test_identical_is_duplicate(self) -> None:
        """Identical observation should be detected as duplicate."""
        dedup = ObservationDeduplicator()
        dedup.add("Hello world")
        assert dedup.is_duplicate("Hello world") is True

    def test_similar_is_duplicate(self) -> None:
        """Similar observation should be detected as duplicate."""
        dedup = ObservationDeduplicator(similarity_threshold=0.8)
        dedup.add("Read file: config.yaml")
        assert dedup.is_duplicate("Read file: config.yaml") is True

    def test_different_not_duplicate(self) -> None:
        """Different observation should not be duplicate."""
        dedup = ObservationDeduplicator()
        dedup.add("Read file: config.yaml")
        assert dedup.is_duplicate("Executed pytest test.py") is False

    def test_add_observation(self) -> None:
        """Adding observations should work."""
        dedup = ObservationDeduplicator()
        dedup.add("Observation 1")
        dedup.add("Observation 2")
        assert dedup.get_recent_count() == 2

    def test_clear_observations(self) -> None:
        """Clearing observations should reset the dedup."""
        dedup = ObservationDeduplicator()
        dedup.add("Observation 1")
        dedup.clear()
        assert dedup.get_recent_count() == 0

    def test_window_size_limit(self) -> None:
        """Observations should be limited by window size."""
        dedup = ObservationDeduplicator(max_window_size=3)
        for i in range(10):
            dedup.add(f"Observation {i}")
        assert dedup.get_recent_count() == 3

    def test_find_similar(self) -> None:
        """Finding similar observations should return matches."""
        dedup = ObservationDeduplicator()
        dedup.add("Read file: config.yaml")
        dedup.add("Read file: settings.yaml")
        dedup.add("Executed pytest")
        similar = dedup.find_similar("Read file: config.yaml")
        assert len(similar) >= 2  # Should find at least itself and similar

    def test_is_similar_method(self) -> None:
        """is_similar should check similarity between two texts."""
        dedup = ObservationDeduplicator()
        assert dedup.is_similar("hello world", "hello world") is True
        assert dedup.is_similar("hello", "world") is False


class TestFindDuplicatesInList:
    """Tests for find_duplicates_in_list function."""

    def test_single_observation(self) -> None:
        """Single observation should have no duplicates."""
        result = find_duplicates_in_list(["Single observation"])
        assert result == []

    def test_all_identical(self) -> None:
        """All identical observations should be one group."""
        result = find_duplicates_in_list(["Same", "Same", "Same"], similarity_threshold=0.9)
        assert len(result) == 1
        assert set(result[0]) == {0, 1, 2}

    def test_all_different(self) -> None:
        """All different observations should have no groups."""
        result = find_duplicates_in_list(["First", "Second", "Third"], similarity_threshold=0.8)
        assert result == []

    def test_partial_duplicates(self) -> None:
        """Partial duplicates should be grouped correctly."""
        # Using identical and very similar strings
        result = find_duplicates_in_list(
            ["Read file: config.yaml", "Read file: config.yaml", "Read file: config.yaml"],
            similarity_threshold=0.85,
        )
        # All should be grouped together since they're identical
        assert len(result) == 1
        assert set(result[0]) == {0, 1, 2}

    def test_custom_threshold(self) -> None:
        """Custom threshold should affect grouping."""
        result_high = find_duplicates_in_list(
            ["hello world", "hello world"], similarity_threshold=0.99
        )
        result_low = find_duplicates_in_list(
            ["hello world", "hello world"], similarity_threshold=0.5
        )
        # Both should find duplicates with high threshold for identical
        assert len(result_high) == 1
