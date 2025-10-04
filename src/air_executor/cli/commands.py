"""CLI command implementations."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from ..core.job import JobState
from ..core.task import TaskQueue, TaskStatus
from ..manager.config import Config
from ..manager.poller import JobPoller
from ..manager.spawner import RunnerSpawner
from ..runners.subprocess_runner import SubprocessRunner
from ..storage.file_store import FileStore

console = Console()


def start_manager(config_path: Optional[Path] = None) -> None:
    """
    Start job manager in background.

    Args:
        config_path: Optional path to config file
    """
    # Load config
    if config_path:
        config = Config.from_file(config_path)
    else:
        config = Config.load_or_default()

    # Check if already running
    pid_file = config.base_path / "manager.pid"
    if pid_file.exists():
        try:
            with open(pid_file, "r") as f:
                existing_pid = int(f.read().strip())
            # Check if process is still alive
            try:
                os.kill(existing_pid, 0)
                console.print(f"[red]Job manager already running (PID {existing_pid})[/red]")
                sys.exit(1)
            except ProcessLookupError:
                # Stale PID file
                pid_file.unlink()
        except (ValueError, OSError):
            pid_file.unlink()

    # Fork to background
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process
            console.print(f"[green]Job manager started (PID {pid})[/green]")
            sys.exit(0)
    except OSError as e:
        console.print(f"[red]Failed to fork process: {e}[/red]")
        sys.exit(1)

    # Child process continues
    # Detach from terminal
    os.setsid()

    # Write PID file
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    # Redirect stdout/stderr to log file
    log_file = config.base_path / "manager.log"
    log_fd = open(log_file, "a")
    os.dup2(log_fd.fileno(), sys.stdout.fileno())
    os.dup2(log_fd.fileno(), sys.stderr.fileno())

    # Initialize components
    store = FileStore(config.base_path)
    runner = SubprocessRunner(config.task_timeout)
    spawner = RunnerSpawner(store, runner, config.max_concurrent_runners)
    poller = JobPoller(store, spawner, config)

    # Start polling loop
    try:
        poller.start()
    finally:
        # Clean up PID file
        if pid_file.exists():
            pid_file.unlink()


def stop_manager() -> None:
    """Stop job manager gracefully."""
    config = Config.load_or_default()
    pid_file = config.base_path / "manager.pid"

    if not pid_file.exists():
        console.print("[yellow]Job manager is not running[/yellow]")
        return

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        # Check if process exists
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            console.print("[yellow]Job manager process not found (stale PID)[/yellow]")
            pid_file.unlink()
            return

        # Send SIGTERM
        console.print(f"Stopping job manager (PID {pid})...")
        os.kill(pid, signal.SIGTERM)

        # Wait for shutdown (max 15 seconds)
        for i in range(15):
            time.sleep(1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                console.print("[green]Job manager stopped[/green]")
                if pid_file.exists():
                    pid_file.unlink()
                return

        # Still running, force kill
        console.print("[yellow]Job manager did not stop gracefully, forcing...[/yellow]")
        os.kill(pid, signal.SIGKILL)
        time.sleep(1)
        console.print("[green]Job manager stopped (forced)[/green]")
        if pid_file.exists():
            pid_file.unlink()

    except (ValueError, OSError) as e:
        console.print(f"[red]Error stopping manager: {e}[/red]")
        sys.exit(1)


def show_status(job_filter: Optional[str] = None) -> None:
    """
    Display job status table.

    Args:
        job_filter: Optional job name filter
    """
    config = Config.load_or_default()
    store = FileStore(config.base_path)

    try:
        job_names = store.list_jobs()
        if job_filter:
            job_names = [name for name in job_names if name == job_filter]

        if not job_names:
            console.print("[yellow]No jobs found[/yellow]")
            return

        # Create table
        table = Table(title="Job Status")
        table.add_column("Job Name", style="cyan")
        table.add_column("State", style="magenta")
        table.add_column("Pending Tasks", justify="right")
        table.add_column("Active Runner", justify="center")
        table.add_column("Updated At", style="dim")

        for job_name in sorted(job_names):
            try:
                job = store.read_job_state(job_name)
                task_queue = TaskQueue(job_name, store.jobs_path / job_name / "tasks.json")

                # Count pending tasks
                pending_count = sum(1 for t in task_queue.get_all() if t.status == TaskStatus.PENDING)

                # Check active runner
                pid = store.read_pid_file(job_name)
                has_runner = "✓" if pid and _is_process_alive(pid) else "✗"

                # Color code state
                state_colors = {
                    "waiting": "yellow",
                    "working": "blue",
                    "completed": "green",
                    "failed": "red"
                }
                state_color = state_colors.get(job.state.value, "white")
                state_text = f"[{state_color}]{job.state.value}[/{state_color}]"

                table.add_row(
                    job.name,
                    state_text,
                    str(pending_count),
                    has_runner,
                    job.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                )

            except Exception as e:
                console.print(f"[red]Error reading job {job_name}: {e}[/red]")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def show_logs(job_name: str, tail: int = 50) -> None:
    """
    Display task execution logs.

    Args:
        job_name: Job name
        tail: Number of lines to display
    """
    config = Config.load_or_default()
    store = FileStore(config.base_path)

    try:
        logs_dir = store.jobs_path / job_name / "logs"
        if not logs_dir.exists():
            console.print(f"[yellow]No logs found for job {job_name}[/yellow]")
            return

        # Get all log files
        log_files = sorted(logs_dir.glob("*.log"))
        if not log_files:
            console.print(f"[yellow]No log files found for job {job_name}[/yellow]")
            return

        # Read and display logs
        console.print(f"[bold]Logs for job {job_name}:[/bold]\n")

        for log_file in log_files:
            console.print(f"[dim]--- {log_file.name} ---[/dim]")
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    # Display last N lines
                    for line in lines[-tail:]:
                        console.print(line.rstrip())
            except Exception as e:
                console.print(f"[red]Error reading {log_file.name}: {e}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def reset_job(job_name: str) -> None:
    """
    Reset job to waiting state.

    Args:
        job_name: Job name
    """
    config = Config.load_or_default()
    store = FileStore(config.base_path)

    try:
        job = store.read_job_state(job_name)

        # Reset to waiting
        job.state = JobState.WAITING
        store.write_job_state(job)

        console.print(f"[green]Job {job_name} reset to waiting state[/green]")

    except FileNotFoundError:
        console.print(f"[red]Job {job_name} not found[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error resetting job: {e}[/red]")
        sys.exit(1)


def run_task_command(job_name: str, task_id: str) -> None:
    """
    Run a single task (internal command for runners).

    Args:
        job_name: Job name
        task_id: Task ID to execute
    """
    config = Config.load_or_default()
    store = FileStore(config.base_path)

    try:
        # Load task
        task_queue = TaskQueue(job_name, store.jobs_path / job_name / "tasks.json")
        task = task_queue.get_by_id(task_id)

        if task is None:
            console.print(f"[red]Task {task_id} not found[/red]")
            sys.exit(1)

        # Mark task as running
        task.mark_running()
        task_queue.update(task)

        console.print(f"[blue]Running task {task_id}...[/blue]")

        # Execute task command
        result = subprocess.run(
            [task.command] + task.args,
            capture_output=True,
            text=True
        )

        # Update task status
        if result.returncode == 0:
            task.mark_completed()
            console.print(f"[green]Task {task_id} completed successfully[/green]")
        else:
            task.mark_failed(f"Exit code {result.returncode}: {result.stderr}")
            console.print(f"[red]Task {task_id} failed: {result.stderr}[/red]")

        task_queue.update(task)

        # Remove PID file
        store.remove_pid_file(job_name)

        sys.exit(result.returncode)

    except Exception as e:
        console.print(f"[red]Error executing task: {e}[/red]")
        # Try to clean up PID file
        try:
            store.remove_pid_file(job_name)
        except Exception:
            pass
        sys.exit(1)


def _is_process_alive(pid: int) -> bool:
    """Check if process is alive."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
