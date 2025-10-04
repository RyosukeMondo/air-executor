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

    def run_task(self, task: Task, session_summary: dict | None = None) -> ExecutionResult:
        """Execute a single fix task"""
        print(f"\n🚀 Running task: {task.type} ({task.id})")

        prompt = self._build_prompt(task, session_summary)

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

    def _build_prompt(self, task: Task, session_summary: dict | None) -> str:
        """Build prompt based on task type"""
        is_batch = BatchTask and isinstance(task, BatchTask)

        if is_batch:
            return PromptGenerator.batch_fix_prompt(task, session_summary)
        if task.type == "fix_build_error":
            return PromptGenerator.build_fix_prompt(task, session_summary)
        if task.type == "fix_test_failure":
            return PromptGenerator.test_fix_prompt(task, session_summary)
        if task.type == "fix_lint_issue":
            return PromptGenerator.lint_fix_prompt(task, session_summary)

        return PromptGenerator.generic_fix_prompt(task, session_summary)

    def _execute(self, prompt: str) -> subprocess.CompletedProcess:
        """Execute claude_wrapper.py with prompt via stdin"""
        import sys

        python_exe = sys.executable
        cmd = [python_exe, str(self.wrapper_path)]
        payload = self._build_payload(prompt)
        env = self._prepare_environment()

        try:
            proc = self._start_process(cmd, env)
            self._send_payload(proc, payload)
            stdout_lines = self._read_stdout_stream(proc, cmd)
            return self._finalize_process(proc, cmd, stdout_lines)
        except subprocess.TimeoutExpired:
            return self._handle_timeout(proc, cmd)

    def _build_payload(self, prompt: str) -> dict:
        """Build JSON payload for wrapper"""
        return {
            "action": "prompt",
            "prompt": prompt,
            "options": {
                "cwd": str(self.working_dir),
                "permission_mode": "bypassPermissions",
                "exit_on_complete": True,
            },
        }

    def _prepare_environment(self) -> dict:
        """Ensure /usr/local/bin is in PATH for claude CLI"""
        env = os.environ.copy()
        if "/usr/local/bin" not in env.get("PATH", ""):
            env["PATH"] = f"/usr/local/bin:{env.get('PATH', '')}"
        return env

    def _start_process(self, cmd: list, env: dict) -> subprocess.Popen:
        """Start wrapper process"""
        return subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.wrapper_path.parent,
            env=env,
        )

    def _send_payload(self, proc: subprocess.Popen, payload: dict):
        """Send JSON payload to process stdin"""
        import json

        proc.stdin.write(json.dumps(payload) + "\n")
        proc.stdin.flush()

    def _read_stdout_stream(self, proc: subprocess.Popen, cmd: list) -> list:
        """Read stdout events as they stream"""
        stdout_lines = []
        start_time = time.time()

        for line in proc.stdout:
            stdout_lines.append(line)

            if self._is_completion_event(line):
                break

            if self._is_timeout_exceeded(start_time):
                proc.kill()
                raise subprocess.TimeoutExpired(cmd, self.timeout)

        return stdout_lines

    def _is_completion_event(self, line: str) -> bool:
        """Check if line indicates completion/shutdown"""
        import json

        try:
            event = json.loads(line)
            return event.get("event") in ["shutdown", "auto_shutdown", "run_cancelled"]
        except (json.JSONDecodeError, AttributeError):
            return False

    def _is_timeout_exceeded(self, start_time: float) -> bool:
        """Check if execution timeout exceeded"""
        return time.time() - start_time > self.timeout

    def _finalize_process(
        self, proc: subprocess.Popen, cmd: list, stdout_lines: list
    ) -> subprocess.CompletedProcess:
        """Close stdin, wait for process, collect outputs"""
        proc.stdin.close()
        proc.wait(timeout=5)

        stdout = "".join(stdout_lines)
        stderr = proc.stderr.read()

        return subprocess.CompletedProcess(
            args=cmd, returncode=proc.returncode, stdout=stdout, stderr=stderr
        )

    def _handle_timeout(self, proc: subprocess.Popen, cmd: list) -> subprocess.CompletedProcess:
        """Handle timeout exception"""
        proc.kill()
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
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
