"""Tests for observation categorization."""

import pytest
from lightagent.agent.observations import (
    ObservationCategory,
    categorize_observation,
    categorize_tool_result,
    get_category_description,
    get_all_categories,
)


class TestCategorizeToolResult:
    """Tests for categorize_tool_result function."""

    def test_read_file_category(self) -> None:
        """read_file should be categorized as CODE."""
        result = categorize_tool_result(
            tool_name="read_file",
            tool_args={"path": "test.py"},
            tool_result="def hello(): return 'world'",
        )
        assert result == ObservationCategory.CODE

    def test_write_file_with_code_extension(self) -> None:
        """write_file with .py extension should be categorized as CODE."""
        result = categorize_tool_result(
            tool_name="write_file",
            tool_args={"path": "test.py"},
            tool_result="def hello(): return 'world'",
        )
        assert result == ObservationCategory.CODE

    def test_grep_category(self) -> None:
        """grep should be categorized as CODE."""
        result = categorize_tool_result(
            tool_name="grep",
            tool_args={"pattern": "def.*test"},
            tool_result="test.py:1:def test():",
        )
        assert result == ObservationCategory.CODE

    def test_exec_with_pytest_bug_result(self) -> None:
        """exec with pytest failing should be categorized as TEST."""
        result = categorize_tool_result(
            tool_name="exec",
            tool_args={"command": "pytest"},
            tool_result="1 failed - test_example in test_file.py",
        )
        assert result == ObservationCategory.TEST

    def test_exec_with_database_keyword(self) -> None:
        """exec with database-related result should be categorized as DATABASE."""
        result = categorize_tool_result(
            tool_name="exec", tool_args={"command": "psql"}, tool_result="SELECT * FROM users"
        )
        assert result == ObservationCategory.DATABASE

    def test_github_workflow_category(self) -> None:
        """github_workflow_tool should be categorized as DEPLOYMENT."""
        result = categorize_tool_result(
            tool_name="github_workflow_tool",
            tool_args={"action": "run"},
            tool_result="Workflow started",
        )
        assert result == ObservationCategory.DEPLOYMENT

    def test_web_search_category(self) -> None:
        """web_search should be categorized as DOCS."""
        result = categorize_tool_result(
            tool_name="web_search",
            tool_args={"query": "python tutorial"},
            tool_result="Found 10 results",
        )
        assert result == ObservationCategory.DOCS

    def test_unknown_tool_defaults_to_info(self) -> None:
        """Unknown tool should default to INFO category."""
        result = categorize_tool_result(
            tool_name="unknown_tool", tool_args={}, tool_result="Some output"
        )
        assert result == ObservationCategory.INFO

    def test_error_result_categorized_as_error(self) -> None:
        """Tool result with error should be categorized as ERROR."""
        result = categorize_tool_result(
            tool_name="exec",
            tool_args={"command": "some_command"},
            tool_result="Error: command not found",
        )
        assert result == ObservationCategory.ERROR

    def test_config_file_categorized_as_config(self) -> None:
        """Reading config files should be categorized as CONFIG."""
        result = categorize_tool_result(
            tool_name="read_file",
            tool_args={"path": "config.yaml"},
            tool_result="database:\n  host: localhost\n  port: 5432",
        )
        assert result == ObservationCategory.CONFIG

    def test_docker_related_categorized_as_deployment(self) -> None:
        """Docker-related operations should be categorized as DEPLOYMENT."""
        result = categorize_tool_result(
            tool_name="exec",
            tool_args={"command": "docker ps"},
            tool_result="CONTAINER ID IMAGE COMMAND",
        )
        assert result == ObservationCategory.DEPLOYMENT

    def test_security_keywords_categorized_as_security(self) -> None:
        """Security-related content should be categorized as SECURITY."""
        result = categorize_tool_result(
            tool_name="read_file",
            tool_args={"path": "secrets.env"},
            tool_result="API_KEY=secret123 JWT_TOKEN=abc",
        )
        assert result == ObservationCategory.SECURITY


class TestCategorizeObservation:
    """Tests for categorize_observation function."""

    def test_bug_insight_categorized_as_bug(self) -> None:
        """Insight about a bug should be categorized as BUG."""
        result = categorize_observation(
            insight="Found a bug in the login function",
            tool_name="read_file",
            tool_result="def login(): raise Exception('bug')",
        )
        assert result == ObservationCategory.BUG

    def test_config_insight_categorized_as_config(self) -> None:
        """Insight about config should be categorized as CONFIG."""
        result = categorize_observation(
            insight="Updated the app settings",
            tool_name="read_file",
            tool_result="timeout: 30\nretry: 3\nlog_level: info",
        )
        assert result == ObservationCategory.CONFIG

    def test_docs_insight_categorized_as_docs(self) -> None:
        """Insight about documentation should be categorized as DOCS."""
        result = categorize_observation(
            insight="Added docstrings to all functions",
            tool_name="write_file",
            tool_result="Documentation added",
        )
        assert result == ObservationCategory.DOCS


class TestGetCategoryDescription:
    """Tests for get_category_description function."""

    def test_bug_description(self) -> None:
        """Bug category should have correct description."""
        desc = get_category_description(ObservationCategory.BUG)
        assert "Bug" in desc or "bug" in desc.lower()

    def test_config_description(self) -> None:
        """Config category should have correct description."""
        desc = get_category_description(ObservationCategory.CONFIG)
        assert "Config" in desc or "config" in desc.lower()

    def test_all_categories_have_description(self) -> None:
        """All categories should have a description."""
        for category in ObservationCategory:
            desc = get_category_description(category)
            assert desc is not None
            assert len(desc) > 0


class TestGetAllCategories:
    """Tests for get_all_categories function."""

    def test_returns_all_categories(self) -> None:
        """Should return all category values."""
        categories = get_all_categories()
        assert len(categories) == len(ObservationCategory)
        assert ObservationCategory.BUG in categories
        assert ObservationCategory.CONFIG in categories
        assert ObservationCategory.DOCS in categories
        assert ObservationCategory.UNKNOWN in categories

    def test_all_are_observation_category(self) -> None:
        """All returned values should be ObservationCategory enum members."""
        categories = get_all_categories()
        for cat in categories:
            assert isinstance(cat, ObservationCategory)
