"""Runner interface for task execution."""

from typing import Protocol

from .job import Job
from .task import Task


class Runner(Protocol):
    """
    Protocol for task runner implementations.

    Defines the contract for executing tasks in various environments
    (subprocess, Docker, Kubernetes, etc.).
    """

    def spawn(self, job: Job, task: Task) -> int:
        """
        Spawn runner process for task execution.

        Args:
            job: Job instance containing the task
            task: Task to execute

        Returns:
            Process ID of spawned runner

        Raises:
            OSError: If spawn fails
        """
        ...

    def is_alive(self, pid: int) -> bool:
        """
        Check if runner process is still active.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running, False otherwise
        """
        ...

    def terminate(self, pid: int, timeout: int = 10) -> None:
        """
        Terminate runner gracefully (SIGTERM then SIGKILL).

        Args:
            pid: Process ID to terminate
            timeout: Seconds to wait between SIGTERM and SIGKILL

        Raises:
            OSError: If termination fails
        """
        ...
