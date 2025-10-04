"""Python test execution (pytest)."""

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List

from ....domain.models import AnalysisResult


class PythonTestRunner:
    """Runs tests using pytest."""

    def __init__(self, config: Dict):
        self.config = config

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """
        Run pytest with specified strategy.

        Args:
            project_path: Path to project
            strategy: 'minimal' | 'selective' | 'comprehensive'

        Returns:
            AnalysisResult with test results
        """
        start_time = time.time()
        result = AnalysisResult(
            language='python',
            phase='tests',
            project_path=project_path
        )

        try:
            # Build pytest command based on strategy
            cmd = ['pytest']

            if strategy == 'minimal':
                # Only fast tests, no slow or integration
                cmd.extend(['-m', 'not slow and not integration', '--tb=short'])
                timeout = 300  # 5 min
            elif strategy == 'selective':
                # No integration tests
                cmd.extend(['-m', 'not integration'])
                timeout = 900  # 15 min
            else:  # comprehensive
                # Full test suite
                cmd.extend(['-v'])
                timeout = 1800  # 30 min

            test_result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Parse test results
            result.test_failures = self._parse_errors(
                test_result.stdout + test_result.stderr
            )

            # Extract counts
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
        """
        Analyze test coverage using pytest-cov.

        Args:
            project_path: Path to project

        Returns:
            AnalysisResult with coverage data
        """
        start_time = time.time()
        result = AnalysisResult(
            language='python',
            phase='coverage',
            project_path=project_path
        )

        try:
            # Run pytest with coverage
            cmd = ['pytest', '--cov', '--cov-report=json', '--cov-report=term']
            subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                timeout=1800  # 30 min
            )

            # Parse coverage JSON
            coverage_file = Path(project_path) / 'coverage.json'
            if coverage_file.exists():
                coverage_data = self._parse_coverage_json(coverage_file)
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
        """
        Run E2E tests (marked with @pytest.mark.e2e).

        Args:
            project_path: Path to project

        Returns:
            AnalysisResult with E2E test results
        """
        start_time = time.time()
        result = AnalysisResult(
            language='python',
            phase='e2e',
            project_path=project_path
        )

        try:
            # Run only E2E marked tests
            cmd = ['pytest', '-m', 'e2e', '-v']
            test_result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=3600  # 60 min
            )

            # Parse runtime errors
            result.runtime_errors = self._parse_errors(
                test_result.stdout + test_result.stderr
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

    def _parse_errors(self, output: str) -> List[Dict]:
        """Parse pytest error messages."""
        errors = []

        # Pytest format: test_file.py::test_name FAILED
        # Also: E       AssertionError: message
        pattern = r'(.+\.py)::(.+?)\s+FAILED'
        for match in re.finditer(pattern, output):
            errors.append({
                'severity': 'error',
                'file': match.group(1),
                'line': 0,
                'column': 0,
                'message': f'Test failed: {match.group(2)}',
                'code': 'test_failure'
            })

        # Extract assertion errors
        pattern = r'E\s+(.+Error:.+)'
        for match in re.finditer(pattern, output):
            if errors:  # Add to last error
                errors[-1]['message'] += f' - {match.group(1)}'

        return errors

    def _extract_test_counts(self, output: str) -> Dict[str, int]:
        """Extract pytest pass/fail counts."""
        passed = 0
        failed = 0

        # Look for summary: "5 passed, 2 failed in 1.23s"
        if match := re.search(r'(\d+) passed', output):
            passed = int(match.group(1))
        if match := re.search(r'(\d+) failed', output):
            failed = int(match.group(1))

        return {'passed': passed, 'failed': failed}

    def _parse_coverage_json(self, coverage_file: Path) -> Dict:
        """Parse coverage.json file."""
        try:
            with open(coverage_file) as f:
                data = json.load(f)

            # Get overall coverage percentage
            totals = data.get('totals', {})
            percentage = totals.get('percent_covered', 0)

            # Find files with low/no coverage
            gaps = []
            files = data.get('files', {})
            for file_path, file_data in files.items():
                file_coverage = file_data.get('summary', {}).get('percent_covered', 0)
                if file_coverage < 50:  # Less than 50% coverage
                    gaps.append({
                        'file': file_path,
                        'coverage': file_coverage,
                        'message': f'Low coverage: {file_coverage:.1f}%'
                    })

            return {
                'percentage': percentage,
                'gaps': gaps
            }

        except Exception:
            return {'percentage': 0, 'gaps': []}
