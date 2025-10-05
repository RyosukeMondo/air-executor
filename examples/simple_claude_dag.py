#!/usr/bin/env python3
"""
Example: Simple DAG that runs a Claude command and captures output
"""

import json
from datetime import datetime
from pathlib import Path


def create_claude_query_job():
    """
    Create a simple job that runs: claude -p "hello, how old are you?"
    and captures the output.
    """
    job_name = "claude-query"
    base_path = Path(".air-executor")
    jobs_path = base_path / "jobs"
    job_dir = jobs_path / job_name

    # Create directories
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "logs").mkdir(exist_ok=True)

    # Create state.json
    job_id = f"{job_name}-{int(datetime.now().timestamp())}"
    state = {
        "id": job_id,
        "name": job_name,
        "state": "waiting",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }

    with open(job_dir / "state.json", "w") as f:
        json.dump(state, f, indent=2)

    # Create single task that runs claude command
    tasks = [
        {
            "id": "claude-query-task",
            "job_name": job_name,
            "command": "claude",
            "args": ["-p", "hello, how old are you?"],
            "dependencies": [],
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "started_at": None,
            "completed_at": None,
            "error": None,
        }
    ]

    with open(job_dir / "tasks.json", "w") as f:
        json.dump(tasks, f, indent=2)

    print(f"✅ Created job: {job_name} (ID: {job_id})")
    print(f"📂 Job directory: {job_dir}")
    print('📝 Command: claude -p "hello, how old are you?"')
    print("\n🚀 To run this job, start the manager:")
    print("   python scripts/run_manager.py")
    print("\n📊 Output will be in:")
    print(f"   {job_dir / 'logs' / 'claude-query-task.log'}")

    return job_id


if __name__ == "__main__":
    create_claude_query_job()
