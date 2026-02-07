"""Context manager to suppress stdout/stderr output."""

import os
import sys
from contextlib import contextmanager


@contextmanager
def suppress_output():
    """Temporarily suppress stdout and stderr."""
    # Save original file descriptors
    stdout_fd = sys.stdout.fileno()
    stderr_fd = sys.stderr.fileno()

    # Save copies of original stdout/stderr
    with (
        os.fdopen(os.dup(stdout_fd), "w") as stdout_copy,
        os.fdopen(os.dup(stderr_fd), "w") as stderr_copy,
    ):
        # Redirect to devnull
        devnull = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(devnull, stdout_fd)
            os.dup2(devnull, stderr_fd)
            yield
        finally:
            # Restore original stdout/stderr
            os.dup2(stdout_copy.fileno(), stdout_fd)
            os.dup2(stderr_copy.fileno(), stderr_fd)
            os.close(devnull)
