"""Unit tests for Task domain model and TaskQueue."""

import tempfile
from pathlib import Path

from air_executor.core.task import Task, TaskQueue, TaskStatus


def test_task_creation():
    """Test task creation with valid data."""
    task = Task(
        id="task-001",
        job_name="test-job",
        command="echo",
        args=["hello"],
        dependencies=[]
    )

    assert task.id == "task-001"
    assert task.job_name == "test-job"
    assert task.command == "echo"
    assert task.args == ["hello"]
    assert task.status == TaskStatus.PENDING
    assert task.started_at is None
    assert task.completed_at is None


def test_task_dependency_checking():
    """Test task dependency satisfaction checking."""
    task = Task(
        id="task-002",
        job_name="test-job",
        command="echo",
        dependencies=["task-001"]
    )

    # Not ready when dependency not completed
    assert task.is_ready(set()) is False

    # Ready when dependency completed
    assert task.is_ready({"task-001"}) is True


def test_task_status_transitions():
    """Test task status update methods."""
    task = Task(id="task-001", job_name="test-job", command="echo")

    # Mark running
    task.mark_running()
    assert task.status == TaskStatus.RUNNING
    assert task.started_at is not None

    # Mark completed
    task.mark_completed()
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None


def test_task_failure():
    """Test task failure handling."""
    task = Task(id="task-001", job_name="test-job", command="echo")

    task.mark_failed("Command not found")
    assert task.status == TaskStatus.FAILED
    assert task.error == "Command not found"
    assert task.completed_at is not None


def test_task_queue_operations():
    """Test task queue add and get operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tasks_file = Path(tmpdir) / "tasks.json"

        queue = TaskQueue("test-job", tasks_file)

        # Add task
        task1 = Task(id="task-001", job_name="test-job", command="echo")
        queue.add(task1)

        # Verify persistence
        assert tasks_file.exists()

        # Get all tasks
        all_tasks = queue.get_all()
        assert len(all_tasks) == 1
        assert all_tasks[0].id == "task-001"


def test_task_queue_pending_with_dependencies():
    """Test getting pending tasks with dependency resolution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tasks_file = Path(tmpdir) / "tasks.json"
        queue = TaskQueue("test-job", tasks_file)

        # Add tasks with dependencies
        task1 = Task(id="task-001", job_name="test-job", command="echo")
        task2 = Task(
            id="task-002",
            job_name="test-job",
            command="echo",
            dependencies=["task-001"]
        )

        queue.add(task1)
        queue.add(task2)

        # Only task1 should be pending (no dependencies)
        pending = queue.get_pending()
        assert len(pending) == 1
        assert pending[0].id == "task-001"

        # Mark task1 completed
        task1.mark_completed()
        queue.update(task1)

        # Now task2 should be pending
        pending = queue.get_pending()
        assert len(pending) == 1
        assert pending[0].id == "task-002"


def test_task_queue_atomic_updates():
    """Test that queue updates are atomic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tasks_file = Path(tmpdir) / "tasks.json"
        queue = TaskQueue("test-job", tasks_file)

        task = Task(id="task-001", job_name="test-job", command="echo")
        queue.add(task)

        # Update task
        task.mark_completed()
        queue.update(task)

        # Verify no temp file left
        assert not (tasks_file.parent / f".{tasks_file.name}.tmp").exists()

        # Reload and verify
        queue2 = TaskQueue("test-job", tasks_file)
        loaded_task = queue2.get_by_id("task-001")
        assert loaded_task.status == TaskStatus.COMPLETED
