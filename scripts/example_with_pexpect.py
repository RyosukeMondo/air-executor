#!/usr/bin/env python3
"""
Example: Using Air-Executor with pexpect for interactive commands

This shows how to create jobs that run interactive commands
that need expect-like input/output handling.
"""

import json
from pathlib import Path
from datetime import datetime


def create_interactive_job(job_name: str, script_path: str):
    """
    Create a job that runs an interactive script using pexpect.

    The script will be executed as a task, and pexpect can handle
    interactive input/output within that script.
    """
    job_dir = Path(".air-executor/jobs") / job_name
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "logs").mkdir(exist_ok=True)

    # Create the pexpect wrapper script
    wrapper_script = job_dir / "run_interactive.py"
    wrapper_script.write_text(f'''#!/usr/bin/env python3
import pexpect
import sys

# Run the interactive command
child = pexpect.spawn('bash {script_path}')
child.logfile = sys.stdout.buffer
child.expect(pexpect.EOF)
child.close()
sys.exit(child.exitstatus)
''')
    wrapper_script.chmod(0o755)

    # Create job state
    state = {
        "id": f"{job_name}-{int(datetime.now().timestamp())}",
        "name": job_name,
        "state": "waiting",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }

    with open(job_dir / "state.json", "w") as f:
        json.dump(state, f, indent=2)

    # Create tasks
    tasks = [{
        "id": "run-interactive",
        "job_name": job_name,
        "command": "python",
        "args": [str(wrapper_script)],
        "dependencies": [],
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "started_at": None,
        "completed_at": None,
        "error": None
    }]

    with open(job_dir / "tasks.json", "w") as f:
        json.dump(tasks, f, indent=2)

    print(f"✅ Created interactive job: {job_name}")


# Example usage
if __name__ == "__main__":
    # Create a test interactive script
    test_script = Path("test_interactive.sh")
    test_script.write_text('''#!/bin/bash
echo "What is your name?"
read name
echo "Hello, $name!"
sleep 1
echo "Process complete"
''')
    test_script.chmod(0o755)

    create_interactive_job("interactive-test", str(test_script))

    print("\n💡 Note: You need to install pexpect first:")
    print("   pip install pexpect")
