"""Tests for sandbox isolation."""

import pytest
from lightagent.agent.sandbox import (
    SandboxConfig,
    SandboxLevel,
    SandboxContainer,
    ExecutionResult,
    SandboxManager,
    default_sandbox_config,
)


class TestSandboxConfig:
    """Tests for SandboxConfig."""

    def test_defaults(self) -> None:
        """Should have correct default values."""
        config = SandboxConfig()
        assert config.enabled is True
        assert config.level == SandboxLevel.PROCESS
        assert config.max_memory_mb == 512
        assert config.max_cpu_seconds == 30
        assert config.max_execution_seconds == 60
        assert config.network_allowed is False
        assert len(config.blocked_dirs) > 0

    def test_custom_values(self) -> None:
        """Should accept custom values."""
        config = SandboxConfig(
            enabled=False,
            level=SandboxLevel.DOCKER,
            max_memory_mb=1024,
            network_allowed=True,
        )
        assert config.enabled is False
        assert config.level == SandboxLevel.DOCKER
        assert config.max_memory_mb == 1024
        assert config.network_allowed is True


class TestDefaultSandboxConfig:
    """Tests for default_sandbox_config function."""

    def test_returns_config(self) -> None:
        """Should return a SandboxConfig instance."""
        config = default_sandbox_config()
        assert isinstance(config, SandboxConfig)


class TestExecutionResult:
    """Tests for ExecutionResult."""

    def test_successful_result(self) -> None:
        """Should create successful result."""
        result = ExecutionResult(
            success=True,
            return_code=0,
            stdout="Hello",
            stderr="",
            execution_time_ms=100,
        )
        assert result.success is True
        assert result.return_code == 0
        assert result.stdout == "Hello"

    def test_failed_result(self) -> None:
        """Should create failed result."""
        result = ExecutionResult(
            success=False,
            return_code=1,
            stdout="",
            stderr="Error",
            execution_time_ms=50,
            error="Process failed",
        )
        assert result.success is False
        assert result.error == "Process failed"

    def test_timeout_result(self) -> None:
        """Should create timeout result."""
        result = ExecutionResult(
            success=False,
            return_code=-1,
            stdout="",
            stderr="Timeout",
            execution_time_ms=60000,
            error="Timeout",
            killed=True,
        )
        assert result.killed is True
        assert result.error == "Timeout"


class TestSandboxContainer:
    """Tests for SandboxContainer."""

    def test_context_manager(self) -> None:
        """Should work as context manager."""
        config = SandboxConfig(enabled=False)  # Disable for testing
        with SandboxContainer(config) as container:
            assert container is not None
            assert container.get_work_dir() is not None

    def test_is_path_allowed(self) -> None:
        """Should check path permissions."""
        config = SandboxConfig(
            enabled=False,
            allowed_dirs=["/tmp"],
            blocked_dirs=["/etc"],
        )
        container = SandboxContainer(config)

        # Should allow /tmp
        assert container._is_path_allowed("/tmp/test") is True

        # Should block /etc
        assert container._is_path_allowed("/etc/passwd") is False

    def test_prepare_command(self) -> None:
        """Should prepare command with limits."""
        config = SandboxConfig(
            enabled=False,
            max_execution_seconds=30,
            network_allowed=False,
            environment_vars={"TEST": "value"},
        )
        container = SandboxContainer(config)

        cmd, env = container._prepare_command(["echo", "test"])

        # Should have timeout prepended
        assert cmd[0] == "timeout"
        assert cmd[1] == "30"

        # Should have environment variable
        assert env["TEST"] == "value"

        # Should have network disabled
        assert env["DISABLE_NETWORK"] == "1"

    def test_get_work_dir(self) -> None:
        """Should return work directory."""
        config = SandboxConfig(enabled=False)
        container = SandboxContainer(config)

        # Work dir is created on __enter__
        with container:
            work_dir = container.get_work_dir()
            assert work_dir is not None
            assert "sandbox_" in work_dir


class TestSandboxManager:
    """Tests for SandboxManager."""

    def test_create_container(self) -> None:
        """Should create containers."""
        manager = SandboxManager()
        container = manager.create_container("test1")

        assert container is not None
        assert manager.active_count() == 1

    def test_get_container(self) -> None:
        """Should get container by name."""
        manager = SandboxManager()
        container = manager.create_container("test1")
        retrieved = manager.get_container("test1")

        assert retrieved is container

    def test_destroy_container(self) -> None:
        """Should destroy containers."""
        manager = SandboxManager()
        manager.create_container("test1")
        assert manager.active_count() == 1

        result = manager.destroy_container("test1")
        assert result is True
        assert manager.active_count() == 0

    def test_destroy_nonexistent(self) -> None:
        """Should handle nonexistent container."""
        manager = SandboxManager()
        result = manager.destroy_container("nonexistent")
        assert result is False

    def test_list_containers(self) -> None:
        """Should list containers."""
        manager = SandboxManager()
        manager.create_container("test1")
        manager.create_container("test2")

        containers = manager.list_containers()
        assert "test1" in containers
        assert "test2" in containers

    def test_cleanup_all(self) -> None:
        """Should clean up all containers."""
        manager = SandboxManager()
        manager.create_container("test1")
        manager.create_container("test2")

        manager.cleanup_all()
        assert manager.active_count() == 0

    def test_sandbox_context_manager(self) -> None:
        """Should work as context manager."""
        manager = SandboxManager()

        with manager.sandbox() as container:
            assert container is not None
            assert manager.active_count() == 1

        # Should be cleaned up after context
        assert manager.active_count() == 0

    def test_get_profile(self) -> None:
        """Should get predefined profiles."""
        manager = SandboxManager()

        profile = manager.get_profile("readonly")
        assert profile is not None
        assert profile.max_memory_mb == 256

        profile = manager.get_profile("safe")
        assert profile is not None
        assert profile.max_memory_mb == 512

    def test_unknown_profile(self) -> None:
        """Should return None for unknown profile."""
        manager = SandboxManager()
        profile = manager.get_profile("unknown_profile")
        assert profile is None


class TestSandboxProfiles:
    """Tests for predefined sandbox profiles."""

    def test_readonly_filesystem(self) -> None:
        """Should have correct settings."""
        from lightagent.agent.sandbox.config import SandboxProfile

        profile = SandboxProfile.readonly_filesystem()
        assert profile.name == "readonly_fs"
        assert profile.config.max_memory_mb == 256
        assert profile.config.max_cpu_seconds == 10

    def test_safe_execution(self) -> None:
        """Should have correct settings."""
        from lightagent.agent.sandbox.config import SandboxProfile

        profile = SandboxProfile.safe_execution()
        assert profile.name == "safe_exec"
        assert profile.config.max_memory_mb == 512
        assert profile.config.max_execution_seconds == 60

    def test_network_allowed(self) -> None:
        """Should have network enabled."""
        from lightagent.agent.sandbox.config import SandboxProfile

        profile = SandboxProfile.network_allowed()
        assert profile.name == "network_ok"
        assert profile.config.network_allowed is True
