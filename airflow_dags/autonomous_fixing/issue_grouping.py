#!/usr/bin/env python3
"""
Issue grouping module.
Groups similar issues for batch fixing.
"""

import re
from typing import List, Dict
from dataclasses import dataclass
from collections import defaultdict

from state_manager import Task, generate_task_id
from datetime import datetime


@dataclass
class BatchTask(Task):
    """Task representing a batch of similar issues"""
    related_issues: List[Dict] = None  # List of {file, line, message}
    batch_type: str = None  # Type of batch (unused_imports, type_errors, etc.)

    def __post_init__(self):
        if self.related_issues is None:
            self.related_issues = []


class IssueGrouper:
    """Group similar issues for efficient batch fixing"""

    # Issue patterns to group together
    BATCH_PATTERNS = {
        'unused_imports': [
            r"Unused import",
            r"import.*isn't used",
        ],
        'missing_imports': [
            r"Undefined (name|class|method)",
            r"The (function|method|getter|setter) '.*' isn't defined",
        ],
        'type_mismatches': [
            r"type '.*' isn't a subtype of type",
            r"The argument type.*can't be assigned to the parameter type",
        ],
        'null_safety': [
            r"can't be assigned to a variable of type.*because.*nullable",
            r"The value 'null'.*can't be returned from",
            r"A value of type.*can't be assigned.*nullable",
        ],
        'missing_overrides': [
            r"Missing.*override",
            r"doesn't override.*inherited",
        ],
        'formatting': [
            r"Line is longer than",
            r"Prefer.*final.*for",
            r"Sort.*directives",
        ]
    }

    # Trivial issues that should be batched (not fixed individually)
    TRIVIAL_PATTERNS = [
        'unused_imports',
        'formatting',
    ]

    # Substantial issues that can be batched if many exist
    SUBSTANTIAL_PATTERNS = [
        'type_mismatches',
        'null_safety',
        'missing_overrides',
    ]

    def __init__(self, min_batch_size: int = 3, max_batch_size: int = 10):
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size

    def group_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Group similar tasks into batches.
        Returns list of individual and batch tasks.
        """
        # Categorize tasks by pattern
        categorized = self._categorize_tasks(tasks)

        result_tasks = []

        for batch_type, task_list in categorized.items():
            if len(task_list) == 0:
                continue

            is_trivial = batch_type in self.TRIVIAL_PATTERNS
            is_substantial = batch_type in self.SUBSTANTIAL_PATTERNS

            # Trivial issues: always batch (don't fix individually)
            if is_trivial:
                batches = self._create_batches(task_list, batch_type, force_batch=True)
                result_tasks.extend(batches)

            # Substantial issues: batch if many exist
            elif is_substantial and len(task_list) >= self.min_batch_size:
                batches = self._create_batches(task_list, batch_type)
                result_tasks.extend(batches)

            # Otherwise: keep as individual tasks
            else:
                result_tasks.extend(task_list)

        # Add uncategorized tasks
        if 'uncategorized' in categorized:
            result_tasks.extend(categorized['uncategorized'])

        print(f"\n📦 Grouping results:")
        print(f"   Input tasks: {len(tasks)}")
        print(f"   Output tasks: {len(result_tasks)}")

        batch_count = sum(1 for t in result_tasks if isinstance(t, BatchTask))
        print(f"   Batch tasks: {batch_count}")
        print(f"   Individual tasks: {len(result_tasks) - batch_count}")

        return result_tasks

    def _categorize_tasks(self, tasks: List[Task]) -> Dict[str, List[Task]]:
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
                categorized['uncategorized'].append(task)

        return dict(categorized)

    def _create_batches(
        self,
        tasks: List[Task],
        batch_type: str,
        force_batch: bool = False
    ) -> List[Task]:
        """
        Create batch tasks from list of similar tasks.

        Args:
            tasks: List of similar tasks
            batch_type: Type of batch
            force_batch: If True, create batches even for small groups
        """
        if not force_batch and len(tasks) < self.min_batch_size:
            return tasks

        batches = []

        # Split into chunks of max_batch_size
        for i in range(0, len(tasks), self.max_batch_size):
            chunk = tasks[i:i + self.max_batch_size]

            # Create batch task
            related_issues = [
                {
                    'file': t.file,
                    'line': t.line,
                    'message': t.message,
                }
                for t in chunk
            ]

            # Aggregate context from all files
            unique_files = list(set(t.file for t in chunk if t.file))
            context_summary = self._create_context_summary(chunk)

            batch_task = BatchTask(
                id=generate_task_id(),
                type=f"fix_batch_{batch_type}",
                priority=chunk[0].priority if chunk else 5,
                phase=chunk[0].phase if chunk else "build",
                file=", ".join(unique_files[:3]),  # List first 3 files
                message=f"Batch fix: {len(chunk)} {batch_type} issues across {len(unique_files)} files",
                context=context_summary,
                created_at=datetime.now().isoformat(),
                related_issues=related_issues,
                batch_type=batch_type
            )

            batches.append(batch_task)

        return batches

    def _create_context_summary(self, tasks: List[Task]) -> str:
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

        return '\n'.join(summary_parts)


def main():
    """CLI testing"""
    import sys
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
            created_at=datetime.now().isoformat()
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
                created_at=datetime.now().isoformat()
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
