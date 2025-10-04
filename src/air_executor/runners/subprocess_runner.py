"""Subprocess-based task runner implementation."""

import os
import signal
import subprocess
import time
from typing import Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from ..core.job import Job
from ..core.task import Task


class SubprocessRunner:
    """
    Subprocess-based runner implementation.

    Spawns task execution as subprocess and manages lifecycle with
    SIGTERM → SIGKILL escalation for timeout enforcement.
    """

    def __init__(self, task_timeout: int = 1800):
        """
        Initialize subprocess runner.

        Args:
            task_timeout: Task timeout in seconds (default 30 minutes)
        """
        self.task_timeout = task_timeout

    def spawn(self, job: Job, task: Task) -> int:
        """
        Spawn subprocess for task execution.

        Executes: python -m air_executor.cli.main run-task --job {job_name} --task {task_id}

        Args:
            job: Job instance containing the task
            task: Task to execute

        Returns:
            Process ID of spawned subprocess

        Raises:
            OSError: If subprocess spawn fails
        """
        # Build command (no shell=True for security)
        # Use python -m to avoid CLI entry point issues
        cmd = [
            "python",
            "-m", "air_executor.cli.main",
            "run-task",
            "--job", job.name,
            "--task", task.id
        ]

        try:
            # Spawn subprocess in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent
            )
            return process.pid

        except (OSError, subprocess.SubprocessError) as e:
            raise OSError(f"Failed to spawn subprocess for task {task.id}: {e}")

    def is_alive(self, pid: int) -> bool:
        """
        Check if runner process is still active.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running, False otherwise
        """
        if HAS_PSUTIL:
            # Use psutil for reliable process checking
            try:
                process = psutil.Process(pid)
                return bool(process.is_running() and process.status() != psutil.STATUS_ZOMBIE)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
        else:
            # Fallback to os.kill(pid, 0)
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                return False

    def terminate(self, pid: int, timeout: int = 10) -> None:
        """
        Terminate runner gracefully (SIGTERM then SIGKILL).

        Args:
            pid: Process ID to terminate
            timeout: Seconds to wait between SIGTERM and SIGKILL

        Raises:
            OSError: If termination fails
        """
        if not self.is_alive(pid):
            return  # Already dead

        try:
            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)

            # Wait for process to exit
            for _ in range(timeout):
                time.sleep(1)
                if not self.is_alive(pid):
                    return  # Process exited gracefully

            # Still alive, send SIGKILL
            if self.is_alive(pid):
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)  # Brief wait for SIGKILL to take effect

        except (OSError, ProcessLookupError) as e:
            # Process may have exited during termination
            if self.is_alive(pid):
                raise OSError(f"Failed to terminate process {pid}: {e}")

    def wait_with_timeout(self, pid: int, timeout: Optional[int] = None) -> Optional[int]:
        """
        Wait for process to exit with optional timeout.

        Args:
            pid: Process ID to wait for
            timeout: Maximum seconds to wait (None = use task_timeout)

        Returns:
            Exit code if process exited, None if timeout

        Raises:
            OSError: If wait fails
        """
        if timeout is None:
            timeout = self.task_timeout

        if HAS_PSUTIL:
            try:
                process = psutil.Process(pid)
                exit_code = process.wait(timeout=timeout)
                return int(exit_code) if exit_code is not None else None
            except psutil.TimeoutExpired:
                return None
            except psutil.NoSuchProcess:
                return 0  # Already exited
        else:
            # Fallback: poll with is_alive
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self.is_alive(pid):
                    # Process exited, but we can't get exit code without psutil
                    return 0
                time.sleep(0.5)
            return None  # Timeout

    def __repr__(self) -> str:
        """Representation of subprocess runner."""
        return f"SubprocessRunner(timeout={self.task_timeout}s)"
