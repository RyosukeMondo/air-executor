#!/usr/bin/env python3
"""
Issue grouping module.
Groups similar issues for batch fixing.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from airflow_dags.autonomous_fixing.adapters.state.state_manager import generate_task_id
from airflow_dags.autonomous_fixing.domain.models.tasks import Task


@dataclass
class BatchTask(Task):
    """Task representing a batch of similar issues"""

    related_issues: list[dict] = field(default_factory=list)  # List of {file, line, message}
    batch_type: str | None = None  # Type of batch (unused_imports, type_errors, etc.)


class IssueGrouper:
    """Group similar issues for efficient batch fixing (human-like strategy)"""

    # Issue patterns to group together
    BATCH_PATTERNS = {
        "unused_imports": [
            r"Unused import",
            r"import.*isn't used",
        ],
        "missing_imports": [
            r"Undefined (name|class|method)",
            r"The (function|method|getter|setter) '.*' isn't defined",
        ],
        "type_mismatches": [
            r"type '.*' isn't a subtype of type",
            r"The argument type.*can't be assigned to the parameter type",
        ],
        "null_safety": [
            r"can't be assigned to a variable of type.*because.*nullable",
            r"The value 'null'.*can't be returned from",
            r"A value of type.*can't be assigned.*nullable",
        ],
        "missing_overrides": [
            r"Missing.*override",
            r"doesn't override.*inherited",
        ],
        "formatting": [
            r"Line is longer than",
            r"Prefer.*final.*for",
            r"Sort.*directives",
        ],
    }

    # Cleanup issues: Fix ALL at once (human: "I'll clean up all X today")
    CLEANUP_PATTERNS = [
        "unused_imports",
        "formatting",
    ]

    # Location-based: Group by directory/screen if multiple issues in same area
    LOCATION_BASED_PATTERNS = [
        "type_mismatches",
        "null_safety",
        "missing_imports",
    ]

    def __init__(
        self,
        max_cleanup_batch_size: int = 50,
        max_location_batch_size: int = 20,
        mega_batch_mode: bool = False,
    ):
        """
        Args:
            max_cleanup_batch_size: Max issues in cleanup batch (unused imports, etc.)
            max_location_batch_size: Max issues per directory/screen batch
            mega_batch_mode: If True, create one comprehensive mega-batch per phase
        """
        self.max_cleanup_batch_size = max_cleanup_batch_size
        self.max_location_batch_size = max_location_batch_size
        self.mega_batch_mode = mega_batch_mode

    def group_tasks(self, tasks: list[Task]) -> list[Task]:
        """
        Group tasks for human-reviewable commits with clear separation of concerns.

        Strategies:
        1. Cleanup commits: "Remove all unused imports" (project-wide, one type)
        2. Location commits: "Fix errors in home screen" (one screen/module)
        3. Type + Location: "Fix type errors in auth/" (similar issue, same area)
        """
        if self.mega_batch_mode:
            # Mega mode: ONE comprehensive batch for everything
            return self._create_mega_batch(tasks)

        # Categorize tasks by pattern
        categorized = self._categorize_tasks(tasks)

        result_tasks = []

        for batch_type, task_list in categorized.items():
            if len(task_list) == 0:
                continue

            is_cleanup = batch_type in self.CLEANUP_PATTERNS
            is_location_based = batch_type in self.LOCATION_BASED_PATTERNS

            # Cleanup commits: "Remove all unused imports" (clear, atomic)
            if is_cleanup and len(task_list) >= 2:
                print(f"  🧹 Cleanup batch: {len(task_list)} {batch_type}")
                batches = self._create_cleanup_batches(task_list, batch_type)
                result_tasks.extend(batches)

            # Location-based commits: "Fix type errors in home/" (scoped, reviewable)
            elif is_location_based and len(task_list) >= 3:
                print(f"  📍 Location-based batching: {len(task_list)} {batch_type}")
                batches = self._create_location_batches(task_list, batch_type)
                result_tasks.extend(batches)

            # Keep as individual if too complex to batch
            else:
                result_tasks.extend(task_list)

        # Add uncategorized tasks
        if "uncategorized" in categorized:
            result_tasks.extend(categorized["uncategorized"])

        print("\n📦 Grouping results:")
        print(f"   Input tasks: {len(tasks)}")
        print(f"   Output tasks: {len(result_tasks)}")

        batch_count = sum(1 for t in result_tasks if isinstance(t, BatchTask))
        print(f"   Batch tasks: {batch_count}")
        print(f"   Individual tasks: {len(result_tasks) - batch_count}")

        return result_tasks

    def _create_mega_batch(self, tasks: list[Task]) -> list[Task]:
        """
        Mega batch mode: Create ONE comprehensive task with ALL issues.

        Human thinking: "Fix all build errors comprehensively in one session"
        """
        if not tasks:
            return []

        # Group all tasks into one mega batch
        related_issues = [
            {"file": t.file, "line": t.line, "message": t.message, "type": t.type} for t in tasks
        ]

        unique_files = list({t.file for t in tasks if t.file})

        # Create categorized summary
        by_type = defaultdict(list)
        for t in tasks:
            msg = t.message
            # Categorize
            if "import" in msg.lower():
                by_type["unused_imports"].append(t)
            elif "type" in msg.lower():
                by_type["type_errors"].append(t)
            elif "null" in msg.lower():
                by_type["null_safety"].append(t)
            else:
                by_type["other"].append(t)

        context_parts = [f"Fix ALL issues comprehensively ({len(tasks)} total):"]
        context_parts.append(f"\nAffected files: {len(unique_files)}")

        for category, cat_tasks in sorted(by_type.items()):
            if cat_tasks:
                context_parts.append(f"\n\n**{category.upper()}** ({len(cat_tasks)} issues):")
                for t in cat_tasks[:10]:  # Show first 10 per category
                    context_parts.append(f"  - {t.file}:{t.line} - {t.message[:60]}")
                if len(cat_tasks) > 10:
                    context_parts.append(f"  ... and {len(cat_tasks) - 10} more")

        mega_task = BatchTask(
            id=generate_task_id(),
            type="fix_mega_batch",
            priority=1,
            phase=tasks[0].phase if tasks else "build",
            file="project-wide",
            message=(
                f"Fix all issues comprehensively "
                f"({len(tasks)} issues, {len(unique_files)} files)"
            ),
            context="\n".join(context_parts),
            created_at=datetime.now().isoformat(),
            related_issues=related_issues,
            batch_type="mega_comprehensive",
        )

        print("\n📦 Mega Batch Mode:")
        print(f"   Input tasks: {len(tasks)}")
        print("   Output: 1 comprehensive mega-batch")

        return [mega_task]

    def _categorize_tasks(self, tasks: list[Task]) -> dict[str, list[Task]]:
        """Categorize tasks by issue pattern"""
        categorized = defaultdict(list)

        for task in tasks:
            message = task.message
            matched = False

            for batch_type, patterns in self.BATCH_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, message, re.IGNORECASE):
                        categorized[batch_type].append(task)
                        matched = True
                        break
                if matched:
                    break

            if not matched:
                categorized["uncategorized"].append(task)

        return dict(categorized)

    def _create_cleanup_batches(self, tasks: list[Task], batch_type: str) -> list[Task]:
        """
        Create cleanup batches: Fix ALL issues of this type (split only if >50 files).

        Human thinking: "I'll clean up all unused imports today"
        """
        batches = []

        # Split only if really necessary (>max_cleanup_batch_size)
        for i in range(0, len(tasks), self.max_cleanup_batch_size):
            chunk = tasks[i : i + self.max_cleanup_batch_size]

            related_issues = [{"file": t.file, "line": t.line, "message": t.message} for t in chunk]

            unique_files = list({t.file for t in chunk if t.file})
            context_summary = self._create_context_summary(chunk)

            batch_task = BatchTask(
                id=generate_task_id(),
                type=f"fix_cleanup_{batch_type}",
                priority=chunk[0].priority if chunk else 5,
                phase=chunk[0].phase if chunk else "build",
                file="project-wide",
                message=(
                    f"Clean up ALL {batch_type} "
                    f"({len(chunk)} issues, {len(unique_files)} files)"
                ),
                context=context_summary,
                created_at=datetime.now().isoformat(),
                related_issues=related_issues,
                batch_type=batch_type,
            )

            batches.append(batch_task)

        return batches

    def _create_location_batches(self, tasks: list[Task], batch_type: str) -> list[Task]:
        """
        Create location-based batches: Group by directory/screen.

        Human thinking: "I'll fix all the home screen errors"
        """
        # Group by directory
        by_directory = defaultdict(list)
        for task in tasks:
            if task.file:
                # Extract directory (e.g., lib/screens/home/ from lib/screens/home/home_screen.dart)
                parts = task.file.split("/")
                if len(parts) > 2:
                    directory = "/".join(parts[:-1])  # Remove filename
                else:
                    directory = parts[0] if parts else "root"
                by_directory[directory].append(task)
            else:
                by_directory["unknown"].append(task)

        batches = []
        individual = []

        for directory, dir_tasks in by_directory.items():
            # If multiple issues in same directory, batch them
            if len(dir_tasks) >= 3:
                # Split if too many
                for i in range(0, len(dir_tasks), self.max_location_batch_size):
                    chunk = dir_tasks[i : i + self.max_location_batch_size]

                    related_issues = [
                        {"file": t.file, "line": t.line, "message": t.message} for t in chunk
                    ]

                    unique_files = list({t.file for t in chunk if t.file})
                    context_summary = self._create_context_summary(chunk)

                    # Create friendly name for directory
                    dir_name = directory.split("/")[-1] if "/" in directory else directory

                    batch_task = BatchTask(
                        id=generate_task_id(),
                        type=f"fix_location_{batch_type}",
                        priority=chunk[0].priority if chunk else 5,
                        phase=chunk[0].phase if chunk else "build",
                        file=directory,
                        message=(
                            f"Fix {batch_type} in {dir_name}/ "
                            f"({len(chunk)} issues, {len(unique_files)} files)"
                        ),
                        context=context_summary,
                        created_at=datetime.now().isoformat(),
                        related_issues=related_issues,
                        batch_type=f"{batch_type}_in_{dir_name}",
                    )

                    batches.append(batch_task)
            else:
                # Keep as individual tasks
                individual.extend(dir_tasks)

        return batches + individual

    def _create_context_summary(self, tasks: list[Task]) -> str:
        """Create summarized context for batch task"""
        # Group by file
        by_file = defaultdict(list)
        for task in tasks:
            if task.file:
                by_file[task.file].append(task)

        summary_parts = []
        summary_parts.append(f"Fixing {len(tasks)} related issues:\n")

        for file, file_tasks in sorted(by_file.items())[:5]:  # Max 5 files in summary
            summary_parts.append(f"\n📄 {file}:")
            for task in file_tasks[:3]:  # Max 3 issues per file
                summary_parts.append(f"  - Line {task.line}: {task.message[:80]}")
            if len(file_tasks) > 3:
                summary_parts.append(f"  ... and {len(file_tasks) - 3} more")

        if len(by_file) > 5:
            summary_parts.append(f"\n... and {len(by_file) - 5} more files")

        return "\n".join(summary_parts)


def main():
    """CLI testing"""
    from state_manager import Task

    # Create test tasks
    test_tasks = [
        Task(
            id=f"task_{i}",
            type="fix_build_error",
            priority=1,
            phase="build",
            file=f"lib/file{i % 3}.dart",
            line=i * 10,
            message="Unused import: 'package:flutter/material.dart'",
            context="import 'package:flutter/material.dart';",
            created_at=datetime.now().isoformat(),
        )
        for i in range(5)
    ]

    # Add some type errors
    for i in range(3):
        test_tasks.append(
            Task(
                id=f"task_type_{i}",
                type="fix_build_error",
                priority=1,
                phase="build",
                file=f"lib/types{i}.dart",
                line=i * 20,
                message="The argument type 'String' can't be assigned to the parameter type 'int'",
                context="function(myString);",
                created_at=datetime.now().isoformat(),
            )
        )

    grouper = IssueGrouper(min_batch_size=3, max_batch_size=5)
    result = grouper.group_tasks(test_tasks)

    print("\n📋 Result tasks:")
    for task in result:
        if isinstance(task, BatchTask):
            print(f"  [BATCH] {task.message}")
            print(f"    Related issues: {len(task.related_issues)}")
        else:
            print(f"  [SINGLE] {task.message}")


if __name__ == "__main__":
    main()
