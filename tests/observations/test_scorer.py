"""Tests for importance scoring."""

import pytest
from lightagent.agent.observations import (
    ImportanceLevel,
    calculate_importance_score,
    get_importance_level,
    should_promote_to_memory,
)


class TestCalculateImportanceScore:
    """Tests for calculate_importance_score function."""

    def test_security_keywords_score_critical(self) -> None:
        """Security-related content should score critical."""
        score = calculate_importance_score(
            insight="Found exposed API key",
            tool_name="read_file",
            tool_result="API_KEY=secret123",
            category="security",
        )
        assert score == ImportanceLevel.CRITICAL

    def test_error_result_scores_high(self) -> None:
        """Error results should score high."""
        score = calculate_importance_score(
            insight="Command failed",
            tool_name="exec",
            tool_result="Error: command not found",
            category="error",
        )
        assert score >= ImportanceLevel.HIGH

    def test_bug_keyword_increases_score(self) -> None:
        """Bug-related content should score higher than base."""
        base = calculate_importance_score(
            insight="Some info", tool_name="read_file", tool_result="Content here", category="code"
        )
        with_bug = calculate_importance_score(
            insight="Fixed a bug in the code",
            tool_name="read_file",
            tool_result="def fix(): pass",
            category="code",
        )
        assert with_bug > base

    def test_config_changes_score_medium_high(self) -> None:
        """Configuration changes should score medium-high."""
        score = calculate_importance_score(
            insight="Updated config file",
            tool_name="write_file",
            tool_result="timeout: 30",
            category="config",
        )
        assert score >= ImportanceLevel.MEDIUM

    def test_info_logs_score_low(self) -> None:
        """Info/debug logs should score low."""
        score = calculate_importance_score(
            insight="Added logging",
            tool_name="exec",
            tool_result="INFO: Server started",
            category="info",
        )
        assert score <= ImportanceLevel.LOW

    def test_unknown_category_defaults(self) -> None:
        """Unknown category should use default score."""
        score = calculate_importance_score(
            insight="Some observation",
            tool_name="unknown_tool",
            tool_result="Result",
            category="unknown",
        )
        assert 0.0 <= score <= 1.0
        assert score == 0.3  # Default for unknown

    def test_security_category_base_high(self) -> None:
        """Security category should have high base score."""
        score = calculate_importance_score(
            insight="Security check",
            tool_name="read_file",
            tool_result="No issues found",
            category="security",
        )
        assert score >= 0.7

    def test_database_category_base(self) -> None:
        """Database category should have medium-high base."""
        score = calculate_importance_score(
            insight="Database query",
            tool_name="exec",
            tool_result="SELECT * FROM users",
            category="database",
        )
        assert score >= 0.5


class TestGetImportanceLevel:
    """Tests for get_importance_level function."""

    def test_critical_level(self) -> None:
        """Score 1.0 should be critical."""
        assert get_importance_level(1.0) == "critical"

    def test_high_level(self) -> None:
        """Score 0.8 should be high."""
        assert get_importance_level(0.8) == "high"

    def test_medium_level(self) -> None:
        """Score 0.5 should be medium."""
        assert get_importance_level(0.5) == "medium"

    def test_low_level(self) -> None:
        """Score 0.3 should be low."""
        assert get_importance_level(0.3) == "low"

    def test_minimal_level(self) -> None:
        """Score 0.1 should be minimal."""
        assert get_importance_level(0.1) == "minimal"

    def test_boundary_values(self) -> None:
        """Test boundary values between levels."""
        assert get_importance_level(0.8) == "high"
        assert get_importance_level(0.5) == "medium"
        assert get_importance_level(0.3) == "low"


class TestShouldPromoteToMemory:
    """Tests for should_promote_to_memory function."""

    def test_critical_promotes(self) -> None:
        """Critical observations should promote."""
        assert should_promote_to_memory(0.9) is True

    def test_high_promotes(self) -> None:
        """High importance should promote."""
        assert should_promote_to_memory(0.8) is True

    def test_medium_does_not_promote(self) -> None:
        """Medium importance should not promote by default."""
        assert should_promote_to_memory(0.5) is False

    def test_low_does_not_promote(self) -> None:
        """Low importance should not promote."""
        assert should_promote_to_memory(0.3) is False

    def test_custom_threshold(self) -> None:
        """Custom threshold should work."""
        assert should_promote_to_memory(0.5, threshold=0.5) is True
        assert should_promote_to_memory(0.4, threshold=0.5) is False


class TestImportanceLevel:
    """Tests for ImportanceLevel constants."""

    def test_critical_is_one(self) -> None:
        """CRITICAL should equal 1.0."""
        assert ImportanceLevel.CRITICAL == 1.0

    def test_values_order(self) -> None:
        """Values should be in descending order."""
        assert ImportanceLevel.CRITICAL > ImportanceLevel.HIGH
        assert ImportanceLevel.HIGH > ImportanceLevel.MEDIUM
        assert ImportanceLevel.MEDIUM > ImportanceLevel.LOW
        assert ImportanceLevel.LOW > ImportanceLevel.MINIMAL

    def test_all_values_between_zero_and_one(self) -> None:
        """All values should be between 0 and 1."""
        assert 0.0 <= ImportanceLevel.CRITICAL <= 1.0
        assert 0.0 <= ImportanceLevel.HIGH <= 1.0
        assert 0.0 <= ImportanceLevel.MEDIUM <= 1.0
        assert 0.0 <= ImportanceLevel.LOW <= 1.0
        assert 0.0 <= ImportanceLevel.MINIMAL <= 1.0
