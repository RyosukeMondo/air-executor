"""Main CLI entry point for Air-Executor."""

from pathlib import Path

import click


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Air-Executor: Autonomous job management with ephemeral task runners."""
    pass


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to config file"
)
def start(config):
    """Start job manager in background."""
    from .commands import start_manager
    start_manager(config)


@cli.command()
def stop():
    """Stop job manager gracefully."""
    from .commands import stop_manager
    stop_manager()


@cli.command()
@click.option("--job", help="Filter by job name")
def status(job):
    """Display job status table."""
    from .commands import show_status
    show_status(job)


@cli.command()
@click.option("--job", required=True, help="Job name")
@click.option("--tail", default=50, help="Number of lines to display")
def logs(job, tail):
    """Display task execution logs."""
    from .commands import show_logs
    show_logs(job, tail)


@cli.command()
@click.option("--job", required=True, help="Job name")
@click.confirmation_option(prompt="Reset job state to waiting?")
def reset(job):
    """Reset job to waiting state."""
    from .commands import reset_job
    reset_job(job)


@cli.command()
@click.option("--job", required=True, help="Job name")
@click.option("--task", required=True, help="Task ID")
def run_task(job, task):
    """Run a single task (internal command for runners)."""
    from .commands import run_task_command
    run_task_command(job, task)


if __name__ == "__main__":
    cli()
