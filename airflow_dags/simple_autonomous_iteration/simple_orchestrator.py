"""
Simple Autonomous Iteration Orchestrator.

Executes a single prompt repeatedly until completion condition is met or max iterations reached.
Much simpler than full autonomous_fixing orchestrator - just:
- Single prompt
- Simple completion check (regex in markdown file)
- Max iteration count

Safety features:
- Circuit breaker: Stop if no progress detected (no git changes)
- Commit check: Track if changes are being made
- Cost protection: Abort if wasting API calls
"""

import re
import subprocess

# Import Claude client from existing infrastructure
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from autonomous_fixing.adapters.ai.claude_client import ClaudeClient


class SimpleOrchestrator:
    """
    Simple orchestrator for iterative autonomous AI execution.

    Responsibilities:
    - Execute prompt with Claude
    - Check completion condition (regex in markdown)
    - Loop until done or max iterations
    """

    def __init__(
        self,
        prompt: str,
        completion_check_file: str,
        completion_regex: str = r"- \[x\] everything done",
        max_iterations: int = 30,
        project_path: str = ".",
        wrapper_path: str = "scripts/claude_wrapper.py",
        python_exec: str = ".venv/bin/python3",
        circuit_breaker_threshold: int = 3,
        require_git_changes: bool = True,
    ):
        """
        Initialize simple orchestrator.

        Args:
            prompt: Prompt to send to Claude on each iteration
            completion_check_file: Path to file to check for completion (e.g., markdown file)
            completion_regex: Regex pattern to match completion condition
            max_iterations: Maximum number of iterations
            project_path: Working directory for Claude
            wrapper_path: Path to claude_wrapper.py
            python_exec: Python executable to use
            circuit_breaker_threshold: Stop after N iterations without progress (default: 3)
            require_git_changes: Require git changes to consider progress (default: True)
        """
        self.prompt = prompt
        self.completion_check_file = Path(completion_check_file)
        self.completion_regex = completion_regex
        self.max_iterations = max_iterations
        self.project_path = Path(project_path)
        self.wrapper_path = wrapper_path
        self.python_exec = python_exec
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.require_git_changes = require_git_changes

        # Initialize Claude client
        self.claude = ClaudeClient(
            wrapper_path=self.wrapper_path,
            python_exec=self.python_exec,
            debug_logger=None,
            config={},
        )

        # Session ID for continuity
        self.session_id: Optional[str] = None

        # Circuit breaker tracking
        self.iterations_without_progress = 0
        self.last_git_diff_hash: Optional[str] = None

    def get_git_diff_hash(self) -> Optional[str]:
        """
        Get hash of current git diff to detect changes.

        Returns:
            Hash of git diff, or None if not a git repo or error
        """
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                import hashlib

                return hashlib.md5(result.stdout.encode()).hexdigest()
            return None
        except Exception:
            return None

    def check_git_changes(self) -> tuple[bool, str]:
        """
        Check if git changes were made since last check.

        Returns:
            Tuple of (has_changes, message)
        """
        if not self.require_git_changes:
            return True, "Git change tracking disabled"

        current_hash = self.get_git_diff_hash()

        if current_hash is None:
            return True, "Not a git repo or git error (skipping check)"

        if self.last_git_diff_hash is None:
            self.last_git_diff_hash = current_hash
            return True, "First iteration (baseline established)"

        if current_hash != self.last_git_diff_hash:
            self.last_git_diff_hash = current_hash
            self.iterations_without_progress = 0
            return True, "Git changes detected"

        return False, "No git changes detected"

    def check_circuit_breaker(self) -> tuple[bool, str]:
        """
        Check if circuit breaker should trigger.

        Returns:
            Tuple of (should_abort, reason)
        """
        if self.iterations_without_progress >= self.circuit_breaker_threshold:
            return True, (
                f"Circuit breaker: {self.iterations_without_progress} iterations "
                f"without progress (threshold: {self.circuit_breaker_threshold})"
            )
        return False, "Circuit breaker OK"

    def check_completion(self) -> tuple[bool, str]:
        """
        Check if completion condition is met.

        Returns:
            Tuple of (is_complete, reason)
        """
        if not self.completion_check_file.exists():
            return False, f"File not found: {self.completion_check_file}"

        try:
            content = self.completion_check_file.read_text(encoding="utf-8")
            match = re.search(self.completion_regex, content)

            if match:
                return True, f"Completion pattern matched: {match.group()}"

            return False, "Completion pattern not found"

        except Exception as e:
            return False, f"Error reading file: {e}"

    def execute_iteration(self, iteration: int) -> dict:
        """
        Execute a single iteration.

        Args:
            iteration: Current iteration number

        Returns:
            Result dict with success, outcome, etc.
        """
        print(f"\n{'='*80}")
        print(f"🔁 ITERATION {iteration}/{self.max_iterations}")
        print(f"{'='*80}")
        print(f"Prompt: {self.prompt[:100]}...")
        print(f"Project: {self.project_path}")
        print()

        start_time = time.time()

        # Execute prompt with Claude
        result = self.claude.query(
            prompt=self.prompt,
            project_path=str(self.project_path),
            timeout=600,  # 10 minutes per iteration
            session_id=self.session_id,
            prompt_type="autonomous_iteration",
        )

        duration = time.time() - start_time

        # Store session ID for continuity
        if not self.session_id:
            # Extract session from events if available
            for event in result.get("events", []):
                if event.get("event") == "session_started":
                    self.session_id = event.get("session_id")
                    break

        print(f"\n⏱️  Iteration completed in {duration:.1f}s")
        print(f"✅ Success: {result.get('success', False)}")

        if not result.get("success"):
            print(f"❌ Error: {result.get('error', 'Unknown error')}")

        return result

    def run(self) -> dict:
        """
        Run the orchestrator - execute iterations until completion or max reached.

        Returns:
            Dict with final results and stats
        """
        print(f"\n{'='*80}")
        print("🚀 Simple Autonomous Iteration Orchestrator")
        print(f"{'='*80}")
        print(f"Max iterations: {self.max_iterations}")
        print(f"Completion file: {self.completion_check_file}")
        print(f"Completion pattern: {self.completion_regex}")
        print(f"{'='*80}\n")

        start_time = time.time()
        iterations_completed = 0
        final_result = None

        for iteration in range(1, self.max_iterations + 1):
            iterations_completed = iteration

            # Execute iteration
            result = self.execute_iteration(iteration)
            final_result = result

            if not result.get("success"):
                print(f"\n❌ Iteration {iteration} failed - stopping")
                break

            # Check completion condition
            is_complete, reason = self.check_completion()
            print(f"\n🔍 Completion check: {reason}")

            if is_complete:
                print(f"\n🎉 COMPLETION CONDITION MET in iteration {iteration}!")
                total_duration = time.time() - start_time
                return {
                    "success": True,
                    "reason": "completion_condition_met",
                    "iterations_completed": iterations_completed,
                    "total_duration": total_duration,
                    "final_result": final_result,
                }

            # Check for git changes (progress detection)
            has_changes, change_msg = self.check_git_changes()
            print(f"📝 Progress check: {change_msg}")

            if not has_changes:
                self.iterations_without_progress += 1

            # Check circuit breaker
            should_abort, abort_reason = self.check_circuit_breaker()
            if should_abort:
                print(f"\n❌ {abort_reason}")
                total_duration = time.time() - start_time
                return {
                    "success": False,
                    "reason": "circuit_breaker_triggered",
                    "iterations_completed": iterations_completed,
                    "total_duration": total_duration,
                    "final_result": final_result,
                    "iterations_without_progress": self.iterations_without_progress,
                }

            # Wait a bit before next iteration (avoid rapid loops)
            if iteration < self.max_iterations:
                print("\n⏳ Waiting 5s before next iteration...")
                time.sleep(5)

        # Max iterations reached
        total_duration = time.time() - start_time
        print(f"\n⚠️  Max iterations ({self.max_iterations}) reached without completion")

        return {
            "success": False,
            "reason": "max_iterations_reached",
            "iterations_completed": iterations_completed,
            "total_duration": total_duration,
            "final_result": final_result,
        }


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Simple autonomous iteration orchestrator")
    parser.add_argument("--prompt", required=True, help="Prompt to send to Claude")
    parser.add_argument(
        "--completion-file", required=True, help="File to check for completion condition"
    )
    parser.add_argument(
        "--completion-regex",
        default=r"- \[x\] everything done",
        help="Regex pattern for completion",
    )
    parser.add_argument(
        "--max-iterations", type=int, default=30, help="Maximum number of iterations"
    )
    parser.add_argument("--project-path", default=".", help="Working directory for Claude")
    parser.add_argument(
        "--wrapper-path",
        default="scripts/claude_wrapper.py",
        help="Path to claude_wrapper.py",
    )
    parser.add_argument("--python-exec", default=".venv/bin/python3", help="Python executable")
    parser.add_argument(
        "--circuit-breaker-threshold",
        type=int,
        default=3,
        help="Stop after N iterations without progress",
    )
    parser.add_argument(
        "--no-git-check",
        action="store_true",
        help="Disable git change requirement (not recommended)",
    )

    args = parser.parse_args()

    orchestrator = SimpleOrchestrator(
        prompt=args.prompt,
        completion_check_file=args.completion_file,
        completion_regex=args.completion_regex,
        max_iterations=args.max_iterations,
        project_path=args.project_path,
        wrapper_path=args.wrapper_path,
        python_exec=args.python_exec,
        circuit_breaker_threshold=args.circuit_breaker_threshold,
        require_git_changes=not args.no_git_check,
    )

    result = orchestrator.run()

    print(f"\n{'='*80}")
    print("📊 FINAL RESULT")
    print(f"{'='*80}")
    print(f"Success: {result['success']}")
    print(f"Reason: {result['reason']}")
    print(f"Iterations: {result['iterations_completed']}")
    print(f"Duration: {result['total_duration']:.1f}s")
    print(f"{'='*80}\n")

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
