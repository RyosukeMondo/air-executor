"""Job poller with polling loop and signal handling."""

import signal
import sys
import time
from typing import Optional

from ..core.job import Job, JobState
from ..core.task import TaskQueue
from ..storage.file_store import FileStore
from .config import Config
from .spawner import RunnerSpawner


class JobPoller:
    """
    Polling loop that discovers jobs and triggers spawning.

    Monitors job directories, checks for pending tasks and active runners,
    and invokes RunnerSpawner for jobs that need work. Handles SIGTERM
    for graceful shutdown.
    """

    def __init__(
        self,
        store: FileStore,
        spawner: RunnerSpawner,
        config: Config,
    ):
        """
        Initialize job poller.

        Args:
            store: File store for job discovery
            spawner: Runner spawner for lifecycle management
            config: Configuration settings
        """
        self.store = store
        self.spawner = spawner
        self.config = config
        self._running = False
        self._shutdown_requested = False

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        """Handle SIGTERM/SIGINT for graceful shutdown."""
        print("\nShutdown requested, completing current poll cycle...", file=sys.stderr)
        self._shutdown_requested = True

    def start(self) -> None:
        """
        Start polling loop (blocks until SIGTERM).

        Continuously polls jobs and spawns runners until shutdown signal.
        """
        self._running = True
        self._shutdown_requested = False

        print(f"Job manager started (poll interval: {self.config.poll_interval}s)")

        try:
            while self._running and not self._shutdown_requested:
                self.poll_once()
                time.sleep(self.config.poll_interval)
        finally:
            self.stop()

    def poll_once(self) -> None:
        """
        Execute single poll cycle across all jobs.

        Discovers jobs, checks states, updates completed jobs,
        and spawns runners for jobs with pending work.
        """
        try:
            # Discover all jobs
            job_names = self.store.list_jobs()

            jobs_to_spawn = []

            for job_name in job_names:
                try:
                    job = self._check_job(job_name)
                    if job is not None:
                        jobs_to_spawn.append(job)
                except Exception as e:
                    self._handle_error(job_name, e)

            # Spawn runners in parallel
            if jobs_to_spawn:
                self.spawner.spawn_if_needed(jobs_to_spawn)

        except Exception as e:
            print(f"Error in poll cycle: {e}", file=sys.stderr)

    def _check_job(self, job_name: str) -> Optional[Job]:
        """
        Check single job and return if needs runner.

        Args:
            job_name: Name of job to check

        Returns:
            Job instance if runner needed, None otherwise

        Raises:
            Exception: If job checking fails
        """
        # Load job state
        job = self.store.read_job_state(job_name)

        # Load task queue
        task_queue = TaskQueue(job_name, self.store.jobs_path / job_name / "tasks.json")

        # Check for job completion
        if job.state == JobState.WORKING:
            # Check if no pending tasks and no active runner
            has_pending = task_queue.has_pending()
            has_active_runner = self._has_active_runner(job_name)

            if not has_pending and not has_active_runner:
                # Job completed
                if task_queue.has_failed():
                    job.transition_to(JobState.FAILED)
                    print(f"Job {job_name} failed (tasks failed)")
                else:
                    job.transition_to(JobState.COMPLETED)
                    self._log_completion_stats(job, task_queue)

                self.store.write_job_state(job)
                return None

        # Check if job needs runner
        if job.state in {JobState.WAITING, JobState.WORKING}:
            has_pending = task_queue.has_pending()
            has_active_runner = self._has_active_runner(job_name)

            if has_pending and not has_active_runner:
                return job

        return None

    def _has_active_runner(self, job_name: str) -> bool:
        """
        Check if job has active runner.

        Args:
            job_name: Name of job to check

        Returns:
            True if active runner exists, False otherwise
        """
        pid = self.store.read_pid_file(job_name)
        if pid is None:
            return False

        # Use spawner's runner to check if alive
        return self.spawner.runner.is_alive(pid)

    def _log_completion_stats(self, job: Job, task_queue: TaskQueue) -> None:
        """
        Log completion time and task statistics.

        Args:
            job: Completed job
            task_queue: Task queue with statistics
        """
        tasks = task_queue.get_all()
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status.value == "completed")
        failed = sum(1 for t in tasks if t.status.value == "failed")

        print(
            f"Job {job.name} completed: " f"{total} tasks ({completed} succeeded, {failed} failed)"
        )

    def _handle_error(self, job_name: str, error: Exception) -> None:
        """
        Handle error for single job without crashing.

        Args:
            job_name: Job that encountered error
            error: Exception that occurred
        """
        print(f"Error checking job {job_name}: {error}", file=sys.stderr)

    def stop(self) -> None:
        """Stop polling loop gracefully."""
        self._running = False
        print("Job manager stopped")

    def __repr__(self) -> str:
        """Representation of poller."""
        return f"JobPoller(poll_interval={self.config.poll_interval}s)"
