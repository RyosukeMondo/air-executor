"""File-based storage with atomic operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.job import Job
from ..core.task import Task


class FileStore:
    """
    File-based storage with atomic write operations.

    Provides reliable persistence for job state and task queues using
    atomic file writes (write to temp file, then rename).
    """

    def __init__(self, base_path: Path = Path(".air-executor")):
        """
        Initialize file store.

        Args:
            base_path: Base directory for all storage (default: .air-executor)
        """
        self.base_path = base_path
        self.jobs_path = base_path / "jobs"

    def read_json(self, path: Path) -> Dict[str, Any]:
        """
        Read JSON file with error handling.

        Args:
            path: Path to JSON file

        Returns:
            Parsed JSON data as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file contains invalid JSON
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        try:
            with open(path, "r") as f:
                data: Dict[str, Any] = json.load(f)
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}")

    def write_json(self, path: Path, data: Union[Dict[str, Any], List[Any]]) -> None:
        """
        Write JSON atomically (write to temp, then rename).

        Args:
            path: Path to JSON file
            data: Data to write

        Raises:
            OSError: If write fails
        """
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Write to temporary file in same directory
        temp_path = path.parent / f".{path.name}.tmp"
        try:
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename
            temp_path.rename(path)
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to write JSON to {path}: {e}")

    def read_job_state(self, job_name: str) -> Job:
        """
        Read job state from jobs/{name}/state.json.

        Args:
            job_name: Name of the job

        Returns:
            Job instance loaded from state file

        Raises:
            FileNotFoundError: If job state file doesn't exist
            ValueError: If state file is invalid
        """
        state_path = self.jobs_path / job_name / "state.json"
        return Job.from_file(state_path)

    def write_job_state(self, job: Job) -> None:
        """
        Write job state to jobs/{name}/state.json atomically.

        Args:
            job: Job instance to save

        Raises:
            OSError: If write fails
        """
        state_path = self.jobs_path / job.name / "state.json"
        job.to_file(state_path)

    def read_tasks(self, job_name: str) -> List[Task]:
        """
        Read task list from jobs/{name}/tasks.json.

        Args:
            job_name: Name of the job

        Returns:
            List of tasks for the job

        Raises:
            FileNotFoundError: If tasks file doesn't exist
            ValueError: If tasks file is invalid
        """
        tasks_path = self.jobs_path / job_name / "tasks.json"
        if not tasks_path.exists():
            return []

        try:
            data = self.read_json(tasks_path)
            if isinstance(data, list):
                return [Task(**task_data) for task_data in data]
            return []
        except Exception as e:
            raise ValueError(f"Failed to read tasks from {tasks_path}: {e}")

    def write_tasks(self, job_name: str, tasks: List[Task]) -> None:
        """
        Write task list to jobs/{name}/tasks.json atomically.

        Args:
            job_name: Name of the job
            tasks: List of tasks to save

        Raises:
            OSError: If write fails
        """
        tasks_path = self.jobs_path / job_name / "tasks.json"
        data = [task.model_dump() for task in tasks]
        self.write_json(tasks_path, data)

    def list_jobs(self) -> List[str]:
        """
        List all job directories.

        Returns:
            List of job names (directory names in jobs/)

        Raises:
            OSError: If directory listing fails
        """
        if not self.jobs_path.exists():
            return []

        try:
            return [
                d.name
                for d in self.jobs_path.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            ]
        except OSError as e:
            raise OSError(f"Failed to list jobs: {e}")

    def create_job_dir(self, job_name: str) -> Path:
        """
        Create job directory structure.

        Creates:
        - jobs/{name}/
        - jobs/{name}/state.json (empty job state)
        - jobs/{name}/tasks.json (empty array)
        - jobs/{name}/logs/ (directory)

        Args:
            job_name: Name of the job

        Returns:
            Path to created job directory

        Raises:
            ValueError: If job directory already exists
            OSError: If directory creation fails
        """
        job_dir = self.jobs_path / job_name

        if job_dir.exists():
            raise ValueError(f"Job directory already exists: {job_dir}")

        try:
            # Create directory structure with restricted permissions
            job_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
            logs_dir = job_dir / "logs"
            logs_dir.mkdir(mode=0o700)

            # Create empty tasks.json
            tasks_path = job_dir / "tasks.json"
            self.write_json(tasks_path, [])

            return job_dir
        except OSError as e:
            raise OSError(f"Failed to create job directory {job_dir}: {e}")

    def job_exists(self, job_name: str) -> bool:
        """
        Check if job directory exists.

        Args:
            job_name: Name of the job

        Returns:
            True if job directory exists, False otherwise
        """
        job_dir = self.jobs_path / job_name
        return job_dir.exists() and job_dir.is_dir()

    def get_job_dir(self, job_name: str) -> Path:
        """
        Get path to job directory.

        Args:
            job_name: Name of the job

        Returns:
            Path to job directory

        Raises:
            ValueError: If job directory doesn't exist
        """
        job_dir = self.jobs_path / job_name
        if not self.job_exists(job_name):
            raise ValueError(f"Job directory not found: {job_dir}")
        return job_dir

    def read_pid_file(self, job_name: str) -> Optional[int]:
        """
        Read runner PID from jobs/{name}/runner.pid.

        Args:
            job_name: Name of the job

        Returns:
            PID if file exists and is valid, None otherwise
        """
        pid_path = self.jobs_path / job_name / "runner.pid"
        if not pid_path.exists():
            return None

        try:
            with open(pid_path, "r") as f:
                first_line = f.readline().strip()
                return int(first_line)
        except (ValueError, OSError):
            return None

    def write_pid_file(self, job_name: str, pid: int) -> None:
        """
        Write runner PID to jobs/{name}/runner.pid.

        Args:
            job_name: Name of the job
            pid: Process ID to write

        Raises:
            OSError: If write fails
        """
        pid_path = self.jobs_path / job_name / "runner.pid"
        try:
            with open(pid_path, "w") as f:
                f.write(f"{pid}\n")
                f.write(f"{datetime.now(timezone.utc).isoformat()}\n")
                f.flush()
                os.fsync(f.fileno())
        except OSError as e:
            raise OSError(f"Failed to write PID file {pid_path}: {e}")

    def remove_pid_file(self, job_name: str) -> None:
        """
        Remove runner PID file.

        Args:
            job_name: Name of the job
        """
        pid_path = self.jobs_path / job_name / "runner.pid"
        if pid_path.exists():
            try:
                pid_path.unlink()
            except OSError:
                pass  # Ignore errors on cleanup

    def __repr__(self) -> str:
        """Representation of file store."""
        return f"FileStore(base_path={self.base_path})"
