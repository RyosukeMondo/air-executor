"""State store interfaces."""

from abc import ABC, abstractmethod

from ..models import Task


class ITaskRepository(ABC):
    """Interface for task storage and retrieval."""

    @abstractmethod
    def queue_task(self, task: Task) -> None:
        """
        Add task to queue.

        Args:
            task: Task to queue
        """
        pass

    @abstractmethod
    def get_next_tasks(self, count: int = 5) -> list[Task]:
        """
        Get highest priority tasks.

        Args:
            count: Number of tasks to retrieve

        Returns:
            List of tasks
        """
        pass

    @abstractmethod
    def mark_task_complete(self, task_id: str) -> None:
        """
        Mark task as completed.

        Args:
            task_id: Task ID
        """
        pass

    @abstractmethod
    def mark_task_failed(self, task_id: str, error_message: str) -> None:
        """
        Mark task as failed.

        Args:
            task_id: Task ID
            error_message: Error message
        """
        pass

    @abstractmethod
    def get_task_status(self, task_id: str) -> str | None:
        """
        Get task status.

        Args:
            task_id: Task ID

        Returns:
            Task status or None if not found
        """
        pass


class IStateStore(ABC):
    """Interface for general state storage."""

    @abstractmethod
    def store_session_summary(self, phase: str, summary: dict) -> None:
        """
        Store session summary.

        Args:
            phase: Phase name ('build', 'test', 'lint')
            summary: Summary data
        """
        pass

    @abstractmethod
    def get_session_summary(self, phase: str) -> dict | None:
        """
        Get session summary.

        Args:
            phase: Phase name

        Returns:
            Summary data or None
        """
        pass

    @abstractmethod
    def record_run_result(self, run_id: str, metrics: dict) -> None:
        """
        Record orchestrator run result.

        Args:
            run_id: Run ID
            metrics: Health metrics
        """
        pass

    @abstractmethod
    def get_run_history(self, count: int = 10) -> list[dict]:
        """
        Get recent run history.

        Args:
            count: Number of runs to retrieve

        Returns:
            List of run data
        """
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """
        Get statistics.

        Returns:
            Stats dictionary
        """
        pass

    @abstractmethod
    def increment_failure_count(self) -> None:
        """Increment consecutive failure counter."""
        pass

    @abstractmethod
    def reset_failure_count(self) -> None:
        """Reset consecutive failure counter."""
        pass

    @abstractmethod
    def is_circuit_open(self, max_failures: int) -> bool:
        """
        Check if circuit breaker is open.

        Args:
            max_failures: Maximum consecutive failures

        Returns:
            True if circuit is open
        """
        pass
