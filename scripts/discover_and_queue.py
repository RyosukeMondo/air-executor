#!/usr/bin/env python3
"""
Example script that discovers files and queues processing tasks dynamically.

This demonstrates the dynamic task generation capability of Air-Executor.
"""

import sys
from pathlib import Path

from air_executor.core.task import Task, TaskQueue
from air_executor.storage.file_store import FileStore


def main():
    """Discover files and queue processing tasks."""
    # Get job name from environment or command line
    job_name = sys.argv[1] if len(sys.argv) > 1 else "dynamic-workflow"

    # Initialize storage
    store = FileStore()
    task_queue = TaskQueue(
        job_name,
        store.jobs_path / job_name / "tasks.json"
    )

    # Discover files (example: all .txt files in current directory)
    files = list(Path(".").glob("*.txt"))

    print(f"Discovered {len(files)} files to process")

    # Queue a processing task for each file
    for i, file_path in enumerate(files):
        task = Task(
            id=f"process-{file_path.stem}",
            job_name=job_name,
            command="python",
            args=["process_file.py", str(file_path)],
            dependencies=[]
        )

        task_queue.add(task)
        print(f"Queued task: {task.id}")

    print(f"Successfully queued {len(files)} tasks")
    print("Job manager will automatically spawn runners for these tasks")


if __name__ == "__main__":
    main()
