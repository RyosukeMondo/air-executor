#!/usr/bin/env python3
"""
Lightweight code quality metrics for Flutter/Dart.
Checks file size, complexity, nesting depth without heavy analysis tools.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class FileMetrics:
    """Metrics for a single file"""
    path: str
    lines: int
    max_nesting_depth: int
    complexity_estimate: int
    classes: int
    functions: int
    issues: List[str]


@dataclass
class ProjectMetrics:
    """Aggregate project metrics"""
    total_files: int
    total_lines: int
    avg_file_size: int
    max_file_size: int
    files_over_threshold: List[Tuple[str, int]]  # (path, line_count)
    max_nesting_depth: int
    high_complexity_files: List[Tuple[str, int]]  # (path, complexity)
    health_score: float


class LightweightCodeMetrics:
    """Fast code quality metrics without external tools"""

    def __init__(self, project_path: str, file_size_threshold: int = 300):
        self.project_path = Path(project_path)
        self.file_size_threshold = file_size_threshold

    def analyze_project(self) -> ProjectMetrics:
        """Analyze all Dart files in project"""
        dart_files = list(self.project_path.rglob("*.dart"))

        # Skip generated and test files for metrics
        dart_files = [
            f for f in dart_files
            if not any(part in str(f) for part in ['.g.dart', '.freezed.dart', '.mocks.dart', 'generated'])
        ]

        file_metrics = [self._analyze_file(f) for f in dart_files]

        # Aggregate metrics
        total_files = len(file_metrics)
        total_lines = sum(m.lines for m in file_metrics)
        avg_file_size = total_lines // total_files if total_files > 0 else 0

        files_over_threshold = [
            (m.path, m.lines)
            for m in file_metrics
            if m.lines > self.file_size_threshold
        ]
        files_over_threshold.sort(key=lambda x: x[1], reverse=True)

        max_file_size = max((m.lines for m in file_metrics), default=0)
        max_nesting = max((m.max_nesting_depth for m in file_metrics), default=0)

        high_complexity = [
            (m.path, m.complexity_estimate)
            for m in file_metrics
            if m.complexity_estimate > 10
        ]
        high_complexity.sort(key=lambda x: x[1], reverse=True)

        # Calculate health score
        health_score = self._calculate_health_score(
            avg_file_size,
            len(files_over_threshold),
            total_files,
            max_nesting,
            len(high_complexity)
        )

        return ProjectMetrics(
            total_files=total_files,
            total_lines=total_lines,
            avg_file_size=avg_file_size,
            max_file_size=max_file_size,
            files_over_threshold=files_over_threshold[:10],  # Top 10
            max_nesting_depth=max_nesting,
            high_complexity_files=high_complexity[:10],  # Top 10
            health_score=health_score
        )

    def _analyze_file(self, filepath: Path) -> FileMetrics:
        """Analyze a single Dart file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            code_lines = [l for l in lines if l.strip() and not l.strip().startswith('//')]
            line_count = len(code_lines)

            max_nesting = self._calculate_max_nesting(code_lines)
            complexity = self._estimate_complexity(code_lines)
            classes = self._count_pattern(code_lines, r'^\s*class\s+\w+')
            functions = self._count_pattern(code_lines, r'^\s*\w+\s+\w+\s*\(')

            issues = []
            if line_count > self.file_size_threshold:
                issues.append(f"File too large: {line_count} lines")
            if max_nesting > 4:
                issues.append(f"Deep nesting: {max_nesting} levels")
            if complexity > 15:
                issues.append(f"High complexity: {complexity}")

            return FileMetrics(
                path=str(filepath.relative_to(self.project_path)),
                lines=line_count,
                max_nesting_depth=max_nesting,
                complexity_estimate=complexity,
                classes=classes,
                functions=functions,
                issues=issues
            )

        except Exception as e:
            return FileMetrics(
                path=str(filepath.relative_to(self.project_path)),
                lines=0,
                max_nesting_depth=0,
                complexity_estimate=0,
                classes=0,
                functions=0,
                issues=[f"Error reading file: {e}"]
            )

    def _calculate_max_nesting(self, lines: List[str]) -> int:
        """Calculate maximum nesting depth"""
        max_depth = 0
        current_depth = 0

        for line in lines:
            stripped = line.strip()

            # Count opening braces
            current_depth += stripped.count('{')

            # Track max
            max_depth = max(max_depth, current_depth)

            # Count closing braces
            current_depth -= stripped.count('}')

        return max_depth

    def _estimate_complexity(self, lines: List[str]) -> int:
        """Estimate cyclomatic complexity (decision points)"""
        complexity = 1  # Base complexity

        decision_keywords = ['if', 'else if', 'for', 'while', 'case', '&&', '||', '??', '?']

        for line in lines:
            stripped = line.strip().lower()
            for keyword in decision_keywords:
                if keyword in stripped:
                    complexity += stripped.count(keyword)

        return complexity

    def _count_pattern(self, lines: List[str], pattern: str) -> int:
        """Count occurrences of regex pattern"""
        count = 0
        for line in lines:
            if re.search(pattern, line):
                count += 1
        return count

    def _calculate_health_score(
        self,
        avg_file_size: int,
        files_over_threshold: int,
        total_files: int,
        max_nesting: int,
        high_complexity_count: int
    ) -> float:
        """Calculate code quality health score (0.0 - 1.0)"""
        score = 1.0

        # File size penalty
        if avg_file_size > self.file_size_threshold:
            score -= 0.2
        if total_files > 0:
            over_threshold_ratio = files_over_threshold / total_files
            score -= over_threshold_ratio * 0.2

        # Nesting penalty
        if max_nesting > 4:
            score -= 0.2
        if max_nesting > 6:
            score -= 0.2

        # Complexity penalty
        if high_complexity_count > 0:
            complexity_ratio = high_complexity_count / total_files if total_files > 0 else 0
            score -= complexity_ratio * 0.2

        return max(0.0, min(1.0, score))


def main():
    """CLI entry point"""
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python code_metrics.py <project_path> [--threshold=300]")
        sys.exit(1)

    project_path = sys.argv[1]
    threshold = 300

    for arg in sys.argv:
        if arg.startswith("--threshold="):
            threshold = int(arg.split("=")[1])

    analyzer = LightweightCodeMetrics(project_path, threshold)
    metrics = analyzer.analyze_project()

    print(f"\n📊 Code Quality Metrics: {Path(project_path).name}")
    print("=" * 60)

    print(f"\n📁 Files:")
    print(f"  Total: {metrics.total_files}")
    print(f"  Total lines: {metrics.total_lines:,}")
    print(f"  Avg file size: {metrics.avg_file_size} lines")
    print(f"  Max file size: {metrics.max_file_size} lines")

    if metrics.files_over_threshold:
        print(f"\n⚠️ Files over {threshold} lines: {len(metrics.files_over_threshold)}")
        for path, lines in metrics.files_over_threshold[:5]:
            print(f"    {path}: {lines} lines")

    print(f"\n🔀 Complexity:")
    print(f"  Max nesting depth: {metrics.max_nesting_depth}")
    if metrics.high_complexity_files:
        print(f"  High complexity files: {len(metrics.high_complexity_files)}")
        for path, complexity in metrics.high_complexity_files[:5]:
            print(f"    {path}: complexity ~{complexity}")

    print(f"\n✅ Code Quality Score: {metrics.health_score:.0%}")
    print("=" * 60)

    if "--json" in sys.argv:
        print(json.dumps({
            "total_files": metrics.total_files,
            "total_lines": metrics.total_lines,
            "avg_file_size": metrics.avg_file_size,
            "max_file_size": metrics.max_file_size,
            "files_over_threshold": len(metrics.files_over_threshold),
            "max_nesting_depth": metrics.max_nesting_depth,
            "high_complexity_files": len(metrics.high_complexity_files),
            "health_score": metrics.health_score
        }, indent=2))


if __name__ == "__main__":
    main()
