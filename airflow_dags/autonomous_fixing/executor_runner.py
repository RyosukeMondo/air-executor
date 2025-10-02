#!/usr/bin/env python3
"""
Air-executor integration module.
Runs fix tasks via claude_wrapper.py with narrow context.
"""

import subprocess
import os
import time
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

from state_manager import Task, StateManager


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
        self,
        wrapper_path: str,
        working_dir: str,
        timeout: int = 300,
        auto_commit: bool = True
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

        # Build prompt based on task type
        if task.type == "fix_build_error":
            prompt = self._build_fix_prompt(task, session_summary)
        elif task.type == "fix_test_failure":
            prompt = self._test_fix_prompt(task, session_summary)
        elif task.type == "fix_lint_issue":
            prompt = self._lint_fix_prompt(task, session_summary)
        else:
            prompt = self._generic_fix_prompt(task, session_summary)

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
            exit_code=result.returncode
        )

        self._print_result(execution_result)
        return execution_result

    def _execute(self, prompt: str) -> subprocess.CompletedProcess:
        """Execute claude_wrapper.py with prompt via stdin"""
        import json
        import sys

        cmd = ["python", str(self.wrapper_path)]

        # Build JSON payload for wrapper
        payload = {
            "action": "prompt",
            "prompt": prompt,
            "options": {
                "cwd": str(self.working_dir),
                "permission_mode": "bypassPermissions",  # Auto-approve actions
                "exit_on_complete": True  # Exit wrapper after completing the task
            }
        }

        try:
            # Send prompt and keep stdin open by not closing it immediately
            # Wrapper will exit when task completes due to exit_on_complete=True
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.wrapper_path.parent
            )

            # Send prompt
            proc.stdin.write(json.dumps(payload) + "\n")
            proc.stdin.flush()

            # Wait for completion (wrapper will exit due to exit_on_complete)
            stdout, stderr = proc.communicate(timeout=self.timeout)

            return subprocess.CompletedProcess(
                args=cmd,
                returncode=proc.returncode,
                stdout=stdout,
                stderr=stderr
            )

        except subprocess.TimeoutExpired:
            proc.kill()
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=124,  # timeout exit code
                stdout="",
                stderr=f"Execution timeout after {self.timeout}s"
            )

    def _build_fix_prompt(self, task: Task, summary: Optional[Dict]) -> str:
        """Generate prompt for build error fix"""
        # Truncate message for commit to avoid errors
        commit_msg = task.message[:60].replace('"', "'").replace('\n', ' ')

        prompt = f"""Fix this Flutter build error:

**File**: {task.file or 'Unknown'}
**Line**: {task.line or '?'}
**Error**: {task.message}

**Code Context**:
```
{task.context}
```

**Instructions**:
1. Analyze the error carefully
2. Fix ONLY this specific error (surgical fix, minimal changes)
3. Run `flutter analyze --no-pub` to verify the fix
4. **IMPORTANT**: Stage and commit your changes with:
   ```bash
   git add -A
   git commit -m "fix: {commit_msg}"
   ```

DO NOT skip the commit step. Changes must be committed before finishing.
"""

        if summary:
            prompt += f"\n\n**Previous session**: Fixed {summary.get('fixed_count', 0)} of {summary.get('total_count', 0)} issues\n"

        return prompt

    def _test_fix_prompt(self, task: Task, summary: Optional[Dict]) -> str:
        """Generate prompt for test failure fix"""
        commit_msg = task.message[:60].replace('"', "'").replace('\n', ' ')

        prompt = f"""Fix this failing Flutter test:

**Test**: {task.message}
**File**: {task.file or 'Unknown'}

**Test Context**:
```
{task.context}
```

**Instructions**:
1. Understand why the test is failing
2. Fix the implementation (NOT the test unless it's clearly wrong)
3. Run `flutter test` to verify
4. **IMPORTANT**: Stage and commit your changes with:
   ```bash
   git add -A
   git commit -m "fix(test): {commit_msg}"
   ```

Fix the root cause, not the symptoms. DO NOT skip the commit step.
"""

        if summary:
            prompt += f"\n\n**Previous session**: Fixed {summary.get('fixed_count', 0)} tests\n"

        return prompt

    def _lint_fix_prompt(self, task: Task, summary: Optional[Dict]) -> str:
        """Generate prompt for lint issue fix"""
        commit_msg = task.message[:60].replace('"', "'").replace('\n', ' ')

        prompt = f"""Fix this Flutter lint issue:

**File**: {task.file or 'Unknown'}
**Issue**: {task.message}

**Code Context**:
```
{task.context}
```

**Instructions**:
1. Understand the lint rule violation
2. Fix according to Dart/Flutter best practices
3. Run `flutter analyze --no-pub` to verify
4. **IMPORTANT**: Stage and commit your changes with:
   ```bash
   git add -A
   git commit -m "style: {commit_msg}"
   ```

Follow Flutter style guide exactly. DO NOT skip the commit step.
"""

        if summary:
            prompt += f"\n\n**Previous session**: Fixed {summary.get('fixed_count', 0)} lint issues\n"

        return prompt

    def _generic_fix_prompt(self, task: Task, summary: Optional[Dict]) -> str:
        """Generic fix prompt"""
        commit_msg = task.message[:60].replace('"', "'").replace('\n', ' ')

        prompt = f"""Fix this issue in the Flutter project:

**Type**: {task.type}
**Description**: {task.message}
**Location**: {task.file}:{task.line if task.line else '?'}

**Context**:
```
{task.context}
```

**Instructions**:
1. Analyze and understand the issue
2. Implement a targeted fix
3. Verify the fix works
4. **IMPORTANT**: Stage and commit your changes with:
   ```bash
   git add -A
   git commit -m "fix: {commit_msg}"
   ```

Focus on quality over speed. DO NOT skip the commit step.
"""

        if summary:
            prompt += f"\n\n**Previous session summary**: {summary}\n"

        return prompt

    def _print_result(self, result: ExecutionResult):
        """Print execution result"""
        status = "✅" if result.success else "❌"
        print(f"{status} Task {result.task_id}: {'Success' if result.success else 'Failed'}")
        print(f"   Duration: {result.duration:.1f}s")

        if result.stdout:
            print(f"   Output: {result.stdout[:200]}...")

        if result.stderr and not result.success:
            print(f"   Error: {result.stderr[:200]}...")


def extract_file_context(filepath: str, error_line: int = None, context_lines: int = 10) -> str:
    """Extract minimal relevant context from a file"""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        if error_line is not None and error_line > 0:
            # Get context around error line
            start = max(0, error_line - context_lines - 1)
            end = min(len(lines), error_line + context_lines)
            context = ''.join(lines[start:end])

            # Add line numbers
            numbered = []
            for i, line in enumerate(lines[start:end], start=start + 1):
                marker = "→ " if i == error_line else "  "
                numbered.append(f"{marker}{i:4d} | {line}")

            return ''.join(numbered)
        else:
            # Return file structure (imports + signatures)
            return extract_structure(lines)

    except Exception as e:
        return f"Could not read file: {str(e)}"


def extract_structure(lines: list) -> str:
    """Extract imports and function/class signatures only"""
    structure = []

    for line in lines:
        stripped = line.strip()
        if (
            stripped.startswith('import ') or
            stripped.startswith('export ') or
            stripped.startswith('class ') or
            stripped.startswith('abstract class ') or
            stripped.startswith('mixin ') or
            stripped.startswith('enum ') or
            'void ' in stripped or
            'Future<' in stripped or
            'Stream<' in stripped
        ):
            structure.append(line)

    return ''.join(structure) if structure else "// Empty or no structure found"


def main():
    """CLI entry point for testing"""
    import sys
    from state_manager import generate_task_id
    from datetime import datetime

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
            created_at=datetime.now().isoformat()
        )

        # Run task
        result = runner.run_task(test_task)

        print(f"\n{'✅ Success' if result.success else '❌ Failed'}")
        sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
