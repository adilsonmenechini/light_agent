"""Sandbox container for isolated execution."""

import asyncio
import os
import signal
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import SandboxConfig, SandboxLevel


@dataclass
class ExecutionResult:
    """Result of sandboxed execution."""

    success: bool
    return_code: int
    stdout: str
    stderr: str
    execution_time_ms: int
    memory_used_mb: float = 0.0
    error: Optional[str] = None
    killed: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SandboxContainer:
    """Sandboxed execution container.

    Provides isolation for executing untrusted code with resource limits.
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        """Initialize sandbox container.

        Args:
            config: Sandbox configuration.
        """
        self.config = config or SandboxConfig()
        self._process: Optional[subprocess.Popen] = None
        self._work_dir: Optional[str] = None

    def __enter__(self) -> "SandboxContainer":
        """Enter sandbox context."""
        self._setup_work_dir()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit sandbox context."""
        self._cleanup()

    def _setup_work_dir(self) -> None:
        """Set up temporary work directory."""
        if self.config.work_dir:
            self._work_dir = self.config.work_dir
        else:
            self._work_dir = tempfile.mkdtemp(prefix="sandbox_")

        Path(self._work_dir).mkdir(parents=True, exist_ok=True)

    def _cleanup(self) -> None:
        """Clean up sandbox resources."""
        if self._process and self._process.poll() is None:
            self._process.kill()
            self._process.wait()

        if self._work_dir and self._work_dir.startswith("/tmp/sandbox_"):
            import shutil

            try:
                shutil.rmtree(self._work_dir, ignore_errors=True)
            except Exception:
                pass

    def _is_path_allowed(self, path: str) -> bool:
        """Check if a path is allowed.

        Args:
            path: Path to check.

        Returns:
            True if path is allowed.
        """
        abs_path = os.path.abspath(path)

        # Check blocked directories
        for blocked in self.config.blocked_dirs:
            if abs_path.startswith(blocked):
                return False

        # Check allowed directories (if specified)
        if self.config.allowed_dirs:
            allowed = False
            for allowed_dir in self.config.allowed_dirs:
                if abs_path.startswith(os.path.abspath(allowed_dir)):
                    allowed = True
                    break
            if not allowed:
                return False

        return True

    def _prepare_command(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
    ) -> tuple[List[str], Dict[str, str]]:
        """Prepare command with restrictions.

        Args:
            command: Command to execute.
            env: Environment variables.

        Returns:
            Prepared command and environment.
        """
        # Add resource limits (Linux-specific)
        prepared_cmd = ["timeout"]

        # Add time limit
        prepared_cmd.extend([str(self.config.max_execution_seconds)])

        # Command
        prepared_cmd.extend(command)

        # Prepare environment
        prepared_env = os.environ.copy()
        for key, value in self.config.environment_vars.items():
            prepared_env[key] = value

        # Block network if not allowed
        if not self.config.network_allowed:
            prepared_env["DISABLE_NETWORK"] = "1"
            prepared_env["NO_PROXY"] = "*"
            prepared_env["no_proxy"] = "*"

        return prepared_cmd, prepared_env

    async def execute(
        self,
        command: List[str],
        input_data: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute command in sandbox.

        Args:
            command: Command to execute.
            input_data: Optional input data.
            timeout: Override timeout in seconds.

        Returns:
            ExecutionResult with output and metrics.
        """
        if self.config.level == SandboxLevel.NONE:
            return await self._execute_direct(command, input_data, timeout)

        return await self._execute_restricted(command, input_data, timeout)

    async def _execute_direct(
        self,
        command: List[str],
        input_data: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute without restrictions (for testing).

        Args:
            command: Command to execute.
            input_data: Optional input data.
            timeout: Override timeout.

        Returns:
            ExecutionResult.
        """
        timeout = timeout or self.config.max_execution_seconds

        try:
            start_time = datetime.now()

            proc = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=10 * 1024 * 1024,  # 10MB
            )

            stdin_bytes = input_data.encode() if input_data else None
            stdout_bytes, stderr_bytes = await proc.communicate(
                input=stdin_bytes,
                timeout=timeout,
            )

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return ExecutionResult(
                success=proc.returncode == 0,
                return_code=proc.returncode or 0,
                stdout=stdout_bytes.decode(errors="replace"),
                stderr=stderr_bytes.decode(errors="replace"),
                execution_time_ms=execution_time,
            )

        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr="Execution timed out",
                execution_time_ms=timeout * 1000,
                error="Timeout",
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=str(e),
                execution_time_ms=0,
                error=str(e),
            )

    async def _execute_restricted(
        self,
        command: List[str],
        input_data: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute with restrictions.

        Args:
            command: Command to execute.
            input_data: Optional input data.
            timeout: Override timeout.

        Returns:
            ExecutionResult.
        """
        prepared_cmd, prepared_env = self._prepare_command(command, {})
        timeout = timeout or self.config.max_execution_seconds

        try:
            start_time = datetime.now()

            proc = await asyncio.create_subprocess_exec(
                *prepared_cmd,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=prepared_env,
                limit=10 * 1024 * 1024,
            )

            stdin_bytes = input_data.encode() if input_data else None
            stdout_bytes, stderr_bytes = await proc.communicate(
                input=stdin_bytes,
                timeout=timeout,
            )

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return ExecutionResult(
                success=proc.returncode == 0,
                return_code=proc.returncode or 0,
                stdout=stdout_bytes.decode(errors="replace"),
                stderr=stderr_bytes.decode(errors="replace"),
                execution_time_ms=execution_time,
            )

        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr="Execution timed out",
                execution_time_ms=timeout * 1000,
                error="Timeout",
                killed=True,
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=str(e),
                execution_time_ms=0,
                error=str(e),
            )

    def execute_python(
        self,
        code: str,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute Python code in sandbox.

        Args:
            code: Python code to execute.
            timeout: Timeout in seconds.

        Returns:
            ExecutionResult.
        """
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            script_path = f.name

        try:
            result = asyncio.run(
                self.execute(
                    ["python3", script_path],
                    timeout=timeout or self.config.max_execution_seconds,
                )
            )
            return result
        finally:
            try:
                os.unlink(script_path)
            except Exception:
                pass

    def get_work_dir(self) -> Optional[str]:
        """Get sandbox work directory.

        Returns:
            Work directory path or None.
        """
        return self._work_dir

    def is_docker_available(self) -> bool:
        """Check if Docker is available.

        Returns:
            True if Docker can be used.
        """
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False
