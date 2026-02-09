"""Importance scoring system for tool observations."""

from typing import Optional
import re


class ImportanceLevel:
    """Importance levels for observations."""

    CRITICAL = 1.0
    HIGH = 0.8
    MEDIUM = 0.5
    LOW = 0.3
    MINIMAL = 0.1


# Keywords that indicate critical importance
_CRITICAL_KEYWORDS = [
    r"security",
    r"vulnerability",
    r"exploit",
    r"breach",
    r"leak",
    r"password",
    r"secret",
    r"token",
    r"api[_-]?key",
    r"credential",
    r"critical",
    r"fatal",
    r"panic",
    r"abort",
    r"sql[_-]?injection",
    r"xss",
    r"csrf",
    r"rce",
]

# Keywords that indicate high importance
_HIGH_KEYWORDS = [
    r"bug",
    r"fix",
    r"error",
    r"exception",
    r"fail",
    r"crash",
    r"config",
    r"settings?",
    r"environment",
    r"deploy",
    r"database",
    r"migration",
    r"schema",
    r"docker",
    r"kubernetes",
    r"container",
]

# Keywords that indicate low/minimal importance
_LOW_KEYWORDS = [
    r"log",
    r"info",
    r"debug",
    r"trace",
    r"version",
    r"hello",
    r"world",
    r"test",
]


def calculate_importance_score(
    insight: str, tool_name: str, tool_result: str, category: str = "unknown"
) -> float:
    """Calculate an importance score (0-1) for an observation.

    Args:
        insight: The extracted insight text.
        tool_name: Name of the tool that was executed.
        tool_result: Result returned by the tool.
        category: The observation category.

    Returns:
        A score between 0 and 1, where 1 is most important.
    """
    combined_text = f"{insight} {tool_result}".lower()

    # Start with base score based on category
    base_score = _get_category_base_score(category)

    # Adjust for critical keywords
    critical_matches = sum(1 for kw in _CRITICAL_KEYWORDS if re.search(kw, combined_text))
    if critical_matches > 0:
        return min(ImportanceLevel.CRITICAL, base_score + (critical_matches * 0.15))

    # Adjust for high importance keywords
    high_matches = sum(1 for kw in _HIGH_KEYWORDS if re.search(kw, combined_text))
    if high_matches > 0:
        # Apply diminishing returns
        bonus = min(0.3, high_matches * 0.1)
        return min(ImportanceLevel.HIGH, base_score + bonus)

    # Adjust for low importance keywords
    low_matches = sum(1 for kw in _LOW_KEYWORDS if re.search(kw, combined_text))
    if low_matches > 0:
        penalty = min(0.2, low_matches * 0.05)
        return max(ImportanceLevel.MINIMAL, base_score - penalty)

    return base_score


def _get_category_base_score(category: str) -> float:
    """Get the base importance score for a category."""
    category_scores = {
        "security": 0.9,
        "error": 0.8,
        "bug": 0.8,
        "config": 0.7,
        "database": 0.7,
        "deployment": 0.7,
        "code": 0.5,
        "docs": 0.4,
        "test": 0.5,
        "performance": 0.6,
        "dependency": 0.4,
        "info": 0.2,
        "unknown": 0.3,
    }
    return category_scores.get(category.lower(), 0.3)


def get_importance_level(score: float) -> str:
    """Convert a numeric score to a human-readable level.

    Args:
        score: A value between 0 and 1.

    Returns:
        One of: "critical", "high", "medium", "low", "minimal".
    """
    if score >= ImportanceLevel.CRITICAL:
        return "critical"
    elif score >= ImportanceLevel.HIGH:
        return "high"
    elif score >= ImportanceLevel.MEDIUM:
        return "medium"
    elif score >= ImportanceLevel.LOW:
        return "low"
    else:
        return "minimal"


def should_promote_to_memory(score: float, threshold: float = 0.7) -> bool:
    """Determine if an observation should be promoted to long-term memory.

    Args:
        score: The importance score.
        threshold: Minimum score to promote (default: 0.7).

    Returns:
        True if the observation should be promoted.
    """
    return score >= threshold
