#!/usr/bin/env python3
"""
Test and coverage metrics for Flutter projects.
Tracks unit tests, integration tests, e2e tests, and code coverage.
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class TestBreakdown:
    """Test metrics by type"""
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    failures: List[str] = None

    def __post_init__(self):
        if self.failures is None:
            self.failures = []

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0


@dataclass
class CoverageMetrics:
    """Code coverage metrics"""
    total_lines: int = 0
    covered_lines: int = 0
    coverage_percent: float = 0.0
    uncovered_files: List[Tuple[str, float]] = None  # (file, coverage%)

    def __post_init__(self):
        if self.uncovered_files is None:
            self.uncovered_files = []


@dataclass
class TestMetrics:
    """Complete test metrics"""
    # Test counts by type
    unit_tests: TestBreakdown
    integration_tests: TestBreakdown
    e2e_tests: TestBreakdown
    widget_tests: TestBreakdown

    # Overall
    total_tests: int
    total_passed: int
    total_failed: int
    overall_pass_rate: float

    # Coverage
    coverage: CoverageMetrics

    # Quality score
    test_quality_score: float

    def to_dict(self) -> dict:
        return {
            'unit_tests': asdict(self.unit_tests),
            'integration_tests': asdict(self.integration_tests),
            'e2e_tests': asdict(self.e2e_tests),
            'widget_tests': asdict(self.widget_tests),
            'total_tests': self.total_tests,
            'total_passed': self.total_passed,
            'total_failed': self.total_failed,
            'overall_pass_rate': self.overall_pass_rate,
            'coverage': asdict(self.coverage),
            'test_quality_score': self.test_quality_score
        }


class FlutterTestAnalyzer:
    """Analyze Flutter tests and coverage"""

    def __init__(self, project_path: str, flutter_bin: str = None):
        self.project_path = Path(project_path)
        self.flutter_bin = flutter_bin or self._find_flutter()

    def _find_flutter(self) -> str:
        """Find Flutter binary"""
        import os
        import shutil

        flutter = shutil.which("flutter")
        if flutter:
            return flutter

        locations = [
            os.path.expanduser("~/flutter/bin/flutter"),
            "/usr/local/bin/flutter"
        ]

        for location in locations:
            if os.path.exists(location):
                return location

        return "flutter"

    def analyze(self, run_coverage: bool = True, timeout: int = 300) -> TestMetrics:
        """Run tests and collect metrics"""
        print("🧪 Analyzing tests...")

        # Categorize test files
        unit_files, integration_files, e2e_files, widget_files = self._categorize_tests()

        # Run tests by type
        unit = self._run_tests(unit_files, "Unit", timeout=timeout)
        integration = self._run_tests(integration_files, "Integration", timeout=timeout)
        e2e = self._run_tests(e2e_files, "E2E", timeout=timeout)
        widget = self._run_tests(widget_files, "Widget", timeout=timeout)

        # Overall stats
        total_tests = sum([unit.total, integration.total, e2e.total, widget.total])
        total_passed = sum([unit.passed, integration.passed, e2e.passed, widget.passed])
        total_failed = sum([unit.failed, integration.failed, e2e.failed, widget.failed])
        overall_pass_rate = total_passed / total_tests if total_tests > 0 else 0.0

        # Coverage
        coverage = CoverageMetrics()
        if run_coverage and total_tests > 0:
            coverage = self._analyze_coverage(timeout=timeout)

        # Quality score
        quality_score = self._calculate_quality_score(
            overall_pass_rate,
            coverage.coverage_percent,
            total_tests,
            unit.total,
            integration.total
        )

        return TestMetrics(
            unit_tests=unit,
            integration_tests=integration,
            e2e_tests=e2e,
            widget_tests=widget,
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            overall_pass_rate=overall_pass_rate,
            coverage=coverage,
            test_quality_score=quality_score
        )

    def _categorize_tests(self) -> Tuple[List[Path], List[Path], List[Path], List[Path]]:
        """Categorize test files by type"""
        test_dir = self.project_path / "test"
        integration_dir = self.project_path / "integration_test"

        unit_tests = []
        integration_tests = []
        e2e_tests = []
        widget_tests = []

        # Unit tests (in test/ directory, not widget tests)
        if test_dir.exists():
            for test_file in test_dir.rglob("*_test.dart"):
                content = test_file.read_text()
                if "testWidgets" in content or "WidgetTester" in content:
                    widget_tests.append(test_file)
                else:
                    unit_tests.append(test_file)

        # Integration tests
        if integration_dir.exists():
            for test_file in integration_dir.rglob("*_test.dart"):
                content = test_file.read_text()
                if "IntegrationTestWidgetsFlutterBinding" in content or "_integration_" in str(test_file):
                    integration_tests.append(test_file)
                else:
                    # Check if it's e2e based on content/naming
                    if "e2e" in str(test_file).lower() or "end_to_end" in str(test_file):
                        e2e_tests.append(test_file)
                    else:
                        integration_tests.append(test_file)

        return unit_tests, integration_tests, e2e_tests, widget_tests

    def _run_tests(self, test_files: List[Path], test_type: str, timeout: int) -> TestBreakdown:
        """Run specific test files and collect results"""
        if not test_files:
            return TestBreakdown()

        print(f"  Running {test_type} tests ({len(test_files)} files)...")

        total = 0
        passed = 0
        failed = 0
        skipped = 0
        failures = []

        try:
            # Run all tests of this type
            result = subprocess.run(
                [self.flutter_bin, "test", "--reporter=json", "--no-pub"] + [str(f) for f in test_files],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Parse JSON output
            for line in result.stdout.splitlines():
                try:
                    event = json.loads(line)

                    if event.get('type') == 'testDone':
                        total += 1
                        test_result = event.get('result')

                        if test_result == 'success':
                            passed += 1
                        elif test_result == 'error' or test_result == 'failure':
                            failed += 1
                            test_name = event.get('test', {}).get('name', 'Unknown')
                            failures.append(f"{test_type}: {test_name}")
                        elif test_result == 'skipped':
                            skipped += 1

                except json.JSONDecodeError:
                    continue

        except subprocess.TimeoutExpired:
            failures.append(f"{test_type} tests timeout")
        except Exception as e:
            failures.append(f"{test_type} execution error: {str(e)}")

        return TestBreakdown(
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            failures=failures
        )

    def _analyze_coverage(self, timeout: int) -> CoverageMetrics:
        """Analyze code coverage"""
        print("  Collecting coverage...")

        try:
            # Run tests with coverage
            result = subprocess.run(
                [self.flutter_bin, "test", "--coverage", "--no-pub"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Parse lcov.info
            lcov_path = self.project_path / "coverage" / "lcov.info"

            if not lcov_path.exists():
                return CoverageMetrics()

            total_lines = 0
            covered_lines = 0
            file_coverage = {}

            current_file = None

            with open(lcov_path, 'r') as f:
                for line in f:
                    if line.startswith('SF:'):
                        current_file = line[3:].strip()
                        file_coverage[current_file] = {'total': 0, 'covered': 0}
                    elif line.startswith('DA:'):
                        # DA:line_number,hit_count
                        parts = line[3:].strip().split(',')
                        if len(parts) == 2:
                            hit_count = int(parts[1])
                            total_lines += 1
                            if current_file:
                                file_coverage[current_file]['total'] += 1

                            if hit_count > 0:
                                covered_lines += 1
                                if current_file:
                                    file_coverage[current_file]['covered'] += 1

            coverage_percent = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0

            # Find files with low coverage
            uncovered = []
            for file, data in file_coverage.items():
                if data['total'] > 0:
                    file_cov = (data['covered'] / data['total']) * 100
                    if file_cov < 80:  # Below 80% coverage
                        # Get relative path
                        try:
                            rel_path = str(Path(file).relative_to(self.project_path))
                        except:
                            rel_path = file
                        uncovered.append((rel_path, file_cov))

            uncovered.sort(key=lambda x: x[1])  # Sort by coverage (lowest first)

            return CoverageMetrics(
                total_lines=total_lines,
                covered_lines=covered_lines,
                coverage_percent=round(coverage_percent, 1),
                uncovered_files=uncovered[:10]  # Top 10 worst coverage
            )

        except Exception as e:
            print(f"  ⚠️ Coverage analysis failed: {e}")
            return CoverageMetrics()

    def _calculate_quality_score(
        self,
        pass_rate: float,
        coverage: float,
        total_tests: int,
        unit_tests: int,
        integration_tests: int
    ) -> float:
        """Calculate test quality score (0.0 - 1.0)"""
        score = 0.0

        # Pass rate: 40% weight
        score += pass_rate * 0.4

        # Coverage: 30% weight
        score += (coverage / 100) * 0.3

        # Test existence: 20% weight
        if total_tests > 0:
            score += 0.2

        # Test diversity: 10% weight (both unit and integration tests)
        if unit_tests > 0 and integration_tests > 0:
            score += 0.1
        elif unit_tests > 0 or integration_tests > 0:
            score += 0.05

        return round(score, 2)


def main():
    """CLI entry point"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_metrics.py <project_path> [--no-coverage] [--json]")
        sys.exit(1)

    project_path = sys.argv[1]
    run_coverage = "--no-coverage" not in sys.argv
    output_json = "--json" in sys.argv

    analyzer = FlutterTestAnalyzer(project_path)
    metrics = analyzer.analyze(run_coverage=run_coverage, timeout=300)

    if output_json:
        print(json.dumps(metrics.to_dict(), indent=2))
    else:
        print("\n" + "=" * 60)
        print("🧪 Test Metrics Summary")
        print("=" * 60)

        print(f"\n📊 Overall:")
        print(f"  Total tests: {metrics.total_tests}")
        print(f"  Passed: {metrics.total_passed}")
        print(f"  Failed: {metrics.total_failed}")
        print(f"  Pass rate: {metrics.overall_pass_rate:.1%}")

        print(f"\n🔬 Unit Tests:")
        print(f"  Total: {metrics.unit_tests.total}")
        print(f"  Pass rate: {metrics.unit_tests.pass_rate:.1%}")
        if metrics.unit_tests.failures:
            print(f"  Failures: {len(metrics.unit_tests.failures)}")

        print(f"\n🔗 Integration Tests:")
        print(f"  Total: {metrics.integration_tests.total}")
        print(f"  Pass rate: {metrics.integration_tests.pass_rate:.1%}")

        print(f"\n🎯 E2E Tests:")
        print(f"  Total: {metrics.e2e_tests.total}")
        print(f"  Pass rate: {metrics.e2e_tests.pass_rate:.1%}")

        print(f"\n🎨 Widget Tests:")
        print(f"  Total: {metrics.widget_tests.total}")
        print(f"  Pass rate: {metrics.widget_tests.pass_rate:.1%}")

        if run_coverage:
            print(f"\n📈 Coverage:")
            print(f"  Total lines: {metrics.coverage.total_lines}")
            print(f"  Covered: {metrics.coverage.covered_lines}")
            print(f"  Coverage: {metrics.coverage.coverage_percent:.1f}%")

            if metrics.coverage.uncovered_files:
                print(f"\n  📉 Low coverage files:")
                for file, cov in metrics.coverage.uncovered_files[:5]:
                    print(f"    {file}: {cov:.1f}%")

        print(f"\n✅ Test Quality Score: {metrics.test_quality_score:.0%}")
        print("=" * 60)


if __name__ == "__main__":
    main()
