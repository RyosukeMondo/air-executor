"""Runner spawner with PID tracking and lifecycle management."""

import concurrent.futures
import sys
from typing import List

from ..core.job import Job, JobState
from ..core.runner import Runner
from ..storage.file_store import FileStore


class RunnerSpawner:
    """
    Manages runner lifecycle with PID tracking.

    Enforces single-runner-per-job constraint and handles parallel
    spawning up to max_concurrent_runners limit.
    """

    def __init__(
        self,
        store: FileStore,
        runner: Runner,
        max_concurrent: int = 10,
    ):
        """
        Initialize runner spawner.

        Args:
            store: File store for PID tracking
            runner: Runner implementation for task execution
            max_concurrent: Maximum concurrent runner spawns
        """
        self.store = store
        self.runner = runner
        self.max_concurrent = max_concurrent

    def spawn_if_needed(self, jobs: List[Job]) -> None:
        """
        Spawn runners for jobs that need them (parallel up to max).

        Args:
            jobs: List of jobs to check for spawning needs
        """
        jobs_to_spawn = []

        for job in jobs:
            if self._should_spawn(job):
                jobs_to_spawn.append(job)

        if not jobs_to_spawn:
            return

        # Spawn in parallel up to max_concurrent
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = {executor.submit(self._spawn_one, job): job for job in jobs_to_spawn}

            for future in concurrent.futures.as_completed(futures):
                job = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"Error spawning runner for job {job.name}: {e}", file=sys.stderr)

    def _should_spawn(self, job: Job) -> bool:
        """
        Check if job needs a runner spawned.

        Args:
            job: Job to check

        Returns:
            True if runner should be spawned, False otherwise
        """
        # Reload job state fresh to avoid race conditions
        try:
            fresh_job = self.store.read_job_state(job.name)
        except Exception as e:
            print(f"Error reloading job state for {job.name}: {e}", file=sys.stderr)
            return False

        # Only spawn for jobs that can have runners
        if not fresh_job.can_spawn_runner():
            return False

        # Check if already has active runner
        if self._has_active_runner(fresh_job):
            return False

        # Check if job has pending tasks
        try:
            from ..core.task import TaskQueue

            task_queue = TaskQueue(
                fresh_job.name, self.store.jobs_path / fresh_job.name / "tasks.json"
            )
            return task_queue.has_pending()
        except Exception as e:
            print(f"Error checking tasks for job {fresh_job.name}: {e}", file=sys.stderr)
            return False

    def _has_active_runner(self, job: Job) -> bool:
        """
        Check if job has active runner via PID file.

        Args:
            job: Job to check

        Returns:
            True if active runner exists, False otherwise
        """
        pid = self.store.read_pid_file(job.name)
        if pid is None:
            return False

        # Check if process is still alive
        if self.runner.is_alive(pid):
            return True

        # Stale PID file - clean it up
        self._cleanup_stale_pid(job)
        return False

    def _spawn_one(self, job: Job) -> None:
        """
        Spawn single runner for job with PID tracking.

        Args:
            job: Job to spawn runner for

        Raises:
            OSError: If spawn fails
        """
        fresh_job = self._reload_job_state(job.name)
        task = self._get_next_task(fresh_job)

        if task is None:
            return  # No work to do

        self._execute_spawn(fresh_job, task)

    def _reload_job_state(self, job_name: str) -> Job:
        """
        Reload fresh job state to avoid race conditions.

        Args:
            job_name: Name of job to reload

        Returns:
            Fresh job instance

        Raises:
            OSError: If reload fails
        """
        try:
            return self.store.read_job_state(job_name)
        except Exception as e:
            raise OSError(f"Failed to reload job state for {job_name}: {e}")

    def _get_next_task(self, job: Job):
        """
        Get next pending task for job.

        Args:
            job: Job to get task for

        Returns:
            Next pending task or None if no tasks
        """
        from ..core.task import TaskQueue

        task_queue = TaskQueue(job.name, self.store.jobs_path / job.name / "tasks.json")
        pending_tasks = task_queue.get_pending()

        if not pending_tasks:
            return None

        return pending_tasks[0]

    def _execute_spawn(self, job: Job, task) -> None:
        """
        Execute runner spawn with state management.

        Args:
            job: Job to spawn runner for
            task: Task to execute

        Raises:
            OSError: If spawn fails
        """
        try:
            self._transition_to_working(job)
            pid = self.runner.spawn(job, task)
            self._create_pid_file(job, pid)
            print(f"Spawned runner (PID {pid}) for job {job.name}, task {task.id}")
        except Exception as e:
            self._cleanup_failed_spawn(job)
            raise OSError(f"Failed to spawn runner for job {job.name}: {e}")

    def _transition_to_working(self, job: Job) -> None:
        """
        Transition job to WORKING state.

        Args:
            job: Job to transition
        """
        job.transition_to(JobState.WORKING)
        self.store.write_job_state(job)

    def _cleanup_failed_spawn(self, job: Job) -> None:
        """
        Clean up after failed spawn attempt.

        Args:
            job: Job to clean up
        """
        try:
            job.transition_to(JobState.WAITING)
            self.store.write_job_state(job)
        except Exception:
            pass  # Ignore state transition errors during cleanup
        self.store.remove_pid_file(job.name)

    def _create_pid_file(self, job: Job, pid: int) -> None:
        """
        Create PID file at jobs/{name}/runner.pid.

        Args:
            job: Job instance
            pid: Process ID to write

        Raises:
            OSError: If PID file creation fails
        """
        self.store.write_pid_file(job.name, pid)

    def _cleanup_stale_pid(self, job: Job) -> None:
        """
        Remove PID file if process is dead.

        Args:
            job: Job with stale PID
        """
        print(f"Cleaning up stale PID file for job {job.name}", file=sys.stderr)
        self.store.remove_pid_file(job.name)

    def __repr__(self) -> str:
        """Representation of spawner."""
        return f"RunnerSpawner(max_concurrent={self.max_concurrent})"
