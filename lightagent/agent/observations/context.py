"""Context awareness for detecting related observations."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import re


@dataclass
class Observation:
    """Represents a tool observation with metadata."""

    id: str
    insight: str
    category: str
    importance: float
    timestamp: datetime
    tool_name: str
    related_ids: list[str] = field(default_factory=list)
    context_tags: list[str] = field(default_factory=list)


@dataclass
class ContextMatch:
    """Represents a context match between observations."""

    observation_id: str
    related_id: str
    match_type: str
    confidence: float
    reason: str


# Keywords that indicate temporal context
_TEMPORAL_KEYWORDS = {
    "before": -1,  # Refers to something before
    "after": 1,  # Refers to something after
    "previously": -1,
    "earlier": -1,
    "later": 1,
    "next": 1,
    "then": 0,
    "now": 0,
    "currently": 0,
}

# Keywords that indicate causal relationships
_CAUSAL_KEYWORDS = {
    "because": 1,
    "caused": 1,
    "result": 1,
    "due": 1,
    "therefore": 1,
    "thus": 1,
    "hence": 1,
    "so": 1,
}

# Keywords that indicate contrast
_CONTRAST_KEYWORDS = {
    "but": -1,
    "however": -1,
    "although": -1,
    "instead": -1,
    "rather": -1,
    "whereas": -1,
    "while": 0,
}


def extract_context_tags(text: str) -> list[str]:
    """Extract context-relevant tags from observation text.

    Args:
        text: The observation text to analyze.

    Returns:
        List of context tags.
    """
    tags = []

    # Extract file paths
    file_paths = re.findall(r"[\w/\-.]+\.(py|js|ts|json|yaml|yml|txt|md)", text)
    if file_paths:
        tags.append("file_references")

    # Extract line numbers
    line_refs = re.findall(r"line\s+\d+|\d+:\d+", text)
    if line_refs:
        tags.append("line_references")

    # Extract error types
    error_types = re.findall(
        r"(ValueError|TypeError|KeyError|AttributeError|ImportError|RuntimeError)", text
    )
    if error_types:
        tags.append("has_error")

    # Extract function/method names
    functions = re.findall(r"def\s+(\w+)|(\w+)\s*\(|(\w+)\s*=\s*function", text)
    if functions:
        tags.append("has_function_ref")

    # Extract configuration keys
    config_keys = re.findall(
        r"(timeout|retry|max_|limit|threshold|port|host|database|url|api_?key)", text
    )
    if config_keys:
        tags.append("has_config")

    # Extract numbers
    numbers = re.findall(r"(error|success|fail|pass|warn|info|debug)", text)
    if numbers:
        tags.append("has_status")

    return tags


def detect_temporal_relation(text: str) -> Optional[str]:
    """Detect temporal relations in text.

    Args:
        text: The text to analyze.

    Returns:
        One of: "before", "after", "simultaneous", or None.
    """
    text_lower = text.lower()

    for keyword, relation in _TEMPORAL_KEYWORDS.items():
        if keyword in text_lower:
            if relation < 0:
                return "before"
            elif relation > 0:
                return "after"
            else:
                return "simultaneous"

    return None


def detect_causal_relation(text: str) -> Optional[str]:
    """Detect causal relations in text.

    Args:
        text: The text to analyze.

    Returns:
        One of: "causal", "contrast", or None.
    """
    text_lower = text.lower()

    for keyword in _CAUSAL_KEYWORDS:
        if keyword in text_lower:
            return "causal"

    for keyword in _CONTRAST_KEYWORDS:
        if keyword in text_lower:
            return "contrast"

    return None


def are_related(
    obs1: Observation, obs2: Observation, time_window_hours: float = 24.0
) -> list[ContextMatch]:
    """Check if two observations are related.

    Args:
        obs1: First observation.
        obs2: Second observation.
        time_window_hours: Maximum time difference to consider related.

    Returns:
        List of context matches explaining the relation.
    """
    matches: list[ContextMatch] = []

    # Check temporal proximity
    time_diff = abs((obs1.timestamp - obs2.timestamp).total_seconds() / 3600)
    if time_diff <= time_window_hours:
        matches.append(
            ContextMatch(
                observation_id=obs1.id,
                related_id=obs2.id,
                match_type="temporal",
                confidence=1.0 - (time_diff / time_window_hours),
                reason=f"Observations within {time_window_hours}h of each other",
            )
        )

    # Check same category
    if obs1.category == obs2.category:
        matches.append(
            ContextMatch(
                observation_id=obs1.id,
                related_id=obs2.id,
                match_type="category",
                confidence=0.9,
                reason=f"Both observations are in category '{obs1.category}'",
            )
        )

    # Check overlapping context tags
    common_tags = set(obs1.context_tags) & set(obs2.context_tags)
    if common_tags:
        matches.append(
            ContextMatch(
                observation_id=obs1.id,
                related_id=obs2.id,
                match_type="context",
                confidence=0.8,
                reason=f"Shared context: {', '.join(common_tags)}",
            )
        )

    # Check same tool
    if obs1.tool_name == obs2.tool_name:
        matches.append(
            ContextMatch(
                observation_id=obs1.id,
                related_id=obs2.id,
                match_type="tool",
                confidence=0.7,
                reason=f"Both from tool '{obs1.tool_name}'",
            )
        )

    # Check importance correlation (both high or both low)
    if (obs1.importance > 0.7 and obs2.importance > 0.7) or (
        obs1.importance < 0.3 and obs2.importance < 0.3
    ):
        matches.append(
            ContextMatch(
                observation_id=obs1.id,
                related_id=obs2.id,
                match_type="importance",
                confidence=0.6,
                reason="Similar importance levels",
            )
        )

    return matches


class ContextAwareObservationStore:
    """Store observations with context awareness."""

    def __init__(self, time_window_hours: float = 24.0, max_related: int = 5):
        """Initialize the store.

        Args:
            time_window_hours: Maximum time window for temporal relations.
            max_related: Maximum number of related observations to track.
        """
        self.time_window_hours = time_window_hours
        self.max_related = max_related
        self._observations: dict[str, Observation] = {}

    def add(self, observation: Observation) -> None:
        """Add an observation and find related ones.

        Args:
            observation: The observation to add.
        """
        # Extract context tags
        observation.context_tags = extract_context_tags(observation.insight)

        # Find related observations
        related = []
        for obs_id, obs in self._observations.items():
            if obs_id == observation.id:
                continue

            matches = are_related(observation, obs, self.time_window_hours)
            if matches:
                related.append((obs_id, sum(m.confidence for m in matches)))

        # Sort by confidence and take top N
        related.sort(key=lambda x: x[1], reverse=True)
        observation.related_ids = [oid for oid, _ in related[: self.max_related]]

        # Update related observations
        for oid in observation.related_ids:
            if observation.id not in self._observations[oid].related_ids:
                if len(self._observations[oid].related_ids) < self.max_related:
                    self._observations[oid].related_ids.append(observation.id)

        self._observations[observation.id] = observation

    def get(self, observation_id: str) -> Optional[Observation]:
        """Get an observation by ID.

        Args:
            observation_id: The ID to look up.

        Returns:
            The observation or None if not found.
        """
        return self._observations.get(observation_id)

    def get_related(self, observation_id: str) -> list[Observation]:
        """Get all related observations.

        Args:
            observation_id: The ID to find relations for.

        Returns:
            List of related observations.
        """
        obs = self.get(observation_id)
        if not obs:
            return []

        return [self._observations[oid] for oid in obs.related_ids if oid in self._observations]

    def get_by_category(self, category: str) -> list[Observation]:
        """Get all observations in a category.

        Args:
            category: The category to filter by.

        Returns:
            List of observations in the category.
        """
        return [obs for obs in self._observations.values() if obs.category == category]

    def get_by_time_window(self, hours: float) -> list[Observation]:
        """Get observations within a time window.

        Args:
            hours: The time window in hours.

        Returns:
            List of recent observations.
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        return [obs for obs in self._observations.values() if obs.timestamp >= cutoff]

    def get_high_importance(self, threshold: float = 0.7) -> list[Observation]:
        """Get high importance observations.

        Args:
            threshold: Minimum importance score.

        Returns:
            List of high importance observations.
        """
        return [obs for obs in self._observations.values() if obs.importance >= threshold]

    def count(self) -> int:
        """Get total number of observations."""
        return len(self._observations)

    def clear(self) -> None:
        """Clear all observations."""
        self._observations.clear()
