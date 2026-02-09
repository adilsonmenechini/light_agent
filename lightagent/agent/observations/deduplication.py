"""Deduplication system for tool observations."""

from typing import Optional
import re
from collections import deque


def normalize_text(text: str) -> str:
    """Normalize text for comparison by removing variations."""
    # Lowercase
    text = text.lower()
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove special characters but keep alphanumerics and spaces
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using Jaccard similarity.

    Args:
        text1: First text to compare.
        text2: Second text to compare.

    Returns:
        A value between 0 and 1, where 1 is identical.
    """
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)

    # Handle empty or very short texts
    if len(norm1) < 5 or len(norm2) < 5:
        return 1.0 if norm1 == norm2 else 0.0

    # Create sets of words
    words1 = set(norm1.split())
    words2 = set(norm2.split())

    # Calculate Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    if union == 0:
        return 0.0

    return intersection / union


def calculate_levenshtein_similarity(text1: str, text2: str) -> float:
    """Calculate similarity using normalized Levenshtein distance.

    Args:
        text1: First text to compare.
        text2: Second text to compare.

    Returns:
        A value between 0 and 1, where 1 is identical.
    """
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)

    # Handle empty cases
    if not norm1 and not norm2:
        return 1.0
    if not norm1 or not norm2:
        return 0.0

    # Calculate Levenshtein distance
    distance = _levenshtein_distance(norm1, norm2)
    max_len = max(len(norm1), len(norm2))

    if max_len == 0:
        return 1.0

    return 1.0 - (distance / max_len)


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    current_row = [0] * (len(s2) + 1)

    for i, c1 in enumerate(s1, 1):
        current_row[0] = i
        for j, c2 in enumerate(s2, 1):
            insert = previous_row[j] + 1
            delete = current_row[j - 1] + 1
            substitute = previous_row[j - 1] + (0 if c1 == c2 else 1)
            current_row[j] = min(insert, delete, substitute)
        previous_row, current_row = current_row, previous_row

    return previous_row[len(s2)]


class ObservationDeduplicator:
    """Deduplicator for observations with sliding window support."""

    def __init__(self, similarity_threshold: float = 0.85, max_window_size: int = 50):
        """Initialize the deduplicator.

        Args:
            similarity_threshold: Minimum similarity to consider duplicates (0-1).
            max_window_size: Maximum number of recent observations to keep.
        """
        self.similarity_threshold = similarity_threshold
        self.max_window_size = max_window_size
        self._recent_observations: deque[str] = deque(maxlen=max_window_size)

    def is_duplicate(self, new_observation: str) -> bool:
        """Check if an observation is a duplicate of recent ones.

        Args:
            new_observation: The new observation to check.

        Returns:
            True if it's a duplicate, False otherwise.
        """
        for recent in self._recent_observations:
            sim = calculate_similarity(new_observation, recent)
            if sim >= self.similarity_threshold:
                return True
        return False

    def is_similar(self, text1: str, text2: str) -> bool:
        """Check if two texts are similar.

        Args:
            text1: First text to compare.
            text2: Second text to compare.

        Returns:
            True if texts are similar (above threshold).
        """
        sim = calculate_similarity(text1, text2)
        return sim >= self.similarity_threshold

    def add(self, observation: str) -> None:
        """Add an observation to the recent list.

        Args:
            observation: The observation to add.
        """
        self._recent_observations.append(normalize_text(observation))

    def get_recent_count(self) -> int:
        """Get the number of recent observations stored."""
        return len(self._recent_observations)

    def clear(self) -> None:
        """Clear all recent observations."""
        self._recent_observations.clear()

    def find_similar(self, text: str) -> list[tuple[str, float]]:
        """Find all similar observations in recent window.

        Args:
            text: The text to find similar observations for.

        Returns:
            List of (observation, similarity) tuples sorted by similarity.
        """
        results = []
        for recent in self._recent_observations:
            sim = calculate_similarity(text, recent)
            if sim > 0:
                results.append((recent, sim))
        return sorted(results, key=lambda x: x[1], reverse=True)


def find_duplicates_in_list(
    observations: list[str], similarity_threshold: float = 0.85
) -> list[list[int]]:
    """Find duplicate groups in a list of observations.

    Args:
        observations: List of observation texts.
        similarity_threshold: Minimum similarity to consider duplicates.

    Returns:
        List of groups, where each group is a list of indices that are duplicates.
    """
    if len(observations) <= 1:
        return []

    groups: list[list[int]] = []
    assigned = set()

    for i, obs1 in enumerate(observations):
        if i in assigned:
            continue

        group = [i]
        assigned.add(i)

        for j, obs2 in enumerate(observations[i + 1 :], i + 1):
            if j in assigned:
                continue

            sim = calculate_similarity(obs1, obs2)
            if sim >= similarity_threshold:
                group.append(j)
                assigned.add(j)

        if len(group) > 1:
            groups.append(group)

    return groups
