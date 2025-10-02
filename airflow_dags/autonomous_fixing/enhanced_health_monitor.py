#!/usr/bin/env python3
"""
Enhanced health monitoring with test coverage and code quality metrics.
Combines build status, tests, coverage, and code quality into comprehensive health score.
"""

import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from health_monitor import FlutterHealthMonitor, HealthMetrics
from test_metrics import FlutterTestAnalyzer, TestMetrics
from code_metrics import LightweightCodeMetrics, ProjectMetrics


@dataclass
class EnhancedHealthMetrics:
    """Comprehensive health metrics"""
    timestamp: str
    project_path: str

    # Build & Analysis
    build_status: str
    build_errors: int
    build_warnings: int
    analysis_errors: int
    analysis_warnings: int

    # Tests
    total_tests: int
    test_pass_rate: float
    unit_tests: int
    integration_tests: int
    e2e_tests: int
    widget_tests: int
    coverage_percent: float

    # Code Quality
    total_files: int
    avg_file_size: int
    files_over_threshold: int
    max_nesting_depth: int
    high_complexity_files: int
    code_quality_score: float

    # Overall
    health_score: float
    test_quality_score: float
    is_healthy: bool

    # Details for debugging
    test_failures: list
    uncovered_files: list

    def to_dict(self) -> dict:
        return asdict(self)


class EnhancedHealthMonitor:
    """Comprehensive health monitoring"""

    def __init__(
        self,
        project_path: str,
        file_size_threshold: int = 300,
        coverage_threshold: float = 80.0,
        test_timeout: int = 300
    ):
        self.project_path = Path(project_path)
        self.file_size_threshold = file_size_threshold
        self.coverage_threshold = coverage_threshold
        self.test_timeout = test_timeout

        # Initialize monitors
        self.build_monitor = FlutterHealthMonitor(str(project_path))
        self.test_analyzer = FlutterTestAnalyzer(str(project_path))
        self.code_analyzer = LightweightCodeMetrics(str(project_path), file_size_threshold)

    def collect_all_metrics(self, run_tests: bool = True, run_coverage: bool = False) -> EnhancedHealthMetrics:
        """Collect comprehensive health metrics"""
        print(f"🔍 Enhanced Health Check: {self.project_path.name}")
        print("=" * 60)

        # 1. Build & Analysis
        print("\n📦 Build & Analysis...")
        build_metrics = self.build_monitor.collect_metrics()

        # 2. Tests (optional, can be slow)
        test_metrics = None
        if run_tests:
            print("\n🧪 Tests & Coverage...")
            test_metrics = self.test_analyzer.analyze(
                run_coverage=run_coverage,
                timeout=self.test_timeout
            )
        else:
            print("\n⏭️ Skipping tests (use --tests flag to run)")

        # 3. Code Quality
        print("\n📊 Code Quality...")
        code_metrics = self.code_analyzer.analyze_project()

        # 4. Calculate comprehensive health score
        health_score = self._calculate_health_score(
            build_metrics,
            test_metrics,
            code_metrics
        )

        # Collect test details
        test_failures = []
        uncovered_files = []

        if test_metrics:
            test_failures = (
                test_metrics.unit_tests.failures[:5] +
                test_metrics.integration_tests.failures[:5] +
                test_metrics.e2e_tests.failures[:5]
            )
            uncovered_files = [
                {"file": f, "coverage": c}
                for f, c in test_metrics.coverage.uncovered_files[:5]
            ]

        enhanced = EnhancedHealthMetrics(
            timestamp=datetime.now().isoformat(),
            project_path=str(self.project_path),

            # Build
            build_status=build_metrics.build_status,
            build_errors=len(build_metrics.build_errors),
            build_warnings=len(build_metrics.build_warnings),
            analysis_errors=build_metrics.analysis_errors,
            analysis_warnings=build_metrics.analysis_warnings,

            # Tests
            total_tests=test_metrics.total_tests if test_metrics else 0,
            test_pass_rate=test_metrics.overall_pass_rate if test_metrics else 0.0,
            unit_tests=test_metrics.unit_tests.total if test_metrics else 0,
            integration_tests=test_metrics.integration_tests.total if test_metrics else 0,
            e2e_tests=test_metrics.e2e_tests.total if test_metrics else 0,
            widget_tests=test_metrics.widget_tests.total if test_metrics else 0,
            coverage_percent=test_metrics.coverage.coverage_percent if test_metrics else 0.0,

            # Code Quality
            total_files=code_metrics.total_files,
            avg_file_size=code_metrics.avg_file_size,
            files_over_threshold=len(code_metrics.files_over_threshold),
            max_nesting_depth=code_metrics.max_nesting_depth,
            high_complexity_files=len(code_metrics.high_complexity_files),
            code_quality_score=code_metrics.health_score,

            # Overall
            health_score=health_score,
            test_quality_score=test_metrics.test_quality_score if test_metrics else 0.0,
            is_healthy=health_score >= 0.8,

            # Details
            test_failures=test_failures,
            uncovered_files=uncovered_files
        )

        self._print_summary(enhanced)
        return enhanced

    def _calculate_health_score(
        self,
        build_metrics: HealthMetrics,
        test_metrics: TestMetrics,
        code_metrics: ProjectMetrics
    ) -> float:
        """Calculate comprehensive health score"""
        score = 0.0

        # Build: 30% weight
        if build_metrics.build_status == "pass":
            score += 0.3

        # Tests: 30% weight
        if test_metrics:
            score += test_metrics.overall_pass_rate * 0.2  # Pass rate
            if test_metrics.coverage.coverage_percent >= self.coverage_threshold:
                score += 0.1  # Coverage bonus
        else:
            # No tests run, give partial credit if build passes
            if build_metrics.build_status == "pass":
                score += 0.1

        # Code Quality: 20% weight
        score += code_metrics.health_score * 0.2

        # Analysis: 20% weight
        if build_metrics.analysis_errors == 0:
            score += 0.2

        return round(score, 2)

    def _print_summary(self, metrics: EnhancedHealthMetrics):
        """Print enhanced metrics summary"""
        print("\n" + "=" * 60)
        print(f"📊 Enhanced Health Report")
        print("=" * 60)

        # Build
        build_emoji = "✅" if metrics.build_status == "pass" else "❌"
        print(f"\n{build_emoji} Build: {metrics.build_status}")
        if metrics.build_errors > 0:
            print(f"  Errors: {metrics.build_errors}")
        if metrics.build_warnings > 0:
            print(f"  Warnings: {metrics.build_warnings}")

        # Analysis
        analysis_emoji = "✅" if metrics.analysis_errors == 0 else "❌"
        print(f"\n{analysis_emoji} Analysis:")
        print(f"  Errors: {metrics.analysis_errors}")
        if metrics.analysis_warnings > 0:
            print(f"  Warnings: {metrics.analysis_warnings}")

        # Tests
        test_emoji = "✅" if metrics.test_pass_rate >= 0.95 else "⚠️" if metrics.test_pass_rate > 0 else "❓"
        print(f"\n{test_emoji} Tests:")
        print(f"  Total: {metrics.total_tests}")
        print(f"  Pass rate: {metrics.test_pass_rate:.1%}")
        print(f"  Unit: {metrics.unit_tests}, Integration: {metrics.integration_tests}, "
              f"E2E: {metrics.e2e_tests}, Widget: {metrics.widget_tests}")

        # Coverage
        cov_emoji = "✅" if metrics.coverage_percent >= self.coverage_threshold else "⚠️" if metrics.coverage_percent > 0 else "❓"
        print(f"\n{cov_emoji} Coverage: {metrics.coverage_percent:.1f}%")
        if metrics.uncovered_files:
            print(f"  Low coverage files: {len(metrics.uncovered_files)}")
            for item in metrics.uncovered_files[:3]:
                print(f"    {item['file']}: {item['coverage']:.1f}%")

        # Code Quality
        code_emoji = "✅" if metrics.code_quality_score >= 0.8 else "⚠️"
        print(f"\n{code_emoji} Code Quality: {metrics.code_quality_score:.0%}")
        print(f"  Files: {metrics.total_files}, Avg size: {metrics.avg_file_size} lines")
        if metrics.files_over_threshold > 0:
            print(f"  ⚠️ Files > {self.file_size_threshold} lines: {metrics.files_over_threshold}")
        if metrics.max_nesting_depth > 4:
            print(f"  ⚠️ Max nesting: {metrics.max_nesting_depth} levels")
        if metrics.high_complexity_files > 0:
            print(f"  ⚠️ High complexity: {metrics.high_complexity_files} files")

        # Overall
        health_emoji = "✅" if metrics.is_healthy else "⚠️"
        print(f"\n{health_emoji} Overall Health: {metrics.health_score:.0%}")
        print(f"  Status: {'Healthy' if metrics.is_healthy else 'Needs Attention'}")
        print("=" * 60 + "\n")


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python enhanced_health_monitor.py <project_path> [--tests] [--coverage] [--json]")
        print("\nOptions:")
        print("  --tests      Run tests (adds ~1-2 min)")
        print("  --coverage   Run coverage analysis (adds ~2-3 min)")
        print("  --json       Output as JSON")
        print("  --threshold=N  File size threshold (default: 300)")
        sys.exit(1)

    project_path = sys.argv[1]
    run_tests = "--tests" in sys.argv
    run_coverage = "--coverage" in sys.argv
    output_json = "--json" in sys.argv

    threshold = 300
    for arg in sys.argv:
        if arg.startswith("--threshold="):
            threshold = int(arg.split("=")[1])

    monitor = EnhancedHealthMonitor(
        project_path,
        file_size_threshold=threshold,
        coverage_threshold=80.0
    )

    metrics = monitor.collect_all_metrics(
        run_tests=run_tests,
        run_coverage=run_coverage
    )

    if output_json:
        import json
        print(json.dumps(metrics.to_dict(), indent=2))

    sys.exit(0 if metrics.is_healthy else 1)


if __name__ == "__main__":
    main()
