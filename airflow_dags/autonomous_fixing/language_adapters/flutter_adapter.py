"""Flutter language adapter."""

import subprocess
import json
import re
import time
from pathlib import Path
from typing import List, Dict
from .base import LanguageAdapter, AnalysisResult


class FlutterAdapter(LanguageAdapter):
    """Adapter for Flutter/Dart projects."""

    @property
    def language_name(self) -> str:
        return "flutter"

    @property
    def project_markers(self) -> List[str]:
        return ["pubspec.yaml"]

    def detect_projects(self, root_path: str) -> List[str]:
        """Find all Flutter projects by looking for pubspec.yaml."""
        projects = []
        root = Path(root_path)

        for pubspec in root.rglob("pubspec.yaml"):
            # Verify it's a Flutter project (has flutter dependency)
            try:
                with open(pubspec) as f:
                    content = f.read()
                    if 'flutter:' in content or 'flutter_test:' in content:
                        projects.append(str(pubspec.parent))
            except Exception:
                continue

        return projects

    def static_analysis(self, project_path: str) -> AnalysisResult:
        """Run flutter analyze + complexity checks."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='static',
            project_path=project_path
        )

        try:
            # Run flutter analyze
            analyze_cmd = ['flutter', 'analyze', '--no-pub']
            if args := self.config.get('analyzer_args'):
                analyze_cmd.extend(args.split())

            analyze_result = subprocess.run(
                analyze_cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parse errors
            result.errors = self.parse_errors(
                analyze_result.stdout + analyze_result.stderr,
                'static'
            )

            # Check file sizes
            result.file_size_violations = self.check_file_sizes(project_path)

            # Check complexity
            result.complexity_violations = self._check_complexity(project_path)

            result.success = len(result.errors) == 0
            result.execution_time = time.time() - start_time

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = "Static analysis timed out after 120 seconds"
        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """Run Flutter tests based on strategy."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='tests',
            project_path=project_path
        )

        try:
            # Build test command based on strategy
            if strategy == 'minimal':
                # Only unit tests
                cmd = ['flutter', 'test', 'test/unit/', '--no-pub']
                timeout = 300  # 5 min
            elif strategy == 'selective':
                # Unit + widget tests, no integration
                cmd = ['flutter', 'test', '--exclude-tags=integration', '--no-pub']
                timeout = 900  # 15 min
            else:  # comprehensive
                # Full test suite
                cmd = ['flutter', 'test', '--no-pub']
                timeout = 1800  # 30 min

            test_result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Parse test results
            result.test_failures = self.parse_errors(
                test_result.stdout + test_result.stderr,
                'tests'
            )

            # Extract pass/fail counts
            counts = self._extract_test_counts(test_result.stdout)
            result.tests_passed = counts['passed']
            result.tests_failed = counts['failed']

            result.success = test_result.returncode == 0
            result.execution_time = time.time() - start_time

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = f"Tests timed out after {timeout} seconds"
        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def analyze_coverage(self, project_path: str) -> AnalysisResult:
        """Analyze test coverage and find gaps."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='coverage',
            project_path=project_path
        )

        try:
            # Run tests with coverage
            cmd = ['flutter', 'test', '--coverage', '--no-pub']
            subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                timeout=1800  # 30 min
            )

            # Parse coverage file
            coverage_file = Path(project_path) / 'coverage' / 'lcov.info'
            if coverage_file.exists():
                coverage_data = self._parse_lcov(coverage_file)
                result.coverage_percentage = coverage_data['percentage']
                result.coverage_gaps = coverage_data['gaps']

            result.success = True
            result.execution_time = time.time() - start_time

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = "Coverage analysis timed out"
        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def run_e2e_tests(self, project_path: str) -> AnalysisResult:
        """Run Flutter integration tests."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='e2e',
            project_path=project_path
        )

        try:
            # Check for integration tests
            integration_dir = Path(project_path) / 'integration_test'
            if not integration_dir.exists():
                result.success = True
                result.error_message = "No integration tests found"
                return result

            # Run integration tests
            cmd = ['flutter', 'test', 'integration_test/', '--no-pub']
            test_result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=3600  # 60 min
            )

            # Parse runtime errors
            result.runtime_errors = self.parse_errors(
                test_result.stdout + test_result.stderr,
                'e2e'
            )

            result.success = test_result.returncode == 0
            result.execution_time = time.time() - start_time

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = "E2E tests timed out"
        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def parse_errors(self, output: str, phase: str) -> List[Dict]:
        """Parse Flutter/Dart error messages."""
        errors = []

        if phase == 'static':
            # Flutter analyze format:
            # error • message • file:line:col • error_code
            pattern = r'(error|warning|info)\s*•\s*(.+?)\s*•\s*(.+?):(\d+):(\d+)\s*•\s*(\w+)?'
            for match in re.finditer(pattern, output):
                errors.append({
                    'severity': match.group(1),
                    'message': match.group(2).strip(),
                    'file': match.group(3).strip(),
                    'line': int(match.group(4)),
                    'column': int(match.group(5)),
                    'code': match.group(6) or ''
                })

        elif phase == 'tests':
            # Flutter test error format
            # Test failed. See exception logs above.
            # or: Expected: <value>, Actual: <value>
            pattern = r'(.+?):(\d+):\d+\s+(.+)'
            for match in re.finditer(pattern, output):
                if 'FAILED' in match.group(0) or 'Expected:' in match.group(0):
                    errors.append({
                        'severity': 'error',
                        'file': match.group(1).strip(),
                        'line': int(match.group(2)),
                        'column': 0,
                        'message': match.group(3).strip(),
                        'code': 'test_failure'
                    })

        elif phase == 'e2e':
            # Integration test errors - similar to unit test format
            errors = self.parse_errors(output, 'tests')

        return errors

    def calculate_complexity(self, file_path: str) -> int:
        """Calculate cyclomatic complexity using simple heuristic."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Count decision points: if, for, while, case, catch, &&, ||, ??
            complexity = 1  # Base complexity
            complexity += content.count(' if ')
            complexity += content.count(' for ')
            complexity += content.count(' while ')
            complexity += content.count(' case ')
            complexity += content.count(' catch ')
            complexity += content.count(' && ')
            complexity += content.count(' || ')
            complexity += content.count(' ?? ')

            return complexity

        except Exception:
            return 0

    def _get_source_files(self, project_path: Path) -> List[Path]:
        """Get all Dart source files."""
        lib_dir = project_path / 'lib'
        if not lib_dir.exists():
            return []
        return list(lib_dir.rglob('*.dart'))

    def _check_complexity(self, project_path: str) -> List[Dict]:
        """Check for files with high complexity."""
        violations = []
        project = Path(project_path)

        for file_path in self._get_source_files(project):
            complexity = self.calculate_complexity(str(file_path))
            if complexity > self.complexity_threshold:
                violations.append({
                    'file': str(file_path),
                    'complexity': complexity,
                    'threshold': self.complexity_threshold,
                    'message': f'Complexity {complexity} exceeds threshold {self.complexity_threshold}'
                })

        return violations

    def _extract_test_counts(self, output: str) -> Dict[str, int]:
        """Extract test pass/fail counts from output."""
        # Flutter test output: "All tests passed!" or "Some tests failed."
        # Also: "+5 passed, -2 failed"
        passed = 0
        failed = 0

        # Look for summary line
        if match := re.search(r'\+(\d+)', output):
            passed = int(match.group(1))
        if match := re.search(r'-(\d+)', output):
            failed = int(match.group(1))

        # Fallback: count individual test results
        if passed == 0 and failed == 0:
            passed = output.count('✓')
            failed = output.count('✗')

        return {'passed': passed, 'failed': failed}

    def _parse_lcov(self, coverage_file: Path) -> Dict:
        """Parse lcov.info coverage file."""
        try:
            with open(coverage_file) as f:
                content = f.read()

            # Count lines found (LF) and lines hit (LH)
            lines_found = sum(int(m.group(1)) for m in re.finditer(r'LF:(\d+)', content))
            lines_hit = sum(int(m.group(1)) for m in re.finditer(r'LH:(\d+)', content))

            percentage = (lines_hit / lines_found * 100) if lines_found > 0 else 0

            # Find uncovered files (LH:0)
            gaps = []
            current_file = None
            for line in content.split('\n'):
                if line.startswith('SF:'):
                    current_file = line[3:]
                elif line.startswith('LH:0') and current_file:
                    gaps.append({
                        'file': current_file,
                        'coverage': 0,
                        'message': 'File has no test coverage'
                    })

            return {
                'percentage': percentage,
                'gaps': gaps
            }

        except Exception as e:
            return {'percentage': 0, 'gaps': []}
