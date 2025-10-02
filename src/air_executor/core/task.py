"""Task domain model and queue management."""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    """
    Represents an executable task with dependencies.

    Tasks are atomic units of work executed by ephemeral runners.
    They can depend on other tasks and track execution lifecycle.
    """

    id: str = Field(..., description="Unique task identifier")
    job_name: str = Field(..., description="Name of parent job")
    command: str = Field(..., description="Command to execute")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this task depends on")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion timestamp")
    error: Optional[str] = Field(default=None, description="Error message if task failed")

    def is_ready(self, completed_task_ids: Set[str]) -> bool:
        """
        Check if all dependencies are satisfied.

        Args:
            completed_task_ids: Set of task IDs that have completed

        Returns:
            True if all dependencies are completed, False otherwise
        """
        if not self.dependencies:
            return True
        return all(dep_id in completed_task_ids for dep_id in self.dependencies)

    def mark_running(self) -> None:
        """Mark task as running with timestamp."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Mark task as completed with timestamp."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """
        Mark task as failed with error message.

        Args:
            error: Error message describing the failure
        """
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error

    def to_dict(self) -> dict:
        """Convert task to dictionary representation."""
        return self.model_dump()

    def __str__(self) -> str:
        """String representation of task."""
        return f"Task(id={self.id}, status={self.status.value})"

    def __repr__(self) -> str:
        """Detailed representation of task."""
        return f"Task(id={self.id}, job={self.job_name}, command={self.command}, status={self.status.value})"


class TaskQueue:
    """
    Manages task collection with atomic persistence.

    Provides thread-safe operations for adding, updating, and querying tasks.
    Backed by file storage for durability.
    """

    def __init__(self, job_name: str, tasks_file: Path):
        """
        Initialize task queue.

        Args:
            job_name: Name of the job this queue belongs to
            tasks_file: Path to tasks.json file
        """
        self.job_name = job_name
        self.tasks_file = tasks_file
        self._tasks: List[Task] = []
        self._load()

    def _load(self) -> None:
        """Load tasks from file if exists."""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, "r") as f:
                    data = json.load(f)
                self._tasks = [Task(**task_data) for task_data in data]
            except (json.JSONDecodeError, ValueError) as e:
                # Log error but don't crash - start with empty queue
                import sys
                print(f"Warning: Failed to load tasks from {self.tasks_file}: {e}", file=sys.stderr)
                self._tasks = []

    def _save(self) -> None:
        """Save tasks to file atomically."""
        import tempfile
        import os

        # Ensure parent directory exists
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file
        temp_path = self.tasks_file.parent / f".{self.tasks_file.name}.tmp"
        try:
            with open(temp_path, "w") as f:
                data = [task.model_dump() for task in self._tasks]
                json.dump(data, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename
            temp_path.rename(self.tasks_file)
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to save tasks to {self.tasks_file}: {e}")

    def add(self, task: Task) -> None:
        """
        Add task to queue atomically.

        Args:
            task: Task to add

        Raises:
            ValueError: If task with same ID already exists
        """
        if any(t.id == task.id for t in self._tasks):
            raise ValueError(f"Task with ID {task.id} already exists")

        self._tasks.append(task)
        self._save()

    def get_pending(self) -> List[Task]:
        """
        Get all pending tasks with satisfied dependencies.

        Returns:
            List of tasks that are pending and ready to run
        """
        completed_ids = self.get_completed_ids()
        return [
            task
            for task in self._tasks
            if task.status == TaskStatus.PENDING and task.is_ready(completed_ids)
        ]

    def get_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task if found, None otherwise
        """
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def update(self, task: Task) -> None:
        """
        Update task status atomically.

        Args:
            task: Task with updated status

        Raises:
            ValueError: If task not found in queue
        """
        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                self._save()
                return
        raise ValueError(f"Task {task.id} not found in queue")

    def get_completed_ids(self) -> Set[str]:
        """
        Get set of completed task IDs for dependency checking.

        Returns:
            Set of task IDs with completed status
        """
        return {task.id for task in self._tasks if task.status == TaskStatus.COMPLETED}

    def get_all(self) -> List[Task]:
        """
        Get all tasks in queue.

        Returns:
            List of all tasks
        """
        return self._tasks.copy()

    def has_pending(self) -> bool:
        """
        Check if queue has any pending tasks.

        Returns:
            True if any tasks are pending, False otherwise
        """
        return any(task.status == TaskStatus.PENDING for task in self._tasks)

    def has_failed(self) -> bool:
        """
        Check if any tasks have failed.

        Returns:
            True if any tasks are failed, False otherwise
        """
        return any(task.status == TaskStatus.FAILED for task in self._tasks)

    def __len__(self) -> int:
        """Return number of tasks in queue."""
        return len(self._tasks)

    def __repr__(self) -> str:
        """Representation of task queue."""
        return f"TaskQueue(job={self.job_name}, tasks={len(self._tasks)})"
