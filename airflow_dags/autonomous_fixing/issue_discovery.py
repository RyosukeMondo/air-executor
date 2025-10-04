#!/usr/bin/env python3
"""
Issue discovery module.
Analyzes Flutter project and generates fix tasks.
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path

from executor_runner import extract_file_context
from state_manager import Task, generate_task_id


class IssueDiscovery:
    """Discover issues in Flutter project"""

    def __init__(self, project_path: str, flutter_bin: str = None):
        self.project_path = Path(project_path)
        self.flutter_bin = flutter_bin or self._find_flutter()

    def _find_flutter(self) -> str:
        """Find Flutter binary"""
        import os
        import shutil

        # Try to find in PATH
        flutter = shutil.which("flutter")
        if flutter:
            return flutter

        # Try common locations
        locations = [os.path.expanduser("~/flutter/bin/flutter"), "/usr/local/bin/flutter"]

        for location in locations:
            if os.path.exists(location):
                return location

        return "flutter"  # Fall back to assuming it's in PATH

    def discover_build_issues(self) -> list[Task]:
        """Discover build/analysis errors"""
        print("🔍 Discovering build issues...")

        try:
            result = subprocess.run(
                [self.flutter_bin, "analyze", "--no-pub"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            tasks = []
            for line in result.stdout.splitlines():
                if " error •" in line:
                    task = self._parse_analysis_issue(line, "error", "build")
                    if task:
                        tasks.append(task)

            print(f"  Found {len(tasks)} build errors")
            return tasks

        except Exception as e:
            print(f"  ❌ Error discovering build issues: {e}")
            return []

    def discover_test_failures(self) -> list[Task]:
        """Discover test failures"""
        print("🔍 Discovering test failures...")

        try:
            result = subprocess.run(
                [self.flutter_bin, "test", "--no-pub", "--reporter=json"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300,
            )

            tasks = []
            import json

            for line in result.stdout.splitlines():
                try:
                    event = json.loads(line)
                    if event.get("type") == "testDone" and event.get("result") != "success":
                        task = self._parse_test_failure(event)
                        if task:
                            tasks.append(task)
                except json.JSONDecodeError:
                    continue

            print(f"  Found {len(tasks)} test failures")
            return tasks

        except Exception as e:
            print(f"  ❌ Error discovering test failures: {e}")
            return []

    def discover_lint_issues(self) -> list[Task]:
        """Discover lint warnings (lower priority)"""
        print("🔍 Discovering lint issues...")

        try:
            result = subprocess.run(
                [self.flutter_bin, "analyze", "--no-pub"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            tasks = []
            for line in result.stdout.splitlines():
                if " warning •" in line or " info •" in line:
                    task = self._parse_analysis_issue(line, "lint", "lint")
                    if task:
                        tasks.append(task)

            print(f"  Found {len(tasks)} lint issues")
            return tasks

        except Exception as e:
            print(f"  ❌ Error discovering lint issues: {e}")
            return []

    def _parse_analysis_issue(self, line: str, issue_type: str, phase: str) -> Task:
        """Parse analysis output line into Task"""
        # Format: "  error • message • file:line:col • code"
        # Example: "  error • Undefined name 'foo' • lib/main.dart:10:5 • undefined_identifier"

        try:
            # Extract location (file:line:col)
            location_match = re.search(r"•\s+([\w/._-]+):(\d+):\d+\s+•", line)
            if not location_match:
                return None

            file_path = location_match.group(1)
            line_num = int(location_match.group(2))

            # Extract message (between first and second •)
            message_match = re.search(r"(error|warning|info)\s+•\s+([^•]+)\s+•", line)
            if not message_match:
                return None

            message = message_match.group(2).strip()

            # Get context
            full_path = self.project_path / file_path
            context = extract_file_context(str(full_path), line_num, context_lines=5)

            # Calculate priority (errors = high, warnings = medium, info = low)
            if "error" in line:
                priority = 1
            elif "warning" in line:
                priority = 5
            else:
                priority = 8

            return Task(
                id=generate_task_id(),
                type=f"fix_{issue_type}_error"
                if issue_type == "build"
                else f"fix_{issue_type}_issue",
                priority=priority,
                phase=phase,
                file=file_path,
                line=line_num,
                message=message,
                context=context,
                created_at=datetime.now().isoformat(),
            )

        except Exception as e:
            print(f"  ⚠️ Failed to parse line: {line[:100]}... ({e})")
            return None

    def _parse_test_failure(self, event: dict) -> Task:
        """Parse test failure event into Task"""
        try:
            test = event.get("test", {})
            test_name = test.get("name", "Unknown test")
            test_url = test.get("url", "")

            # Extract file from URL
            file_match = re.search(r"file://[^:]+/([^:]+)", test_url)
            file_path = file_match.group(1) if file_match else None

            # Extract error message
            error_message = event.get("error", "Test failed")

            # Get context if we have file path
            context = ""
            if file_path:
                full_path = self.project_path / file_path
                if full_path.exists():
                    context = extract_file_context(str(full_path))

            return Task(
                id=generate_task_id(),
                type="fix_test_failure",
                priority=3,
                phase="test",
                file=file_path,
                message=f"{test_name}: {error_message}",
                context=context or "// Test context not available",
                created_at=datetime.now().isoformat(),
            )

        except Exception as e:
            print(f"  ⚠️ Failed to parse test failure: {e}")
            return None


def main():
    """CLI entry point"""
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python issue_discovery.py <project_path> [build|test|lint|all]")
        sys.exit(1)

    project_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "all"

    discovery = IssueDiscovery(project_path)

    all_tasks = []

    if mode in ["build", "all"]:
        all_tasks.extend(discovery.discover_build_issues())

    if mode in ["test", "all"]:
        all_tasks.extend(discovery.discover_test_failures())

    if mode in ["lint", "all"]:
        all_tasks.extend(discovery.discover_lint_issues())

    print(f"\n📋 Total issues discovered: {len(all_tasks)}")

    # Output as JSON
    if "--json" in sys.argv:
        print(json.dumps([task.to_dict() for task in all_tasks], indent=2))
    else:
        # Summary
        by_type = {}
        for task in all_tasks:
            by_type[task.type] = by_type.get(task.type, 0) + 1

        print("\nBreakdown:")
        for task_type, count in sorted(by_type.items()):
            print(f"  - {task_type}: {count}")


if __name__ == "__main__":
    main()
