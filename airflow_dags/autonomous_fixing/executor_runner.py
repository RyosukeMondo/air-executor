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

        # Check if this is a batch task
        is_batch = BatchTask and isinstance(task, BatchTask)

        # Build prompt based on task type
        if is_batch:
            prompt = self._batch_fix_prompt(task, session_summary)
        elif task.type == "fix_build_error":
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
                "exit_on_complete": True  # Exit wrapper after completing the task
            }
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
                env=env  # Pass updated environment
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
                    if event.get('event') in ['shutdown', 'auto_shutdown', 'run_cancelled']:
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
            stdout = ''.join(stdout_lines)
            stderr = proc.stderr.read()

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

    def _batch_fix_prompt(self, task, summary: Optional[Dict]) -> str:
        """Generate prompt for batch fix"""
        batch_type = task.batch_type if hasattr(task, 'batch_type') else 'issues'
        related_issues = task.related_issues if hasattr(task, 'related_issues') else []

        # Check if this is a mega batch
        is_mega = batch_type == "mega_comprehensive"

        if is_mega:
            # Mega batch: comprehensive fix of everything
            return self._mega_batch_prompt(task, summary)

        # Regular batch: focused on one type or location
        # Create readable issue list
        issue_list = []
        for i, issue in enumerate(related_issues[:20], 1):  # Show more for batch
            issue_list.append(f"{i}. {issue['file']}:{issue['line']} - {issue['message'][:80]}")

        if len(related_issues) > 20:
            issue_list.append(f"... and {len(related_issues) - 20} more similar issues")

        issues_text = '\n'.join(issue_list)

        # Get unique files
        files = list(set(issue['file'] for issue in related_issues if issue.get('file')))
        files_text = '\n'.join([f"  - {f}" for f in files[:15]])
        if len(files) > 15:
            files_text += f"\n  ... and {len(files) - 15} more files"

        # Determine commit message based on batch type
        if 'cleanup' in str(task.type):
            commit_prefix = "chore"
            commit_desc = f"remove all {batch_type}"
        elif 'location' in str(task.type):
            commit_prefix = "fix"
            commit_desc = batch_type.replace('_', ' ')
        else:
            commit_prefix = "fix"
            commit_desc = f"{batch_type} across {len(files)} files"

        prompt = f"""Fix ALL {len(related_issues)} {batch_type} issues in Flutter project.

**Scope**: {batch_type}
**Files Affected** ({len(files)} total):
{files_text}

**All Issues to Fix**:
{issues_text}

**Your Task**:
1. Fix ALL {len(related_issues)} issues listed above
2. Work through files systematically
3. Apply consistent patterns across similar issues
4. Look for root causes that affect multiple issues
5. Run `flutter analyze --no-pub` to verify all fixes
6. **IMPORTANT**: Create ONE commit with all changes:
   ```bash
   git add -A
   git commit -m "{commit_prefix}: {commit_desc}"
   ```

This is a focused batch fix. Handle all {len(related_issues)} issues comprehensively in one session.
DO NOT skip any issues. DO NOT skip the commit step.
"""

        if summary:
            prompt += f"\n\n**Previous session**: Fixed {summary.get('fixed_count', 0)} batches\n"

        return prompt

    def _categorize_issue(self, message: str) -> str:
        """Categorize issue based on message content (SRP)"""
        msg_lower = message.lower()
        if 'import' in msg_lower and 'unused' in msg_lower:
            return 'Unused Imports'
        if 'type' in msg_lower:
            return 'Type Errors'
        if 'null' in msg_lower:
            return 'Null Safety'
        if 'override' in msg_lower:
            return 'Missing Overrides'
        return 'Other Issues'

    def _group_issues_by_category(self, issues: list) -> dict:
        """Group issues by category (SRP, SSOT)"""
        by_category = {}
        for issue in issues:
            category = self._categorize_issue(issue.get('message', ''))
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(issue)
        return by_category

    def _format_categorized_issues(self, by_category: dict) -> list:
        """Format categorized issues for display (SRP, SLAP)"""
        formatted = []
        for category, issues in sorted(by_category.items()):
            formatted.append(f"\n**{category}** ({len(issues)} issues):")
            for i, issue in enumerate(issues[:10], 1):
                formatted.append(f"  {i}. {issue['file']}:{issue['line']} - {issue['message'][:70]}")
            if len(issues) > 10:
                formatted.append(f"  ... and {len(issues) - 10} more")
        return formatted

    def _mega_batch_prompt(self, task, summary: Optional[Dict]) -> str:
        """Generate prompt for mega batch (all issues in phase)"""
        related_issues = task.related_issues if hasattr(task, 'related_issues') else []

        by_category = self._group_issues_by_category(related_issues)
        issues_by_category = self._format_categorized_issues(by_category)
        files = list(set(issue['file'] for issue in related_issues if issue.get('file')))

        prompt = f"""COMPREHENSIVE FIX: Fix ALL {len(related_issues)} issues in Flutter project.

**Scope**: Complete phase fix (all discovered issues)
**Total Issues**: {len(related_issues)}
**Affected Files**: {len(files)}

**Issues Organized by Category**:
{chr(10).join(issues_by_category)}

**Your Mission**:
1. Fix ALL {len(related_issues)} issues across all categories
2. Start with cleanup issues (unused imports, formatting)
3. Then fix type errors and null safety systematically
4. Work through files logically (by directory/module)
5. Run `flutter analyze --no-pub` frequently to track progress
6. **IMPORTANT**: Create ONE comprehensive commit:
   ```bash
   git add -A
   git commit -m "fix: comprehensive cleanup of {len(related_issues)} issues"
   ```

This is a COMPREHENSIVE fix session. Take your time, be systematic, and fix everything.
You can modify as many files as needed. This is your opportunity to clean up the entire codebase.

DO NOT skip any issues. DO NOT skip the commit step.
"""

        if summary:
            prompt += f"\n\n**Previous session**: Fixed {summary.get('fixed_count', 0)} comprehensive batches\n"

        return prompt

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
2. Implement a proper fix (make necessary changes, don't be overly minimal)
3. Consider if related code needs updates for consistency
4. Run `flutter analyze --no-pub` to verify the fix
5. **IMPORTANT**: Stage and commit your changes with:
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
3. Make comprehensive changes if needed across related files
4. Run `flutter test` to verify
5. **IMPORTANT**: Stage and commit your changes with:
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
3. Apply similar fixes to related code if applicable
4. Run `flutter analyze --no-pub` to verify
5. **IMPORTANT**: Stage and commit your changes with:
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
            ''.join(lines[start:end])

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
            created_at=datetime.now().isoformat()
        )

        # Run task
        result = runner.run_task(test_task)

        print(f"\n{'✅ Success' if result.success else '❌ Failed'}")
        sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
