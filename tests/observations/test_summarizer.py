"""Tests for AI summarization."""

import pytest
from lightagent.agent.observations.summarizer import (
    SummarizationConfig,
    generate_summary,
    generate_session_summary,
    get_supported_languages,
    get_supported_styles,
)


class TestSummarizationConfig:
    """Tests for SummarizationConfig."""

    def test_defaults(self) -> None:
        """Should have correct default values."""
        config = SummarizationConfig()
        assert config.max_summary_length == 150
        assert config.include_context is True
        assert config.language == "pt"
        assert config.style == "concise"

    def test_custom_values(self) -> None:
        """Should accept custom values."""
        config = SummarizationConfig(
            max_summary_length=200, include_context=False, language="en", style="detailed"
        )
        assert config.max_summary_length == 200
        assert config.include_context is False
        assert config.language == "en"
        assert config.style == "detailed"


class TestGenerateSummary:
    """Tests for generate_summary function."""

    @pytest.mark.asyncio
    async def test_fallback_exec(self) -> None:
        """Should use fallback for exec."""
        result = await generate_summary(
            tool_name="exec",
            tool_args={"command": "pytest"},
            tool_result="3 tests passed, 1 failed in 2.5 seconds",
        )
        assert "Executou" in result or "command" in result.lower()

    @pytest.mark.asyncio
    async def test_empty_result(self) -> None:
        """Should handle empty results."""
        result = await generate_summary(tool_name="exec", tool_args={}, tool_result="")
        # Should not crash

    @pytest.mark.asyncio
    async def test_error_result(self) -> None:
        """Should handle error results."""
        result = await generate_summary(
            tool_name="exec", tool_args={}, tool_result="Error: command not found"
        )
        assert "Error" in result or "Erro" in result

    @pytest.mark.asyncio
    async def test_truncation(self) -> None:
        """Should truncate very long results."""
        long_result = "x" * 3000
        result = await generate_summary(tool_name="exec", tool_args={}, tool_result=long_result)
        assert len(result) < 2500

    @pytest.mark.asyncio
    async def test_short_result(self) -> None:
        """Should not truncate very short results."""
        result = await generate_summary(tool_name="exec", tool_args={}, tool_result="OK")
        assert result == "OK"

    @pytest.mark.asyncio
    async def test_grep_result(self) -> None:
        """Should count grep results."""
        result = await generate_summary(
            tool_name="grep",
            tool_args={"pattern": "def"},
            tool_result="file1.py:1:def test()\nfile2.py:2:def test2()",
        )
        assert "2" in result or "resultados" in result.lower()


class TestGenerateSessionSummary:
    """Tests for generate_session_summary function."""

    @pytest.mark.asyncio
    async def test_empty_observations(self) -> None:
        """Should handle empty observations."""
        result = await generate_session_summary([], language="pt")
        assert "nenhuma" in result.lower() or "no" in result.lower()

        result = await generate_session_summary([], language="en")
        assert "no" in result.lower()

    @pytest.mark.asyncio
    async def test_fallback_summary(self) -> None:
        """Should use fallback when no LLM provider."""
        observations = [
            {"insight": "Found bug 1", "category": "bug", "importance": 0.8},
            {"insight": "Config updated", "category": "config", "importance": 0.5},
        ]
        result = await generate_session_summary(observations, language="pt")
        assert "bug" in result.lower()
        assert "config" in result.lower()


class TestGetSupportedLanguages:
    """Tests for get_supported_languages function."""

    def test_returns_list(self) -> None:
        """Should return a list of languages."""
        langs = get_supported_languages()
        assert isinstance(langs, list)
        assert "pt" in langs
        assert "en" in langs


class TestGetSupportedStyles:
    """Tests for get_supported_styles function."""

    def test_returns_list(self) -> None:
        """Should return a list of styles."""
        styles = get_supported_styles()
        assert isinstance(styles, list)
        assert "concise" in styles
        assert "detailed" in styles
        assert "narrative" in styles


class TestShouldUseAI:
    """Tests for internal _should_use_ai function."""

    def test_long_exec_result(self) -> None:
        """Should use AI for long exec results."""
        from lightagent.agent.observations.summarizer import _should_use_ai

        assert _should_use_ai("exec", "x" * 600) is True

    def test_short_exec_result(self) -> None:
        """Should not use AI for short exec results."""
        from lightagent.agent.observations.summarizer import _should_use_ai

        assert _should_use_ai("exec", "x" * 100) is False

    def test_list_dir(self) -> None:
        """Should not use AI for list_dir."""
        from lightagent.agent.observations.summarizer import _should_use_ai

        assert _should_use_ai("list_dir", "files...") is False
