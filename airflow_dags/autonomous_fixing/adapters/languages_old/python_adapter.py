"""Python language adapter."""

import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List

from .base import AnalysisResult, LanguageAdapter, ToolValidationResult


class PythonAdapter(LanguageAdapter):
    """Adapter for Python projects."""

    @property
    def language_name(self) -> str:
        return "python"

    @property
    def project_markers(self) -> List[str]:
        return ["setup.py", "pyproject.toml", "requirements.txt", "setup.cfg"]

    def detect_projects(self, root_path: str) -> List[str]:
        """Find all Python projects."""
        projects = []
        root = Path(root_path)

        # Look for project markers
        for marker in self.project_markers:
            for file_path in root.rglob(marker):
                project_dir = file_path.parent
                if str(project_dir) not in projects:
                    projects.append(str(project_dir))

        return projects

    def static_analysis(self, project_path: str) -> AnalysisResult:
        """Run pylint + mypy in parallel."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='static',
            project_path=project_path
        )

        try:
            errors = []

            # Run linters in parallel
            linters = self.config.get('linters', ['pylint', 'mypy'])

            if 'pylint' in linters:
                errors.extend(self._run_pylint(project_path))

            if 'mypy' in linters:
                errors.extend(self._run_mypy(project_path))

            result.errors = errors
            result.file_size_violations = self.check_file_sizes(project_path)
            result.complexity_violations = self._check_complexity(project_path)

            # Quality check delegated to AnalysisResult model (SOLID: Single Responsibility)
            result.success = result.compute_quality_check()
            result.execution_time = time.time() - start_time

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """Run pytest with strategy."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
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
            result.test_failures = self.parse_errors(
                test_result.stdout + test_result.stderr,
                'tests'
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
        """Analyze test coverage using pytest-cov."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
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
        """Run E2E tests (marked with @pytest.mark.e2e)."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
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
        """Parse Python error messages."""
        errors = []

        if phase == 'static':
            # Already parsed by _run_pylint and _run_mypy
            return []

        elif phase in ('tests', 'e2e'):
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

    def calculate_complexity(self, file_path: str) -> int:
        """Calculate cyclomatic complexity using radon."""
        try:
            # Use radon for accurate complexity
            result = subprocess.run(
                ['radon', 'cc', file_path, '-s', '-n', 'A'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Parse radon output: "A 1:0 ClassName.method_name - A (1)"
            max_complexity = 0
            for match in re.finditer(r'\((\d+)\)', result.stdout):
                complexity = int(match.group(1))
                max_complexity = max(max_complexity, complexity)

            return max_complexity

        except Exception:
            # Fallback to simple heuristic
            return self._simple_complexity(file_path)

    def _simple_complexity(self, file_path: str) -> int:
        """Simple complexity heuristic (fallback)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            complexity = 1
            complexity += content.count(' if ')
            complexity += content.count(' for ')
            complexity += content.count(' while ')
            complexity += content.count(' and ')
            complexity += content.count(' or ')
            complexity += content.count('except ')

            return complexity

        except Exception:
            return 0

    def _get_source_files(self, project_path: Path) -> List[Path]:
        """Get all Python source files."""
        source_files = []
        for pattern in ['**/*.py']:
            source_files.extend(project_path.rglob(pattern))

        # Exclude common non-source directories
        excluded = {'venv', '.venv', 'env', '__pycache__', '.tox', 'build', 'dist'}
        return [f for f in source_files if not any(e in f.parts for e in excluded)]

    def _run_pylint(self, project_path: str) -> List[Dict]:
        """Run pylint and parse errors."""
        try:
            result = subprocess.run(
                ['pylint', '.', '--output-format=json'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parse JSON output
            if result.stdout:
                lint_results = json.loads(result.stdout)
                return [
                    {
                        'severity': item.get('type', 'error'),
                        'file': item.get('path', ''),
                        'line': item.get('line', 0),
                        'column': item.get('column', 0),
                        'message': item.get('message', ''),
                        'code': item.get('symbol', '')
                    }
                    for item in lint_results
                    if item.get('type') in ('error', 'fatal')
                ]

        except Exception:
            pass

        return []

    def _run_mypy(self, project_path: str) -> List[Dict]:
        """Run mypy and parse errors."""
        try:
            result = subprocess.run(
                ['mypy', '.', '--show-error-codes'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            errors = []
            # Mypy format: file.py:line: error: message [error-code]
            pattern = r'(.+\.py):(\d+):\s*(error|warning):\s*(.+?)\s*\[(.+?)\]'
            for match in re.finditer(pattern, result.stdout):
                errors.append({
                    'severity': match.group(3),
                    'file': match.group(1),
                    'line': int(match.group(2)),
                    'column': 0,
                    'message': match.group(4),
                    'code': match.group(5)
                })

            return errors

        except Exception:
            pass

        return []

    def _check_complexity(self, project_path: str) -> List[Dict]:
        """Check for high complexity files."""
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

    def validate_tools(self) -> List[ToolValidationResult]:
        """Validate Python toolchain availability."""
        results = []

        # 1. Python itself
        results.append(self._validate_python())

        # 2. Linters (from config)
        linters = self.config.get('linters', ['pylint', 'mypy'])
        for linter in linters:
            results.append(self._validate_tool(
                linter,
                version_flag='--version',
                fix_suggestion=f'Install {linter}: pip install {linter}'
            ))

        # 3. Test runner
        test_runner = self.config.get('test_runner', 'pytest')
        results.append(self._validate_tool(
            test_runner,
            version_flag='--version',
            fix_suggestion=f'Install {test_runner}: pip install {test_runner}'
        ))

        # 4. Coverage tool (optional)
        results.append(self._validate_tool(
            'coverage',
            version_flag='--version',
            fix_suggestion='Install coverage: pip install coverage',
            optional=True
        ))

        return results

    def _validate_python(self) -> ToolValidationResult:
        """Validate Python installation."""
        python_cmd = shutil.which('python') or shutil.which('python3')

        if not python_cmd:
            return ToolValidationResult(
                tool_name='python',
                available=False,
                error_message='Python not found in PATH',
                fix_suggestion='Install Python: https://python.org/downloads'
            )

        try:
            result = subprocess.run(
                [python_cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            version_match = re.search(r'Python ([\d.]+)', result.stdout + result.stderr)
            version = version_match.group(1) if version_match else 'unknown'

            return ToolValidationResult(
                tool_name='python',
                available=True,
                version=version,
                path=python_cmd
            )
        except Exception as e:
            return ToolValidationResult(
                tool_name='python',
                available=False,
                path=python_cmd,
                error_message=f'Python found but failed to run: {e}'
            )

    def _validate_tool(self, tool_name: str, version_flag: str, fix_suggestion: str, optional: bool = False) -> ToolValidationResult:
        """Generic tool validation."""
        # First check PATH
        tool_cmd = shutil.which(tool_name)

        # If not in PATH, check if running in venv and look there
        if not tool_cmd:
            import sys
            if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
                # We're in a venv, check venv bin directory
                venv_bin = Path(sys.prefix) / 'bin' / tool_name
                if venv_bin.exists():
                    tool_cmd = str(venv_bin)

        if not tool_cmd:
            return ToolValidationResult(
                tool_name=tool_name,
                available=False,
                error_message=f'{tool_name} not found in PATH' if not optional else f'{tool_name} not found (optional)',
                fix_suggestion=fix_suggestion if not optional else None
            )

        try:
            result = subprocess.run(
                [tool_cmd, version_flag],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Try to extract version from output
            output = result.stdout + result.stderr
            version_match = re.search(r'([\d.]+)', output)
            version = version_match.group(1) if version_match else 'unknown'

            return ToolValidationResult(
                tool_name=tool_name,
                available=True,
                version=version,
                path=tool_cmd
            )
        except Exception as e:
            return ToolValidationResult(
                tool_name=tool_name,
                available=False,
                path=tool_cmd,
                error_message=f'{tool_name} found but failed to run: {e}'
            )
