"""Go language adapter."""

import subprocess
import re
import time
import shutil
from pathlib import Path
from typing import List, Dict
from .base import LanguageAdapter
from ...domain.models import AnalysisResult, ToolValidationResult
from ..error_parser import ErrorParserStrategy


class GoAdapter(LanguageAdapter):
    """Adapter for Go projects."""

    @property
    def language_name(self) -> str:
        return "go"

    @property
    def project_markers(self) -> List[str]:
        return ["go.mod"]

    def detect_projects(self, root_path: str) -> List[str]:
        """Find all Go projects by go.mod."""
        projects = []
        root = Path(root_path)

        for go_mod in root.rglob("go.mod"):
            projects.append(str(go_mod.parent))

        return projects

    def static_analysis(self, project_path: str) -> AnalysisResult:
        """Run go vet + staticcheck."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='static',
            project_path=project_path
        )

        try:
            errors = []

            # Run go vet
            errors.extend(self._run_go_vet(project_path))

            # Run staticcheck if available
            linters = self.config.get('linters', ['go vet', 'staticcheck'])
            if 'staticcheck' in linters:
                errors.extend(self._run_staticcheck(project_path))

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
        """Run go test with strategy."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='tests',
            project_path=project_path
        )

        try:
            # Build test command based on strategy
            cmd = ['go', 'test', './...']

            if strategy == 'minimal':
                # Only short tests
                cmd.append('-short')
                timeout = 300  # 5 min
            elif strategy == 'selective':
                # Short tests + tagged non-integration
                cmd.extend(['-short', '-tags=!integration'])
                timeout = 900  # 15 min
            else:  # comprehensive
                # Full test suite
                cmd.append('-v')
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
        """Analyze test coverage using go test -cover."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='coverage',
            project_path=project_path
        )

        try:
            # Run tests with coverage
            cmd = ['go', 'test', './...', '-coverprofile=coverage.out', '-covermode=atomic']
            subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                timeout=1800  # 30 min
            )

            # Parse coverage file
            coverage_file = Path(project_path) / 'coverage.out'
            if coverage_file.exists():
                coverage_data = self._parse_coverage_file(coverage_file)
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
        """Run E2E tests (tagged with integration)."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name,
            phase='e2e',
            project_path=project_path
        )

        try:
            # Run integration tests
            cmd = ['go', 'test', './...', '-tags=integration', '-v']
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
        """Parse Go error messages using centralized parser (SOLID: SRP)."""
        return ErrorParserStrategy.parse(
            language='go',
            output=output,
            phase=phase
        )
    def calculate_complexity(self, file_path: str) -> int:
        """Calculate cyclomatic complexity using gocyclo."""
        try:
            # Use gocyclo if available
            result = subprocess.run(
                ['gocyclo', '-over', '1', file_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            # gocyclo output: "10 main main.go:15:1 funcName"
            max_complexity = 0
            pattern = r'^(\d+)\s+'
            for match in re.finditer(pattern, result.stdout, re.MULTILINE):
                complexity = int(match.group(1))
                max_complexity = max(max_complexity, complexity)

            return max_complexity

        except Exception:
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
            complexity += content.count(' case ')
            complexity += content.count(' && ')
            complexity += content.count(' || ')
            complexity += content.count('select {')

            return complexity

        except Exception:
            return 0

    def _get_source_files(self, project_path: Path) -> List[Path]:
        """Get all Go source files."""
        source_files = []
        for go_file in project_path.rglob('*.go'):
            # Exclude test files and vendor
            if not go_file.name.endswith('_test.go') and 'vendor' not in go_file.parts:
                source_files.append(go_file)
        return source_files

    def _run_go_vet(self, project_path: str) -> List[Dict]:
        """Run go vet and parse errors."""
        try:
            result = subprocess.run(
                ['go', 'vet', './...'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            errors = []
            # go vet format: file.go:line:col: message
            pattern = r'(.+\.go):(\d+):(\d+):\s*(.+)'
            for match in re.finditer(pattern, result.stderr):
                errors.append({
                    'severity': 'error',
                    'file': match.group(1),
                    'line': int(match.group(2)),
                    'column': int(match.group(3)),
                    'message': match.group(4),
                    'code': 'vet'
                })

            return errors

        except Exception:
            pass

        return []

    def _run_staticcheck(self, project_path: str) -> List[Dict]:
        """Run staticcheck and parse errors."""
        try:
            result = subprocess.run(
                ['staticcheck', './...'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            errors = []
            # staticcheck format: file.go:line:col: message (SA1234)
            pattern = r'(.+\.go):(\d+):(\d+):\s*(.+?)\s*\((\w+)\)'
            for match in re.finditer(pattern, result.stdout):
                errors.append({
                    'severity': 'error',
                    'file': match.group(1),
                    'line': int(match.group(2)),
                    'column': int(match.group(3)),
                    'message': match.group(4),
                    'code': match.group(5)
                })

            return errors

        except Exception:
            pass

        return []

    def _extract_test_counts(self, output: str) -> Dict[str, int]:
        """Extract test pass/fail counts."""
        passed = 0
        failed = 0

        # Count PASS and FAIL lines
        passed = output.count('PASS:')
        failed = output.count('FAIL:')

        # Also look for summary: "ok  	package/path	0.123s"
        ok_count = output.count('\nok  ')
        fail_count = output.count('\nFAIL')

        return {
            'passed': max(passed, ok_count),
            'failed': max(failed, fail_count)
        }

    def _parse_coverage_file(self, coverage_file: Path) -> Dict:
        """Parse Go coverage.out file."""
        try:
            with open(coverage_file) as f:
                lines = f.readlines()

            # Skip mode line
            if lines and lines[0].startswith('mode:'):
                lines = lines[1:]

            # Parse coverage lines: file.go:startLine.col,endLine.col numStmt count
            total_stmts = 0
            covered_stmts = 0
            file_coverage = {}

            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 3:
                    file_loc = parts[0].split(':')[0]  # Extract filename
                    num_stmts = int(parts[1])
                    count = int(parts[2])

                    total_stmts += num_stmts
                    if count > 0:
                        covered_stmts += num_stmts

                    # Track per-file coverage
                    if file_loc not in file_coverage:
                        file_coverage[file_loc] = {'total': 0, 'covered': 0}
                    file_coverage[file_loc]['total'] += num_stmts
                    if count > 0:
                        file_coverage[file_loc]['covered'] += num_stmts

            # Calculate overall percentage
            percentage = (covered_stmts / total_stmts * 100) if total_stmts > 0 else 0

            # Find files with low coverage
            gaps = []
            for file_path, cov_data in file_coverage.items():
                file_pct = (cov_data['covered'] / cov_data['total'] * 100) if cov_data['total'] > 0 else 0
                if file_pct < 50:
                    gaps.append({
                        'file': file_path,
                        'coverage': file_pct,
                        'message': f'Low coverage: {file_pct:.1f}%'
                    })

            return {
                'percentage': percentage,
                'gaps': gaps
            }

        except Exception:
            return {'percentage': 0, 'gaps': []}

    def validate_tools(self) -> List[ToolValidationResult]:
        """Validate Go toolchain availability."""
        results = []

        # 1. Go itself
        results.append(self._validate_go())

        # 2. Linters (from config)
        linters = self.config.get('linters', ['go vet', 'staticcheck'])
        if 'staticcheck' in linters:
            results.append(self._validate_tool(
                'staticcheck',
                version_flag='--version',
                fix_suggestion='Install staticcheck: go install honnef.co/go/tools/cmd/staticcheck@latest',
                optional=True
            ))

        # 3. Test runner (go test - built into go, validated via go command)
        # 4. Coverage tool (go test -cover - built into go)

        return results

    def _validate_go(self) -> ToolValidationResult:
        """Validate Go installation."""
        go_cmd = shutil.which('go')

        if not go_cmd:
            return ToolValidationResult(
                tool_name='go',
                available=False,
                error_message='Go not found in PATH',
                fix_suggestion='Install Go: https://golang.org/doc/install'
            )

        try:
            result = subprocess.run(
                [go_cmd, 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            version_match = re.search(r'go version go([\d.]+)', result.stdout)
            version = version_match.group(1) if version_match else 'unknown'

            return ToolValidationResult(
                tool_name='go',
                available=True,
                version=version,
                path=go_cmd
            )
        except Exception as e:
            return ToolValidationResult(
                tool_name='go',
                available=False,
                path=go_cmd,
                error_message=f'Go found but failed to run: {e}'
            )

    def _validate_tool(self, tool_name: str, version_flag: str, fix_suggestion: str, optional: bool = False) -> ToolValidationResult:
        """Generic tool validation."""
        tool_cmd = shutil.which(tool_name)

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
