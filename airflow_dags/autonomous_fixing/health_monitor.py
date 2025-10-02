#!/usr/bin/env python3
"""
Health monitoring system for Flutter projects.
Collects metrics on build status, test results, and code quality.
"""

import subprocess
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class HealthMetrics:
    """Health metrics for a Flutter project"""
    timestamp: str
    project_path: str

    # Build metrics
    build_status: str  # 'pass' | 'fail' | 'unknown'
    build_errors: List[str]
    build_warnings: List[str]

    # Test metrics
    test_status: str  # 'pass' | 'fail' | 'unknown'
    test_total: int
    test_passed: int
    test_failed: int
    test_failures: List[str]

    # Analysis metrics
    analysis_status: str  # 'pass' | 'fail' | 'unknown'
    analysis_errors: int
    analysis_warnings: int
    analysis_infos: int
    analysis_issues: List[Dict[str, str]]

    # Overall health
    health_score: float  # 0.0 - 1.0
    is_healthy: bool

    def to_dict(self) -> dict:
        return asdict(self)


class FlutterHealthMonitor:
    """Monitor health of Flutter projects"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.flutter_bin = self._find_flutter()

    def _find_flutter(self) -> str:
        """Find Flutter binary"""
        # Try common locations
        locations = [
            os.path.expanduser("~/flutter/bin/flutter"),
            "/usr/local/bin/flutter",
            "flutter"  # In PATH
        ]

        for location in locations:
            result = subprocess.run(
                [location, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return location

        raise RuntimeError("Flutter not found. Please install Flutter.")

    def collect_metrics(self) -> HealthMetrics:
        """Collect all health metrics"""
        print(f"🔍 Collecting health metrics for {self.project_path.name}...")

        # Collect all metrics
        build_status, build_errors, build_warnings = self._check_build()
        test_status, test_total, test_passed, test_failed, test_failures = self._run_tests()
        analysis_status, analysis_errors, analysis_warnings, analysis_infos, analysis_issues = self._run_analysis()

        # Calculate health score
        health_score = self._calculate_health_score(
            build_status, test_passed, test_total, analysis_errors
        )

        metrics = HealthMetrics(
            timestamp=datetime.now().isoformat(),
            project_path=str(self.project_path),
            build_status=build_status,
            build_errors=build_errors,
            build_warnings=build_warnings,
            test_status=test_status,
            test_total=test_total,
            test_passed=test_passed,
            test_failed=test_failed,
            test_failures=test_failures,
            analysis_status=analysis_status,
            analysis_errors=analysis_errors,
            analysis_warnings=analysis_warnings,
            analysis_infos=analysis_infos,
            analysis_issues=analysis_issues,
            health_score=health_score,
            is_healthy=health_score >= 0.8
        )

        self._print_summary(metrics)
        return metrics

    def _check_build(self) -> tuple:
        """Check build status"""
        print("  📦 Checking build...")

        try:
            # Run flutter analyze first (faster than full build)
            result = subprocess.run(
                [self.flutter_bin, "analyze", "--no-pub"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            if "No issues found!" in result.stdout:
                return "pass", [], []

            # Parse errors and warnings
            errors = self._parse_build_output(result.stdout, "error")
            warnings = self._parse_build_output(result.stdout, "warning")

            status = "fail" if errors else "pass"
            return status, errors, warnings

        except subprocess.TimeoutExpired:
            return "unknown", ["Build timeout"], []
        except Exception as e:
            return "unknown", [f"Build check failed: {str(e)}"], []

    def _run_tests(self) -> tuple:
        """Run tests and collect results"""
        print("  🧪 Running tests...")

        try:
            result = subprocess.run(
                [self.flutter_bin, "test", "--no-pub", "--reporter=json"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse JSON test results
            total = 0
            passed = 0
            failed = 0
            failures = []

            for line in result.stdout.splitlines():
                try:
                    event = json.loads(line)
                    if event.get('type') == 'testDone':
                        total += 1
                        if event.get('result') == 'success':
                            passed += 1
                        else:
                            failed += 1
                            test_name = event.get('test', {}).get('name', 'Unknown')
                            failures.append(test_name)
                except json.JSONDecodeError:
                    continue

            status = "pass" if failed == 0 and total > 0 else "fail" if failed > 0 else "unknown"
            return status, total, passed, failed, failures

        except subprocess.TimeoutExpired:
            return "unknown", 0, 0, 0, ["Test timeout"]
        except Exception as e:
            return "unknown", 0, 0, 0, [f"Test execution failed: {str(e)}"]

    def _run_analysis(self) -> tuple:
        """Run static analysis"""
        print("  🔎 Running analysis...")

        try:
            result = subprocess.run(
                [self.flutter_bin, "analyze", "--no-pub"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parse analysis output
            errors = 0
            warnings = 0
            infos = 0
            issues = []

            for line in result.stdout.splitlines():
                if " error •" in line:
                    errors += 1
                    issues.append(self._parse_issue(line, "error"))
                elif " warning •" in line:
                    warnings += 1
                    issues.append(self._parse_issue(line, "warning"))
                elif " info •" in line:
                    infos += 1
                    issues.append(self._parse_issue(line, "info"))

            status = "pass" if errors == 0 else "fail"
            return status, errors, warnings, infos, issues

        except subprocess.TimeoutExpired:
            return "unknown", 0, 0, 0, [{"message": "Analysis timeout"}]
        except Exception as e:
            return "unknown", 0, 0, 0, [{"message": f"Analysis failed: {str(e)}"}]

    def _parse_build_output(self, output: str, level: str) -> List[str]:
        """Parse build output for errors/warnings"""
        issues = []
        for line in output.splitlines():
            if f" {level} •" in line:
                issues.append(line.strip())
        return issues

    def _parse_issue(self, line: str, severity: str) -> Dict[str, str]:
        """Parse a single issue line"""
        parts = line.split("•")
        if len(parts) >= 2:
            message = parts[1].strip().split(" at ")[0]
            location = parts[0].strip()
            return {
                "severity": severity,
                "message": message,
                "location": location
            }
        return {"severity": severity, "message": line.strip()}

    def _calculate_health_score(
        self,
        build_status: str,
        test_passed: int,
        test_total: int,
        analysis_errors: int
    ) -> float:
        """Calculate overall health score (0.0 - 1.0)"""
        score = 0.0

        # Build: 40% weight
        if build_status == "pass":
            score += 0.4

        # Tests: 40% weight
        if test_total > 0:
            test_pass_rate = test_passed / test_total
            score += 0.4 * test_pass_rate
        else:
            score += 0.2  # Partial credit if no tests

        # Analysis: 20% weight
        if analysis_errors == 0:
            score += 0.2

        return round(score, 2)

    def _print_summary(self, metrics: HealthMetrics):
        """Print health metrics summary"""
        print("\n" + "="*60)
        print(f"📊 Health Report: {Path(metrics.project_path).name}")
        print("="*60)

        # Build
        build_emoji = "✅" if metrics.build_status == "pass" else "❌" if metrics.build_status == "fail" else "❓"
        print(f"\n{build_emoji} Build: {metrics.build_status}")
        if metrics.build_errors:
            print(f"  Errors: {len(metrics.build_errors)}")
        if metrics.build_warnings:
            print(f"  Warnings: {len(metrics.build_warnings)}")

        # Tests
        test_emoji = "✅" if metrics.test_status == "pass" else "❌" if metrics.test_status == "fail" else "❓"
        print(f"\n{test_emoji} Tests: {metrics.test_status}")
        if metrics.test_total > 0:
            print(f"  Passed: {metrics.test_passed}/{metrics.test_total}")
            if metrics.test_failed > 0:
                print(f"  Failed: {metrics.test_failed}")

        # Analysis
        analysis_emoji = "✅" if metrics.analysis_status == "pass" else "❌" if metrics.analysis_status == "fail" else "❓"
        print(f"\n{analysis_emoji} Analysis: {metrics.analysis_status}")
        if metrics.analysis_errors > 0:
            print(f"  Errors: {metrics.analysis_errors}")
        if metrics.analysis_warnings > 0:
            print(f"  Warnings: {metrics.analysis_warnings}")

        # Overall
        health_emoji = "✅" if metrics.is_healthy else "⚠️"
        print(f"\n{health_emoji} Health Score: {metrics.health_score:.0%}")
        print(f"  Status: {'Healthy' if metrics.is_healthy else 'Needs Attention'}")
        print("="*60 + "\n")


def main():
    """CLI entry point"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python health_monitor.py <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]

    if not os.path.exists(project_path):
        print(f"❌ Project not found: {project_path}")
        sys.exit(1)

    monitor = FlutterHealthMonitor(project_path)
    metrics = monitor.collect_metrics()

    # Output JSON for programmatic use
    if "--json" in sys.argv:
        print(json.dumps(metrics.to_dict(), indent=2))

    # Exit with appropriate code
    sys.exit(0 if metrics.is_healthy else 1)


if __name__ == "__main__":
    main()
