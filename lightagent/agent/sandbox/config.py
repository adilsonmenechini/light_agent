"""Configuration for sandbox isolation."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class SandboxLevel(Enum):
    """Sandbox isolation levels."""

    NONE = "none"  # No isolation
    PROCESS = "process"  # Process-level isolation (default on Linux)
    DOCKER = "docker"  # Docker container isolation
    FIRECRACKER = "firecracker"  # MicroVM isolation (not yet implemented)


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution.

    Attributes:
        enabled: Whether sandbox isolation is enabled.
        level: Isolation level to use.
        max_memory_mb: Maximum memory in megabytes.
        max_cpu_seconds: Maximum CPU time in seconds.
        max_execution_seconds: Maximum total execution time.
        max_file_size_mb: Maximum file size in megabytes.
        allowed_dirs: List of allowed directories (empty = all denied).
        blocked_dirs: List of blocked directories.
        network_allowed: Whether network access is allowed.
        environment_vars: Allowed environment variables.
        work_dir: Working directory for sandbox.
    """

    enabled: bool = True
    level: SandboxLevel = SandboxLevel.PROCESS
    max_memory_mb: int = 512
    max_cpu_seconds: int = 30
    max_execution_seconds: int = 60
    max_file_size_mb: int = 100
    allowed_dirs: list[str] = field(default_factory=list)
    blocked_dirs: list[str] = field(
        default_factory=lambda: [
            "/etc",
            "/root",
            "/home",
            "/var/log",
            "/proc",
            "/sys",
            "/dev",
        ]
    )
    network_allowed: bool = False
    environment_vars: dict[str, str] = field(default_factory=dict)
    work_dir: Optional[str] = None


def default_sandbox_config() -> SandboxConfig:
    """Get default sandbox configuration."""
    return SandboxConfig()


@dataclass
class SandboxProfile:
    """Predefined sandbox profiles for different use cases."""

    name: str
    description: str
    config: SandboxConfig

    @staticmethod
    def readonly_filesystem() -> "SandboxProfile":
        """Read-only filesystem profile."""
        return SandboxProfile(
            name="readonly_fs",
            description="Read-only filesystem with limited memory",
            config=SandboxConfig(
                max_memory_mb=256,
                max_cpu_seconds=10,
                max_execution_seconds=30,
                allowed_dirs=["/tmp"],
            ),
        )

    @staticmethod
    def safe_execution() -> "SandboxProfile":
        """Safe execution profile for untrusted code."""
        return SandboxProfile(
            name="safe_exec",
            description="Safe execution with memory and time limits",
            config=SandboxConfig(
                max_memory_mb=512,
                max_cpu_seconds=30,
                max_execution_seconds=60,
                allowed_dirs=["/tmp", "/workspace"],
                network_allowed=False,
            ),
        )

    @staticmethod
    def network_allowed() -> "SandboxProfile":
        """Network-enabled sandbox for API calls."""
        return SandboxProfile(
            name="network_ok",
            description="Sandbox with network access",
            config=SandboxConfig(
                max_memory_mb=1024,
                max_cpu_seconds=60,
                max_execution_seconds=120,
                allowed_dirs=["/tmp", "/workspace"],
                network_allowed=True,
            ),
        )
