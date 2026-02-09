"""Tests for SubagentManager."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, MagicMock

import pytest

from lightagent.agent.subagent import ExecToolConfig, SubagentManager
from lightagent.providers.base import LLMResponse
from lightagent.session.manager import SessionManager


class TestExecToolConfig:
    """Tests for ExecToolConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ExecToolConfig()
        assert config.timeout == 60
        assert config.restrict_to_workspace is False

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = ExecToolConfig(timeout=120, restrict_to_workspace=True)
        assert config.timeout == 120
        assert config.restrict_to_workspace is True


class TestSubagentManager:
    """Tests for SubagentManager class."""

    @pytest.fixture
    def temp_workspace(self) -> Path:
        """Create temporary workspace."""
        with TemporaryDirectory() as tmp:
            yield Path(tmp)

    @pytest.fixture
    def mock_provider(self) -> MagicMock:
        """Create a mock LLM provider."""
        provider = MagicMock()
        provider.generate = AsyncMock(
            return_value=LLMResponse(content="Task completed successfully.")
        )
        provider.get_default_model = MagicMock(return_value="test/model")
        return provider

    @pytest.fixture
    def session_manager(self, temp_workspace: Path) -> SessionManager:
        """Create a session manager."""
        return SessionManager(temp_workspace)

    def test_init(self, mock_provider: MagicMock, temp_workspace: Path) -> None:
        """Test SubagentManager initialization."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )
        assert manager.provider == mock_provider
        assert manager.workspace == temp_workspace
        assert manager.model is not None
        assert manager.exec_config is not None

    def test_init_with_custom_model(self, mock_provider: MagicMock, temp_workspace: Path) -> None:
        """Test initialization with custom model."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
            model="custom/model",
        )
        assert manager.model == "custom/model"

    def test_init_with_exec_config(self, mock_provider: MagicMock, temp_workspace: Path) -> None:
        """Test initialization with custom exec config."""
        config = ExecToolConfig(timeout=300, restrict_to_workspace=True)
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
            exec_config=config,
        )
        assert manager.exec_config.timeout == 300
        assert manager.exec_config.restrict_to_workspace is True

    @pytest.mark.asyncio
    async def test_spawn_returns_status_message(
        self, mock_provider: MagicMock, temp_workspace: Path
    ) -> None:
        """Test that spawn returns a status message."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )

        result = await manager.spawn("List files in current directory", label="List files")

        assert "started" in result.lower() or "spawned" in result.lower()

    @pytest.mark.asyncio
    async def test_spawn_tracks_running_task(
        self, mock_provider: MagicMock, temp_workspace: Path
    ) -> None:
        """Test that spawn tracks running tasks."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )

        initial_count = manager.get_running_count()
        await manager.spawn("Test task", label="Test")
        assert manager.get_running_count() == initial_count + 1

    @pytest.mark.asyncio
    async def test_get_running_count_empty(
        self, mock_provider: MagicMock, temp_workspace: Path
    ) -> None:
        """Test getting running count when no tasks."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )

        assert manager.get_running_count() == 0

    @pytest.mark.asyncio
    async def test_get_result(self, mock_provider: MagicMock, temp_workspace: Path) -> None:
        """Test getting a result by task ID."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )

        result = manager.get_result("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_results(self, mock_provider: MagicMock, temp_workspace: Path) -> None:
        """Test listing all results."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )

        results = manager.list_results()
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_wait_for_no_tasks(self, mock_provider: MagicMock, temp_workspace: Path) -> None:
        """Test waiting when no tasks are running."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )

        result = await manager.wait_for()
        assert "no running subagents" in result["summary"].lower()

    @pytest.mark.asyncio
    async def test_wait_for_specific_tasks(
        self, mock_provider: MagicMock, temp_workspace: Path
    ) -> None:
        """Test waiting for specific task IDs."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )

        result = await manager.wait_for(task_ids=["nonexistent"])
        assert "no running subagents" in result["summary"].lower()

    @pytest.mark.asyncio
    async def test_build_subagent_prompt(
        self, mock_provider: MagicMock, temp_workspace: Path
    ) -> None:
        """Test subagent prompt generation."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )

        prompt = manager._build_subagent_prompt("Test task description")

        assert "Test task description" in prompt
        assert "Subagent" in prompt
        assert str(temp_workspace) in prompt

    @pytest.mark.asyncio
    async def test_spawn_with_label(self, mock_provider: MagicMock, temp_workspace: Path) -> None:
        """Test spawning with a custom label."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )

        result = await manager.spawn(
            "A very long task description that exceeds thirty characters",
            label="Short Label",
        )

        assert "Short Label" in result

    @pytest.mark.asyncio
    async def test_spawn_auto_generates_label(
        self, mock_provider: MagicMock, temp_workspace: Path
    ) -> None:
        """Test that spawn auto-generates label from task."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )

        result = await manager.spawn("Short task")

        # Auto-generated label should contain task
        assert "Short task" in result or "started" in result.lower()

    @pytest.mark.asyncio
    async def test_spawn_with_model(self, mock_provider: MagicMock, temp_workspace: Path) -> None:
        """Test spawning with custom model."""
        manager = SubagentManager(
            provider=mock_provider,
            workspace=temp_workspace,
            session_manager=SessionManager(temp_workspace),
        )

        # Model should be passed through
        result = await manager.spawn("Task", model="custom/model")
        assert "started" in result.lower()
