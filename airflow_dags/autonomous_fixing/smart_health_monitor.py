#!/usr/bin/env python3
"""
Smart health monitoring with tiered checks.
Static checks (fast) → Dynamic checks (slow) only if static passes.
"""

import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from code_metrics import LightweightCodeMetrics
from domain.enums import AnalysisStatus


@dataclass
class StaticHealthMetrics:
    """Fast static analysis (no execution)"""

    timestamp: str
    project_path: str

    # Analysis (flutter analyze - fast)
    analysis_errors: int
    analysis_warnings: int
    analysis_status: str  # 'pass' | 'fail'

    # Code quality (no execution)
    total_files: int
    avg_file_size: int
    files_over_threshold: int
    max_nesting_depth: int
    high_complexity_files: int
    code_quality_score: float

    # Static score
    static_health_score: float
    passes_static: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DynamicHealthMetrics:
    """Slow dynamic checks (execution required)"""

    # Tests (flutter test - slow)
    total_tests: int
    test_pass_rate: float
    unit_tests: int
    integration_tests: int
    e2e_tests: int

    # Coverage (flutter test --coverage - very slow)
    coverage_percent: float

    # Dynamic score
    dynamic_health_score: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SmartHealthMetrics:
    """Combined metrics with execution info"""

    static: StaticHealthMetrics
    dynamic: DynamicHealthMetrics | None

    overall_health_score: float
    is_healthy: bool
    check_mode: str  # 'static_only' | 'full'

    def to_dict(self) -> dict:
        return {
            "static": self.static.to_dict(),
            "dynamic": self.dynamic.to_dict() if self.dynamic else None,
            "overall_health_score": self.overall_health_score,
            "is_healthy": self.is_healthy,
            "check_mode": self.check_mode,
        }


class SmartHealthMonitor:
    """Smart tiered health monitoring"""

    def __init__(
        self,
        project_path: str,
        flutter_bin: str = None,
        file_size_threshold: int = 300,
        static_pass_threshold: float = 0.6,
    ):
        self.project_path = Path(project_path)
        self.flutter_bin = flutter_bin or self._find_flutter()
        self.file_size_threshold = file_size_threshold
        self.static_pass_threshold = static_pass_threshold

    def _find_flutter(self) -> str:
        """Find Flutter binary"""
        import os
        import shutil

        flutter = shutil.which("flutter")
        if flutter:
            return flutter

        locations = [os.path.expanduser("~/flutter/bin/flutter"), "/usr/local/bin/flutter"]

        for location in locations:
            if os.path.exists(location):
                return location

        return "flutter"

    def check_health(self, force_dynamic: bool = False) -> SmartHealthMetrics:
        """
        Smart health check with tiered approach.

        1. Run static checks (fast ~10s)
        2. If static passes OR force_dynamic, run dynamic checks (slow ~2-5min)
        3. Return combined results
        """
        print(f"🔍 Smart Health Check: {self.project_path.name}")
        print("=" * 60)

        # Step 1: Static checks (always run - fast)
        print("\n⚡ Static Analysis (fast)...")
        static = self._run_static_checks()

        # Step 2: Decide if dynamic checks needed
        run_dynamic = force_dynamic or static.passes_static

        dynamic = None
        if run_dynamic:
            if not force_dynamic:
                print(
                    f"\n✅ Static passed ({static.static_health_score:.0%}) → Running dynamic checks..."
                )
            else:
                print("\n🔨 Force dynamic mode...")
            print("🧪 Dynamic Analysis (slow ~2-5min)...")
            dynamic = self._run_dynamic_checks()
        else:
            print(
                f"\n❌ Static failed ({static.static_health_score:.0%}) → Skipping dynamic checks"
            )
            print("   (Fix static issues first to save time)")

        # Step 3: Calculate overall score
        overall = self._calculate_overall_score(static, dynamic)

        result = SmartHealthMetrics(
            static=static,
            dynamic=dynamic,
            overall_health_score=overall,
            is_healthy=overall >= 0.8,
            check_mode="full" if dynamic else "static_only",
        )

        self._print_summary(result)
        return result

    def _run_flutter_analyze(self) -> tuple[int, int, str]:
        """Run flutter analyze and return (errors, warnings, status)"""
        import subprocess

        analysis_errors = 0
        analysis_warnings = 0
        analysis_status = "unknown"

        try:
            result = subprocess.run(
                [self.flutter_bin, "analyze", "--no-pub"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            for line in result.stdout.splitlines():
                if " error •" in line:
                    analysis_errors += 1
                elif " warning •" in line:
                    analysis_warnings += 1

            analysis_status = (
                str(AnalysisStatus.PASS) if analysis_errors == 0 else str(AnalysisStatus.FAIL)
            )

        except Exception as e:
            print(f"  ⚠️ Analysis failed: {e}")

        return analysis_errors, analysis_warnings, analysis_status

    def _run_static_checks(self) -> StaticHealthMetrics:
        """Run fast static checks (no execution)"""
        # 1. Flutter analyze (fast ~5s)
        analysis_errors, analysis_warnings, analysis_status = self._run_flutter_analyze()

        # 2. Code quality (fast ~5s)
        code_analyzer = LightweightCodeMetrics(str(self.project_path), self.file_size_threshold)
        code_metrics = code_analyzer.analyze_project()

        # 3. Calculate static score
        static_score = self._calculate_static_score(
            analysis_status, analysis_errors, code_metrics.health_score
        )

        return StaticHealthMetrics(
            timestamp=datetime.now().isoformat(),
            project_path=str(self.project_path),
            analysis_errors=analysis_errors,
            analysis_warnings=analysis_warnings,
            analysis_status=analysis_status,
            total_files=code_metrics.total_files,
            avg_file_size=code_metrics.avg_file_size,
            files_over_threshold=len(code_metrics.files_over_threshold),
            max_nesting_depth=code_metrics.max_nesting_depth,
            high_complexity_files=len(code_metrics.high_complexity_files),
            code_quality_score=code_metrics.health_score,
            static_health_score=static_score,
            passes_static=static_score >= self.static_pass_threshold,
        )

    def _run_dynamic_checks(self) -> DynamicHealthMetrics:
        """Run slow dynamic checks (execution required)"""
        from test_metrics import FlutterTestAnalyzer

        # Run tests
        analyzer = FlutterTestAnalyzer(str(self.project_path))
        test_metrics = analyzer.analyze(run_coverage=False, timeout=180)

        # Calculate dynamic score
        dynamic_score = self._calculate_dynamic_score(
            test_metrics.overall_pass_rate, test_metrics.coverage.coverage_percent
        )

        return DynamicHealthMetrics(
            total_tests=test_metrics.total_tests,
            test_pass_rate=test_metrics.overall_pass_rate,
            unit_tests=test_metrics.unit_tests.total,
            integration_tests=test_metrics.integration_tests.total,
            e2e_tests=test_metrics.e2e_tests.total,
            coverage_percent=test_metrics.coverage.coverage_percent,
            dynamic_health_score=dynamic_score,
        )

    def _calculate_static_score(
        self, analysis_status: str, analysis_errors: int, code_quality: float
    ) -> float:
        """Calculate static health score"""
        score = 0.0

        # Analysis: 60% weight
        if analysis_status == str(AnalysisStatus.PASS):
            score += 0.6
        elif analysis_errors < 100:  # Partial credit for few errors
            score += 0.3

        # Code quality: 40% weight
        score += code_quality * 0.4

        return round(score, 2)

    def _calculate_dynamic_score(self, test_pass_rate: float, coverage: float) -> float:
        """Calculate dynamic health score"""
        score = 0.0

        # Test pass rate: 70% weight
        score += test_pass_rate * 0.7

        # Coverage: 30% weight
        score += (coverage / 100) * 0.3

        return round(score, 2)

    def _calculate_overall_score(
        self, static: StaticHealthMetrics, dynamic: DynamicHealthMetrics | None
    ) -> float:
        """Calculate overall health score"""
        if not dynamic:
            # Static only
            return static.static_health_score * 0.7  # Penalize for no dynamic

        # Weighted average: static 40%, dynamic 60%
        overall = static.static_health_score * 0.4 + dynamic.dynamic_health_score * 0.6

        return round(overall, 2)

    def _print_static_analysis(self, static: StaticHealthMetrics):
        """Print static analysis results"""
        print(f"\n⚡ Static Analysis ({static.static_health_score:.0%}):")

        analysis_emoji = "✅" if static.analysis_status == str(AnalysisStatus.PASS) else "❌"
        print(f"  {analysis_emoji} Analysis: {static.analysis_status}")
        if static.analysis_errors > 0:
            print(f"     Errors: {static.analysis_errors}")
        if static.analysis_warnings > 0:
            print(f"     Warnings: {static.analysis_warnings}")

        code_emoji = "✅" if static.code_quality_score >= 0.8 else "⚠️"
        print(f"  {code_emoji} Code Quality: {static.code_quality_score:.0%}")
        print(f"     Files: {static.total_files}, Avg: {static.avg_file_size} lines")
        if static.files_over_threshold > 0:
            print(f"     ⚠️ {static.files_over_threshold} files > {self.file_size_threshold} lines")
        if static.max_nesting_depth > 4:
            print(f"     ⚠️ Max nesting: {static.max_nesting_depth} levels")

    def _print_dynamic_analysis(self, dynamic: DynamicHealthMetrics):
        """Print dynamic analysis results"""
        print(f"\n🧪 Dynamic Analysis ({dynamic.dynamic_health_score:.0%}):")

        test_emoji = "✅" if dynamic.test_pass_rate >= 0.95 else "⚠️"
        print(f"  {test_emoji} Tests: {dynamic.test_pass_rate:.1%} pass rate")
        print(f"     Total: {dynamic.total_tests}")
        print(
            f"     Unit: {dynamic.unit_tests}, Integration: {dynamic.integration_tests}, E2E: {dynamic.e2e_tests}"
        )

        if dynamic.coverage_percent > 0:
            cov_emoji = "✅" if dynamic.coverage_percent >= 80 else "⚠️"
            print(f"  {cov_emoji} Coverage: {dynamic.coverage_percent:.1f}%")

    def _print_overall_health(self, metrics: SmartHealthMetrics):
        """Print overall health status"""
        health_emoji = "✅" if metrics.is_healthy else "⚠️"
        print(f"\n{health_emoji} Overall Health: {metrics.overall_health_score:.0%}")
        print(f"   Mode: {metrics.check_mode}")
        print(f"   Status: {'Healthy' if metrics.is_healthy else 'Needs Attention'}")
        print("=" * 60 + "\n")

    def _print_summary(self, metrics: SmartHealthMetrics):
        """Print smart health summary"""
        print("\n" + "=" * 60)
        print("📊 Smart Health Summary")
        print("=" * 60)

        static = metrics.static
        self._print_static_analysis(static)

        if metrics.dynamic:
            self._print_dynamic_analysis(metrics.dynamic)
        else:
            print(
                f"\n⏭️ Dynamic checks skipped (static score: {static.static_health_score:.0%} < {self.static_pass_threshold:.0%})"
            )

        self._print_overall_health(metrics)


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python smart_health_monitor.py <project_path> [--force-dynamic] [--json]")
        print("\nModes:")
        print("  Default: Run static → dynamic only if static passes")
        print("  --force-dynamic: Always run both static and dynamic")
        print("\nOptions:")
        print("  --threshold=N: File size threshold (default: 300)")
        print("  --json: Output as JSON")
        sys.exit(1)

    project_path = sys.argv[1]
    force_dynamic = "--force-dynamic" in sys.argv
    output_json = "--json" in sys.argv

    threshold = 300
    for arg in sys.argv:
        if arg.startswith("--threshold="):
            threshold = int(arg.split("=")[1])

    monitor = SmartHealthMonitor(project_path, file_size_threshold=threshold)
    metrics = monitor.check_health(force_dynamic=force_dynamic)

    if output_json:
        import json

        print(json.dumps(metrics.to_dict(), indent=2))

    sys.exit(0 if metrics.is_healthy else 1)


if __name__ == "__main__":
    main()
