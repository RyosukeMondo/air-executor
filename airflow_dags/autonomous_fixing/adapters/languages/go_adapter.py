"""Go language adapter."""

import re
import shutil
import subprocess
import time
from pathlib import Path

from ...domain.exceptions import ConfigurationError
from ...domain.models import AnalysisResult, ToolValidationResult
from ..error_parser import ErrorParserStrategy
from .base import LanguageAdapter


class GoAdapter(LanguageAdapter):
    """Adapter for Go projects."""

    @property
    def language_name(self) -> str:
        return "go"

    @property
    def project_markers(self) -> list[str]:
        return ["go.mod"]

    def detect_projects(self, root_path: str) -> list[str]:
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
            language=self.language_name, phase="static", project_path=project_path
        )

        try:
            errors = []

            # Run go vet
            errors.extend(self._run_go_vet(project_path))

            # Run staticcheck if available
            linters = self.config.get("linters", ["go vet", "staticcheck"])
            if "staticcheck" in linters:
                errors.extend(self._run_staticcheck(project_path))

            result.errors = errors
            result.file_size_violations = self.check_file_sizes(project_path)
            result.complexity_violations = self.check_complexity(project_path)

            # Quality check delegated to AnalysisResult model (SOLID: Single Responsibility)
            result.success = result.compute_quality_check()
            result.execution_time = time.time() - start_time

        except ConfigurationError:
            # Configuration errors from nested calls - re-raise immediately
            raise

        except RuntimeError as e:
            result.success = False
            result.error_message = str(e)
            result.execution_time = time.time() - start_time
        except Exception as e:
            result.success = False
            result.error_message = f"Unexpected error in static analysis: {e}"
            result.execution_time = time.time() - start_time

        return result

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """Run go test with strategy."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name, phase="tests", project_path=project_path
        )

        try:
            cmd, timeout = self._build_test_command(strategy)
            test_result = subprocess.run(
                cmd, cwd=project_path, capture_output=True, text=True, timeout=timeout
            )

            self._populate_test_results(result, test_result)
            result.success = test_result.returncode == 0
            result.execution_time = time.time() - start_time

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = f"Tests timed out after {timeout} seconds"
            result.execution_time = time.time() - start_time
        except FileNotFoundError as e:
            # go command not found - fail fast
            raise ConfigurationError(
                f"Go not found: {e}\n" f"Install Go: https://golang.org/doc/install"
            ) from e
        except Exception as e:
            result.success = False
            result.error_message = f"Unexpected error running tests: {e}"
            result.execution_time = time.time() - start_time

        return result

    def _build_test_command(self, strategy: str) -> tuple:
        """Build test command and timeout based on strategy."""
        cmd = ["go", "test", "./..."]

        if strategy == "minimal":
            cmd.append("-short")
            timeout = 300  # 5 min
        elif strategy == "selective":
            cmd.extend(["-short", "-tags=!integration"])
            timeout = 900  # 15 min
        else:  # comprehensive
            cmd.append("-v")
            timeout = 1800  # 30 min

        return cmd, timeout

    def _populate_test_results(self, result: AnalysisResult, test_result) -> None:
        """Populate test results from subprocess output."""
        result.test_failures = self.parse_errors(test_result.stdout + test_result.stderr, "tests")

        counts = self._extract_test_counts(test_result.stdout)
        result.tests_passed = counts["passed"]
        result.tests_failed = counts["failed"]

    def analyze_coverage(self, project_path: str) -> AnalysisResult:
        """Analyze test coverage using go test -cover."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name, phase="coverage", project_path=project_path
        )

        try:
            # Run tests with coverage
            cmd = ["go", "test", "./...", "-coverprofile=coverage.out", "-covermode=atomic"]
            subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                timeout=1800,  # 30 min
            )

            # Parse coverage file
            coverage_file = Path(project_path) / "coverage.out"
            if coverage_file.exists():
                coverage_data = self._parse_coverage_file(coverage_file)
                result.coverage_percentage = coverage_data["percentage"]
                result.coverage_gaps = coverage_data["gaps"]

            result.success = True
            result.execution_time = time.time() - start_time

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = "Coverage analysis timed out"
            result.execution_time = time.time() - start_time
        except FileNotFoundError as e:
            # go command not found - fail fast
            raise ConfigurationError(
                f"Go not found for coverage: {e}\n" f"Install Go: https://golang.org/doc/install"
            ) from e
        except Exception as e:
            result.success = False
            result.error_message = f"Unexpected error in coverage analysis: {e}"
            result.execution_time = time.time() - start_time

        return result

    def run_e2e_tests(self, project_path: str) -> AnalysisResult:
        """Run E2E tests (tagged with integration)."""
        start_time = time.time()
        result = AnalysisResult(language=self.language_name, phase="e2e", project_path=project_path)

        try:
            # Run integration tests
            cmd = ["go", "test", "./...", "-tags=integration", "-v"]
            test_result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=3600,  # 60 min
            )

            # Parse runtime errors
            result.runtime_errors = self.parse_errors(
                test_result.stdout + test_result.stderr, "e2e"
            )

            result.success = test_result.returncode == 0
            result.execution_time = time.time() - start_time

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = "E2E tests timed out"
            result.execution_time = time.time() - start_time
        except FileNotFoundError as e:
            # go command not found - fail fast
            raise ConfigurationError(
                f"Go not found for E2E tests: {e}\n" f"Install Go: https://golang.org/doc/install"
            ) from e
        except Exception as e:
            result.success = False
            result.error_message = f"Unexpected error in E2E tests: {e}"
            result.execution_time = time.time() - start_time

        return result

    def parse_errors(self, output: str, phase: str) -> list[dict]:
        """Parse Go error messages using centralized parser (SOLID: SRP)."""
        return ErrorParserStrategy.parse(language="go", output=output, phase=phase)

    def calculate_complexity(self, file_path: str) -> int:
        """Calculate cyclomatic complexity using gocyclo."""
        try:
            # Use gocyclo if available
            result = subprocess.run(
                ["gocyclo", "-over", "1", file_path], capture_output=True, text=True, timeout=5
            )

            # gocyclo output: "10 main main.go:15:1 funcName"
            max_complexity = 0
            pattern = r"^(\d+)\s+"
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
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            complexity = 1
            complexity += content.count(" if ")
            complexity += content.count(" for ")
            complexity += content.count(" case ")
            complexity += content.count(" && ")
            complexity += content.count(" || ")
            complexity += content.count("select {")

            return complexity

        except Exception:
            return 0

    def _get_source_files(self, project_path: Path) -> list[Path]:
        """Get all Go source files."""
        source_files = []
        for go_file in project_path.rglob("*.go"):
            # Exclude test files and vendor
            if not go_file.name.endswith("_test.go") and "vendor" not in go_file.parts:
                source_files.append(go_file)
        return source_files

    def _run_go_vet(self, project_path: str) -> list[dict]:
        """Run go vet and parse errors."""
        try:
            result = subprocess.run(
                ["go", "vet", "./..."],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            errors = []
            # go vet format: file.go:line:col: message
            pattern = r"(.+\.go):(\d+):(\d+):\s*(.+)"
            for match in re.finditer(pattern, result.stderr):
                errors.append(
                    {
                        "severity": "error",
                        "file": match.group(1),
                        "line": int(match.group(2)),
                        "column": int(match.group(3)),
                        "message": match.group(4),
                        "code": "vet",
                    }
                )

            return errors

        except Exception:
            pass

        return []

    def _run_staticcheck(self, project_path: str) -> list[dict]:
        """Run staticcheck and parse errors."""
        try:
            result = subprocess.run(
                ["staticcheck", "./..."],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            errors = []
            # staticcheck format: file.go:line:col: message (SA1234)
            pattern = r"(.+\.go):(\d+):(\d+):\s*(.+?)\s*\((\w+)\)"
            for match in re.finditer(pattern, result.stdout):
                errors.append(
                    {
                        "severity": "error",
                        "file": match.group(1),
                        "line": int(match.group(2)),
                        "column": int(match.group(3)),
                        "message": match.group(4),
                        "code": match.group(5),
                    }
                )

            return errors

        except Exception:
            pass

        return []

    def _extract_test_counts(self, output: str) -> dict[str, int]:
        """Extract test pass/fail counts."""
        passed = 0
        failed = 0

        # Count PASS and FAIL lines
        passed = output.count("PASS:")
        failed = output.count("FAIL:")

        # Also look for summary: "ok  	package/path	0.123s"
        ok_count = output.count("\nok  ")
        fail_count = output.count("\nFAIL")

        return {"passed": max(passed, ok_count), "failed": max(failed, fail_count)}

    def _parse_coverage_file(self, coverage_file: Path) -> dict:
        """Parse Go coverage.out file."""
        try:
            lines = self._read_coverage_lines(coverage_file)
            total_stmts, covered_stmts, file_coverage = self._process_coverage_lines(lines)
            percentage = self._calculate_percentage(covered_stmts, total_stmts)
            gaps = self._find_coverage_gaps(file_coverage)

            return {"percentage": percentage, "gaps": gaps}

        except Exception:
            return {"percentage": 0, "gaps": []}

    def _read_coverage_lines(self, coverage_file: Path) -> list[str]:
        """Read and prepare coverage file lines."""
        with open(coverage_file, encoding="utf-8") as f:
            lines = f.readlines()

        # Skip mode line if present
        if lines and lines[0].startswith("mode:"):
            return lines[1:]
        return lines

    def _process_coverage_lines(self, lines: list[str]) -> tuple:
        """Process coverage lines and extract coverage data."""
        total_stmts = 0
        covered_stmts = 0
        file_coverage = {}

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 3:
                continue

            file_loc = parts[0].split(":")[0]
            num_stmts = int(parts[1])
            count = int(parts[2])

            total_stmts += num_stmts
            if count > 0:
                covered_stmts += num_stmts

            self._update_file_coverage(file_coverage, file_loc, num_stmts, count)

        return total_stmts, covered_stmts, file_coverage

    def _update_file_coverage(
        self, file_coverage: dict, file_loc: str, num_stmts: int, count: int
    ) -> None:
        """Update coverage tracking for a specific file."""
        if file_loc not in file_coverage:
            file_coverage[file_loc] = {"total": 0, "covered": 0}

        file_coverage[file_loc]["total"] += num_stmts
        if count > 0:
            file_coverage[file_loc]["covered"] += num_stmts

    def _calculate_percentage(self, covered: int, total: int) -> float:
        """Calculate coverage percentage."""
        if total == 0:
            return 0
        return (covered / total) * 100

    def _find_coverage_gaps(self, file_coverage: dict) -> list[dict]:
        """Find files with low coverage (<50%)."""
        gaps = []
        for file_path, cov_data in file_coverage.items():
            file_pct = self._calculate_percentage(cov_data["covered"], cov_data["total"])
            if file_pct < 50:
                gaps.append(
                    {
                        "file": file_path,
                        "coverage": file_pct,
                        "message": f"Low coverage: {file_pct:.1f}%",
                    }
                )
        return gaps

    def validate_tools(self) -> list[ToolValidationResult]:
        """Validate Go toolchain availability."""
        results = []

        # 1. Go itself
        results.append(self._validate_go())

        # 2. Linters (from config)
        linters = self.config.get("linters", ["go vet", "staticcheck"])
        if "staticcheck" in linters:
            results.append(
                self._validate_tool(
                    "staticcheck",
                    version_flag="--version",
                    fix_suggestion=(
                        "Install staticcheck: "
                        "go install honnef.co/go/tools/cmd/staticcheck@latest"
                    ),
                    optional=True,
                )
            )

        # 3. Test runner (go test - built into go, validated via go command)
        # 4. Coverage tool (go test -cover - built into go)

        return results

    def _validate_go(self) -> ToolValidationResult:
        """Validate Go installation."""
        go_cmd = shutil.which("go")

        if not go_cmd:
            return ToolValidationResult(
                tool_name="go",
                available=False,
                error_message="Go not found in PATH",
                fix_suggestion="Install Go: https://golang.org/doc/install",
            )

        try:
            result = subprocess.run([go_cmd, "version"], capture_output=True, text=True, timeout=5)

            version = self._extract_go_version(result.stdout)
            return ToolValidationResult(
                tool_name="go", available=True, version=version, path=go_cmd
            )
        except Exception as e:
            return ToolValidationResult(
                tool_name="go",
                available=False,
                path=go_cmd,
                error_message=f"Go found but failed to run: {e}",
            )

    def _extract_go_version(self, output: str) -> str:
        """Extract Go version from 'go version' output."""
        version_match = re.search(r"go version go([\d.]+)", output)
        return version_match.group(1) if version_match else "unknown"

    def _validate_tool(
        self, tool_name: str, version_flag: str, fix_suggestion: str, optional: bool = False
    ) -> ToolValidationResult:
        """Generic tool validation."""
        tool_cmd = shutil.which(tool_name)

        if not tool_cmd:
            return self._create_tool_not_found_result(tool_name, fix_suggestion, optional)

        try:
            result = subprocess.run(
                [tool_cmd, version_flag], capture_output=True, text=True, timeout=5
            )

            version = self._extract_version(result.stdout + result.stderr)
            return ToolValidationResult(
                tool_name=tool_name, available=True, version=version, path=tool_cmd
            )
        except Exception as e:
            return ToolValidationResult(
                tool_name=tool_name,
                available=False,
                path=tool_cmd,
                error_message=f"{tool_name} found but failed to run: {e}",
            )

    def _create_tool_not_found_result(
        self, tool_name: str, fix_suggestion: str, optional: bool
    ) -> ToolValidationResult:
        """Create result for tool not found scenario."""
        error_msg = (
            f"{tool_name} not found in PATH"
            if not optional
            else f"{tool_name} not found (optional)"
        )
        return ToolValidationResult(
            tool_name=tool_name,
            available=False,
            error_message=error_msg,
            fix_suggestion=fix_suggestion if not optional else None,
        )

    def _extract_version(self, output: str) -> str:
        """Extract version number from tool output."""
        version_match = re.search(r"([\d.]+)", output)
        return version_match.group(1) if version_match else "unknown"
