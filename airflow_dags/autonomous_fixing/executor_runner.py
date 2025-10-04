#!/usr/bin/env python3
"""
Air-executor integration module.
Runs fix tasks via claude_wrapper.py with narrow context.
"""

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from executor_prompts import PromptGenerator
from executor_utils import extract_file_context, extract_structure  # noqa: F401
from state_manager import Task

# Import BatchTask if available
try:
    from issue_grouping import BatchTask
except ImportError:
    BatchTask = None


@dataclass
class ExecutionResult:
    """Result of executing a fix task"""

    task_id: str
    success: bool
    stdout: str
    stderr: str
    duration: float
    exit_code: int


class AirExecutorRunner:
    """Run tasks via air-executor (claude_wrapper.py)"""

    def __init__(
        self, wrapper_path: str, working_dir: str, timeout: int = 300, auto_commit: bool = True
    ):
        self.wrapper_path = Path(wrapper_path)
        self.working_dir = Path(working_dir)
        self.timeout = timeout
        self.auto_commit = auto_commit

        if not self.wrapper_path.exists():
            raise FileNotFoundError(f"claude_wrapper.py not found: {self.wrapper_path}")

    def run_task(self, task: Task, session_summary: Optional[Dict] = None) -> ExecutionResult:
        """Execute a single fix task"""
        print(f"\n🚀 Running task: {task.type} ({task.id})")

        # Check if this is a batch task
        is_batch = BatchTask and isinstance(task, BatchTask)

        # Build prompt based on task type using PromptGenerator
        if is_batch:
            prompt = PromptGenerator.batch_fix_prompt(task, session_summary)
        elif task.type == "fix_build_error":
            prompt = PromptGenerator.build_fix_prompt(task, session_summary)
        elif task.type == "fix_test_failure":
            prompt = PromptGenerator.test_fix_prompt(task, session_summary)
        elif task.type == "fix_lint_issue":
            prompt = PromptGenerator.lint_fix_prompt(task, session_summary)
        else:
            prompt = PromptGenerator.generic_fix_prompt(task, session_summary)

        # Execute via air-executor
        start_time = time.time()
        result = self._execute(prompt)
        duration = time.time() - start_time

        execution_result = ExecutionResult(
            task_id=task.id,
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            duration=duration,
            exit_code=result.returncode,
        )

        self._print_result(execution_result)
        return execution_result

    def _execute(self, prompt: str) -> subprocess.CompletedProcess:
        """Execute claude_wrapper.py with prompt via stdin"""
        import json
        import sys

        # Use same python as current process (venv python)
        python_exe = sys.executable
        cmd = [python_exe, str(self.wrapper_path)]

        # Build JSON payload for wrapper
        payload = {
            "action": "prompt",
            "prompt": prompt,
            "options": {
                "cwd": str(self.working_dir),
                "permission_mode": "bypassPermissions",  # Auto-approve actions
                "exit_on_complete": True,  # Exit wrapper after completing the task
            },
        }

        # Ensure /usr/local/bin is in PATH for claude CLI
        env = os.environ.copy()
        if "/usr/local/bin" not in env.get("PATH", ""):
            env["PATH"] = f"/usr/local/bin:{env.get('PATH', '')}"

        try:
            # Send prompt and keep stdin open by not closing it immediately
            # Wrapper will exit when task completes due to exit_on_complete=True
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.wrapper_path.parent,
                env=env,  # Pass updated environment
            )

            # Send prompt
            proc.stdin.write(json.dumps(payload) + "\n")
            proc.stdin.flush()

            # Read stdout events as they stream (prevents blocking)
            stdout_lines = []
            import time

            start_time = time.time()

            for line in proc.stdout:
                stdout_lines.append(line)

                # Check for completion/shutdown events
                try:
                    event = json.loads(line)
                    if event.get("event") in ["shutdown", "auto_shutdown", "run_cancelled"]:
                        break
                except (json.JSONDecodeError, AttributeError):
                    pass

                # Timeout check
                if time.time() - start_time > self.timeout:
                    proc.kill()
                    raise subprocess.TimeoutExpired(cmd, self.timeout)

            # Close stdin and wait for process to finish
            proc.stdin.close()
            proc.wait(timeout=5)

            # Collect outputs
            stdout = "".join(stdout_lines)
            stderr = proc.stderr.read()

            return subprocess.CompletedProcess(
                args=cmd, returncode=proc.returncode, stdout=stdout, stderr=stderr
            )

        except subprocess.TimeoutExpired:
            proc.kill()
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=124,  # timeout exit code
                stdout="",
                stderr=f"Execution timeout after {self.timeout}s",
            )

    def _print_result(self, result: ExecutionResult):
        """Print execution result"""
        status = "✅" if result.success else "❌"
        print(f"{status} Task {result.task_id}: {'Success' if result.success else 'Failed'}")
        print(f"   Duration: {result.duration:.1f}s")

        if result.stdout:
            print(f"   Output: {result.stdout[:200]}...")

        if result.stderr and not result.success:
            print(f"   Error: {result.stderr[:200]}...")


def main():
    """CLI entry point for testing"""
    import sys
    from datetime import datetime

    from state_manager import generate_task_id

    if len(sys.argv) < 3:
        print("Usage: python executor_runner.py <wrapper_path> <working_dir> [test]")
        sys.exit(1)

    wrapper_path = sys.argv[1]
    working_dir = sys.argv[2]

    runner = AirExecutorRunner(wrapper_path, working_dir)

    if len(sys.argv) > 3 and sys.argv[3] == "test":
        # Create test task
        test_task = Task(
            id=generate_task_id(),
            type="fix_build_error",
            priority=1,
            phase="build",
            file="lib/main.dart",
            line=42,
            message="Undefined name 'foo'",
            context="void main() {\n  print(foo);  // ← Error here\n}\n",
            created_at=datetime.now().isoformat(),
        )

        # Run task
        result = runner.run_task(test_task)

        print(f"\n{'✅ Success' if result.success else '❌ Failed'}")
        sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
