"""Sandbox manager for managing multiple isolated execution environments."""

from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from .config import SandboxConfig, SandboxLevel, SandboxProfile, default_sandbox_config
from .container import SandboxContainer, ExecutionResult


class SandboxManager:
    """Manager for creating and managing sandboxed execution environments."""

    def __init__(self, config: Optional[SandboxConfig] = None):
        """Initialize sandbox manager.

        Args:
            config: Default sandbox configuration.
        """
        self.default_config = config or default_sandbox_config()
        self._containers: Dict[str, SandboxContainer] = {}
        self._active_count = 0

    def create_container(
        self,
        name: Optional[str] = None,
        config: Optional[SandboxConfig] = None,
    ) -> SandboxContainer:
        """Create a new sandbox container.

        Args:
            name: Optional container name.
            config: Optional configuration.

        Returns:
            SandboxContainer instance.
        """
        container_config = config or self.default_config
        container = SandboxContainer(container_config)
        container_name = name or f"sandbox_{self._active_count}"
        self._containers[container_name] = container
        self._active_count += 1
        return container

    def get_container(self, name: str) -> Optional[SandboxContainer]:
        """Get a container by name.

        Args:
            name: Container name.

        Returns:
            SandboxContainer or None if not found.
        """
        return self._containers.get(name)

    def destroy_container(self, name: str) -> bool:
        """Destroy a container.

        Args:
            name: Container name.

        Returns:
            True if container was destroyed.
        """
        container = self._containers.get(name)
        if container:
            container._cleanup()
            del self._containers[name]
            return True
        return False

    @contextmanager
    def sandbox(
        self,
        config: Optional[SandboxConfig] = None,
    ) -> Generator[SandboxContainer, None, None]:
        """Context manager for sandbox execution.

        Args:
            config: Optional sandbox configuration.

        Yields:
            SandboxContainer instance.
        """
        container = self.create_container(config=config)
        try:
            yield container
        finally:
            # Find and destroy the container
            for name, cont in list(self._containers.items()):
                if cont is container:
                    self.destroy_container(name)
                    break

    def execute_in_sandbox(
        self,
        command: list[str],
        config: Optional[SandboxConfig] = None,
        **kwargs: Any,
    ) -> ExecutionResult:
        """Execute a command in a temporary sandbox.

        Args:
            command: Command to execute.
            config: Optional sandbox configuration.
            **kwargs: Additional arguments for execute().

        Returns:
            ExecutionResult.
        """
        with self.sandbox(config=config) as container:
            return container.execute(command, **kwargs)

    def execute_python_in_sandbox(
        self,
        code: str,
        config: Optional[SandboxConfig] = None,
        **kwargs: Any,
    ) -> ExecutionResult:
        """Execute Python code in a temporary sandbox.

        Args:
            code: Python code to execute.
            config: Optional sandbox configuration.
            **kwargs: Additional arguments for execute_python().

        Returns:
            ExecutionResult.
        """
        with self.sandbox(config=config) as container:
            return container.execute_python(code, **kwargs)

    def get_profile(self, profile_name: str) -> Optional[SandboxConfig]:
        """Get a predefined sandbox profile.

        Args:
            profile_name: Name of the profile.

        Returns:
            SandboxConfig or None.
        """
        profiles = {
            "readonly": SandboxProfile.readonly_filesystem(),
            "safe": SandboxProfile.safe_execution(),
            "network": SandboxProfile.network_allowed(),
        }
        profile = profiles.get(profile_name)
        return profile.config if profile else None

    def list_containers(self) -> list[str]:
        """List active container names.

        Returns:
            List of container names.
        """
        return list(self._containers.keys())

    def active_count(self) -> int:
        """Get number of active containers.

        Returns:
            Active container count.
        """
        return len(self._containers)

    def cleanup_all(self) -> None:
        """Clean up all containers."""
        for container in list(self._containers.values()):
            container._cleanup()
        self._containers.clear()
        self._active_count = 0

    def is_available(self) -> bool:
        """Check if sandbox execution is available.

        Returns:
            True if sandbox can be used.
        """
        try:
            container = self.create_container()
            container._setup_work_dir()
            return True
        except Exception:
            return False
        finally:
            self.cleanup_all()
