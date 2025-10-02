"""JavaScript/TypeScript language adapter."""

import subprocess
import json
import re
import time
from pathlib import Path
from typing import List, Dict
from .base import LanguageAdapter, AnalysisResult


class JavaScriptAdapter(LanguageAdapter):
    """Adapter for JavaScript/TypeScript projects."""

    @property
    def language_name(self) -> str:
        return "javascript"

    @property
    def project_markers(self) -> List[str]:
        return ["package.json"]

    def detect_projects(self, root_path: str) -> List[str]:
        """Find all JS/TS projects by package.json."""
        projects = []
        root = Path(root_path)

        for package_json in root.rglob("package.json"):
            # Exclude node_modules
            if 'node_modules' not in package_json.parts:
                projects.append(str(package_json.parent))

        return projects

    def static_analysis(self, project_path: str) -> AnalysisResult:
        """Run eslint + tsc in parallel."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='static',
            project_path=project_path
        )

        try:
            errors = []

            # Run ESLint
            errors.extend(self._run_eslint(project_path))

            # Run TypeScript compiler if tsconfig exists
            if (Path(project_path) / 'tsconfig.json').exists():
                errors.extend(self._run_tsc(project_path))

            result.errors = errors
            result.file_size_violations = self.check_file_sizes(project_path)
            result.complexity_violations = self._check_complexity(project_path)

            result.success = len(result.errors) == 0
            result.execution_time = time.time() - start_time

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """Run Jest/Vitest with strategy."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='tests',
            project_path=project_path
        )

        try:
            # Determine test framework
            framework = self.config.get('test_framework', 'jest')

            # Build test command based on strategy
            if framework == 'jest':
                cmd = ['npm', 'test', '--']
            else:  # vitest
                cmd = ['npm', 'run', 'test', '--']

            if strategy == 'minimal':
                # Only unit tests, fast
                cmd.extend(['--testPathPattern=unit', '--bail'])
                timeout = 300  # 5 min
            elif strategy == 'selective':
                # Unit + integration
                cmd.extend(['--testPathPattern=(unit|integration)'])
                timeout = 900  # 15 min
            else:  # comprehensive
                # Full suite
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
        """Analyze test coverage using Jest/Vitest coverage."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='coverage',
            project_path=project_path
        )

        try:
            # Run tests with coverage
            cmd = ['npm', 'test', '--', '--coverage', '--coverageReporters=json']
            subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                timeout=1800  # 30 min
            )

            # Parse coverage JSON
            coverage_file = Path(project_path) / 'coverage' / 'coverage-final.json'
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
        """Run E2E tests using Playwright/Cypress."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='e2e',
            project_path=project_path
        )

        try:
            # Check for E2E framework
            package_json = Path(project_path) / 'package.json'
            with open(package_json) as f:
                package_data = json.load(f)

            deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}

            if 'playwright' in deps or '@playwright/test' in deps:
                cmd = ['npx', 'playwright', 'test']
            elif 'cypress' in deps:
                cmd = ['npx', 'cypress', 'run']
            else:
                result.success = True
                result.error_message = "No E2E framework found"
                return result

            # Run E2E tests
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
        """Parse JS/TS error messages."""
        errors = []

        if phase == 'tests':
            # Jest/Vitest format: FAIL src/file.test.js
            # or: ● Test suite failed to run
            pattern = r'FAIL\s+(.+\.(?:test|spec)\.[jt]sx?)'
            for match in re.finditer(pattern, output):
                errors.append({
                    'severity': 'error',
                    'file': match.group(1),
                    'line': 0,
                    'column': 0,
                    'message': 'Test suite failed',
                    'code': 'test_failure'
                })

            # Extract specific test failures
            pattern = r'●\s+(.+)'
            for match in re.finditer(pattern, output):
                if errors:
                    errors[-1]['message'] += f' - {match.group(1)}'

        elif phase == 'e2e':
            # Playwright: Error: expect(received).toBe(expected)
            # Cypress: CypressError: Timed out retrying
            pattern = r'Error:\s+(.+)'
            for match in re.finditer(pattern, output):
                errors.append({
                    'severity': 'error',
                    'file': '',
                    'line': 0,
                    'column': 0,
                    'message': match.group(1),
                    'code': 'e2e_failure'
                })

        return errors

    def calculate_complexity(self, file_path: str) -> int:
        """Calculate cyclomatic complexity using complexity-report."""
        try:
            # Use complexity-report if available
            result = subprocess.run(
                ['npx', 'complexity-report', file_path, '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.stdout:
                data = json.loads(result.stdout)
                # Get maximum complexity from all functions
                max_complexity = 0
                for func in data.get('functions', []):
                    complexity = func.get('cyclomatic', 0)
                    max_complexity = max(max_complexity, complexity)
                return max_complexity

        except Exception:
            pass

        # Fallback to simple heuristic
        return self._simple_complexity(file_path)

    def _simple_complexity(self, file_path: str) -> int:
        """Simple complexity heuristic."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            complexity = 1
            complexity += content.count(' if ')
            complexity += content.count(' for ')
            complexity += content.count(' while ')
            complexity += content.count(' case ')
            complexity += content.count(' && ')
            complexity += content.count(' || ')
            complexity += content.count(' ?? ')
            complexity += content.count('catch ')

            return complexity

        except Exception:
            return 0

    def _get_source_files(self, project_path: Path) -> List[Path]:
        """Get all JS/TS source files."""
        source_files = []
        for pattern in ['**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx']:
            source_files.extend(project_path.rglob(pattern))

        # Exclude node_modules, build, dist
        excluded = {'node_modules', 'build', 'dist', 'coverage', '.next', 'out'}
        return [f for f in source_files if not any(e in f.parts for e in excluded)]

    def _run_eslint(self, project_path: str) -> List[Dict]:
        """Run ESLint and parse errors."""
        try:
            result = subprocess.run(
                ['npx', 'eslint', '.', '--format', 'json'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.stdout:
                lint_results = json.loads(result.stdout)
                errors = []
                for file_result in lint_results:
                    for message in file_result.get('messages', []):
                        if message.get('severity') == 2:  # Error level
                            errors.append({
                                'severity': 'error',
                                'file': file_result.get('filePath', ''),
                                'line': message.get('line', 0),
                                'column': message.get('column', 0),
                                'message': message.get('message', ''),
                                'code': message.get('ruleId', '')
                            })
                return errors

        except Exception:
            pass

        return []

    def _run_tsc(self, project_path: str) -> List[Dict]:
        """Run TypeScript compiler and parse errors."""
        try:
            result = subprocess.run(
                ['npx', 'tsc', '--noEmit'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            errors = []
            # TSC format: file.ts(line,col): error TS1234: message
            pattern = r'(.+\.tsx?)\((\d+),(\d+)\):\s*error\s*TS(\d+):\s*(.+)'
            for match in re.finditer(pattern, result.stdout):
                errors.append({
                    'severity': 'error',
                    'file': match.group(1),
                    'line': int(match.group(2)),
                    'column': int(match.group(3)),
                    'message': match.group(5),
                    'code': f'TS{match.group(4)}'
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
        """Extract test pass/fail counts."""
        passed = 0
        failed = 0

        # Jest: "Tests: 2 failed, 5 passed, 7 total"
        if match := re.search(r'(\d+) passed', output):
            passed = int(match.group(1))
        if match := re.search(r'(\d+) failed', output):
            failed = int(match.group(1))

        return {'passed': passed, 'failed': failed}

    def _parse_coverage_json(self, coverage_file: Path) -> Dict:
        """Parse Jest/Vitest coverage JSON."""
        try:
            with open(coverage_file) as f:
                data = json.load(f)

            # Calculate overall coverage
            total_lines = 0
            covered_lines = 0
            gaps = []

            for file_path, file_data in data.items():
                if 's' in file_data:  # Statement coverage
                    statements = file_data['s']
                    total_lines += len(statements)
                    covered_lines += sum(1 for hits in statements.values() if hits > 0)

                    # Check if file has low coverage
                    file_total = len(statements)
                    file_covered = sum(1 for hits in statements.values() if hits > 0)
                    coverage_pct = (file_covered / file_total * 100) if file_total > 0 else 0

                    if coverage_pct < 50:
                        gaps.append({
                            'file': file_path,
                            'coverage': coverage_pct,
                            'message': f'Low coverage: {coverage_pct:.1f}%'
                        })

            percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0

            return {
                'percentage': percentage,
                'gaps': gaps
            }

        except Exception:
            return {'percentage': 0, 'gaps': []}
