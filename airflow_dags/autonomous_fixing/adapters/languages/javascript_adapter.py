"""JavaScript/TypeScript language adapter."""

import subprocess
import json
import re
import time
import shutil
from pathlib import Path
from typing import List, Dict
from .base import LanguageAdapter
from ...domain.models import AnalysisResult, ToolValidationResult
from ..test_result_parser import TestResultParserStrategy
from ..error_parser import ErrorParserStrategy


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
            result.complexity_violations = self.check_complexity(project_path)

            # Quality check delegated to AnalysisResult model (SOLID: Single Responsibility)
            result.success = result.compute_quality_check()
            result.execution_time = time.time() - start_time

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """Run Jest/Vitest with strategy using centralized parsing."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='tests',
            project_path=project_path
        )

        try:
            # Determine test framework
            framework = self.config.get('test_framework', 'jest')
            output_file = Path(project_path) / '.test-results.json'

            # Build test command based on strategy
            if framework == 'jest':
                cmd = ['npm', 'test', '--']
                # Try to get JSON output for structured parsing
                cmd.extend(['--json', f'--outputFile={output_file}'])
            else:  # vitest
                cmd = ['npm', 'run', 'test', '--']
                cmd.extend(['--reporter=json', f'--outputFile={output_file}'])

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

            # Parse test results using centralized strategy (SOLID: Single Responsibility)
            output = test_result.stdout + test_result.stderr
            counts = TestResultParserStrategy.parse(
                language='javascript',
                output=output,
                output_file=output_file if output_file.exists() else None
            )

            # Parse test failures for error reporting
            result.test_failures = self.parse_errors(output, 'tests')

            # Apply parsed counts
            result.tests_passed = counts.passed
            result.tests_failed = counts.failed
            result.tests_skipped = counts.skipped

            result.success = counts.success
            result.execution_time = time.time() - start_time

            # Cleanup JSON output file
            if output_file.exists():
                output_file.unlink()

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
        """Parse JS/TS error messages using centralized parser (SOLID: SRP)."""
        # Use centralized error parser for all phases
        return ErrorParserStrategy.parse(
            language='javascript',
            output=output,
            phase=phase
        )

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
        """Get all JS/TS source files using centralized exclusion (SOLID: DRY)."""
        source_files = []
        for pattern in ['**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx']:
            source_files.extend(project_path.rglob(pattern))

        return self._filter_excluded_paths(source_files)

    def _run_eslint(self, project_path: str) -> List[Dict]:
        """Run ESLint and parse errors using centralized parser."""
        try:
            result = subprocess.run(
                ['npx', 'eslint', '.', '--format', 'json'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Use centralized error parser (SOLID: Single Responsibility)
            return ErrorParserStrategy.parse(
                language='javascript',
                output=result.stdout,
                phase='static'
            )

        except Exception:
            return []

    def _run_tsc(self, project_path: str) -> List[Dict]:
        """Run TypeScript compiler and parse errors using centralized parser."""
        try:
            result = subprocess.run(
                ['npx', 'tsc', '--noEmit'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Use centralized error parser (SOLID: Single Responsibility)
            return ErrorParserStrategy.parse(
                language='typescript',
                output=result.stdout,
                phase='static'
            )

        except Exception:
            return []

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

    def validate_tools(self) -> List[ToolValidationResult]:
        """Validate JavaScript/TypeScript toolchain availability."""
        results = []

        # 1. Node.js
        results.append(self._validate_node())

        # 2. Package manager (npm/yarn/pnpm)
        results.append(self._validate_package_manager())

        # 3. Linter (ESLint/TSC)
        linters = self.config.get('linters', ['eslint'])
        for linter in linters:
            if linter == 'eslint':
                results.append(self._validate_tool('eslint', '--version', 'Install ESLint: npm install -g eslint'))
            elif linter == 'tsc':
                results.append(self._validate_tool('tsc', '--version', 'Install TypeScript: npm install -g typescript'))

        # 4. Test runner
        test_runner = self.config.get('test_runner', 'jest')
        results.append(self._validate_tool(
            test_runner,
            '--version',
            f'Install {test_runner}: npm install -g {test_runner}'
        ))

        return results

    def _validate_node(self) -> ToolValidationResult:
        """Validate Node.js installation."""
        node_cmd = shutil.which('node')

        if not node_cmd:
            return ToolValidationResult(
                tool_name='node',
                available=False,
                error_message='Node.js not found in PATH',
                fix_suggestion='Install Node.js: https://nodejs.org/en/download'
            )

        try:
            result = subprocess.run(
                [node_cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            version = result.stdout.strip().lstrip('v')

            return ToolValidationResult(
                tool_name='node',
                available=True,
                version=version,
                path=node_cmd
            )
        except Exception as e:
            return ToolValidationResult(
                tool_name='node',
                available=False,
                path=node_cmd,
                error_message=f'Node.js found but failed to run: {e}'
            )

    def _validate_package_manager(self) -> ToolValidationResult:
        """Validate package manager (npm/yarn/pnpm)."""
        # Try npm first (comes with Node.js)
        for pm in ['npm', 'yarn', 'pnpm']:
            pm_cmd = shutil.which(pm)
            if pm_cmd:
                try:
                    result = subprocess.run(
                        [pm_cmd, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    return ToolValidationResult(
                        tool_name=pm,
                        available=True,
                        version=result.stdout.strip(),
                        path=pm_cmd
                    )
                except:
                    continue

        return ToolValidationResult(
            tool_name='npm/yarn/pnpm',
            available=False,
            error_message='No package manager found',
            fix_suggestion='Install Node.js (includes npm): https://nodejs.org'
        )

    def _validate_tool(self, tool_name: str, version_flag: str, fix_suggestion: str) -> ToolValidationResult:
        """Generic tool validation."""
        tool_cmd = shutil.which(tool_name)

        if not tool_cmd:
            return ToolValidationResult(
                tool_name=tool_name,
                available=False,
                error_message=f'{tool_name} not found in PATH',
                fix_suggestion=fix_suggestion
            )

        try:
            result = subprocess.run(
                [tool_cmd, version_flag],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Extract version from output
            output = result.stdout + result.stderr
            version_match = re.search(r'v?([\d.]+)', output)
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
