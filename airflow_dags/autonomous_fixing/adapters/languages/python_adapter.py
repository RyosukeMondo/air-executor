"""Python language adapter."""

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

from ...domain.exceptions import ConfigurationError
from ...domain.models import AnalysisResult, ToolValidationResult
from ..error_parser import ErrorParserStrategy
from ..test_result_parser import TestResultParserStrategy
from .base import LanguageAdapter
from .python_linters import PythonLinters


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
        """Run configured linters (ruff/pylint + mypy)."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name, phase="static", project_path=project_path
        )

        try:
            errors = []

            # Run linters based on config
            linters = self.config.get("linters", ["ruff", "mypy"])

            if "ruff" in linters:
                errors.extend(PythonLinters.run_ruff(project_path))

            if "pylint" in linters:
                errors.extend(PythonLinters.run_pylint(project_path))

            if "mypy" in linters:
                errors.extend(PythonLinters.run_mypy(project_path))

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
            # Other runtime errors - create failed result
            result.success = False
            result.error_message = str(e)
            result.execution_time = time.time() - start_time
        except Exception as e:
            # Unexpected errors - log and fail
            result.success = False
            result.error_message = f"Unexpected error in static analysis: {e}"
            result.execution_time = time.time() - start_time

        return result

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """Run pytest with strategy using centralized parsing."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name, phase="tests", project_path=project_path
        )

        try:
            # Build pytest command based on strategy
            xml_file = Path(project_path) / ".pytest-results.xml"
            cmd = ["pytest", f"--junitxml={xml_file}"]

            if strategy == "minimal":
                # Only fast tests, no slow or integration
                cmd.extend(["-m", "not slow and not integration", "--tb=short"])
                timeout = 300  # 5 min
            elif strategy == "selective":
                # No integration tests
                cmd.extend(["-m", "not integration"])
                timeout = 900  # 15 min
            else:  # comprehensive
                # Full test suite
                cmd.extend(["-v"])
                timeout = 1800  # 30 min

            test_result = subprocess.run(
                cmd, cwd=project_path, capture_output=True, text=True, timeout=timeout
            )

            # Parse test results using centralized strategy (SOLID: Single Responsibility)
            output = test_result.stdout + test_result.stderr
            counts = TestResultParserStrategy.parse(
                language="python",
                output=output,
                output_file=xml_file if xml_file.exists() else None,
            )

            # Parse test failures for error reporting
            result.test_failures = self.parse_errors(output, "tests")

            # Apply parsed counts
            result.tests_passed = counts.passed
            result.tests_failed = counts.failed
            result.tests_skipped = counts.skipped

            result.success = counts.success
            result.execution_time = time.time() - start_time

            # Cleanup XML file
            if xml_file.exists():
                xml_file.unlink()

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = f"Tests timed out after {timeout} seconds"
            result.execution_time = time.time() - start_time
        except FileNotFoundError as e:
            # pytest not installed or not in PATH - fail fast
            raise ConfigurationError(
                f"pytest not found: {e}\n"
                f"Install with: pip install pytest"
            ) from e
        except Exception as e:
            # Unexpected errors
            result.success = False
            result.error_message = f"Unexpected error running tests: {e}"
            result.execution_time = time.time() - start_time

        return result

    def analyze_coverage(self, project_path: str) -> AnalysisResult:
        """Analyze test coverage using pytest-cov."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name, phase="coverage", project_path=project_path
        )

        try:
            # Run pytest with coverage
            cmd = ["pytest", "--cov", "--cov-report=json", "--cov-report=term"]
            subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                timeout=1800,  # 30 min
            )

            # Parse coverage JSON
            coverage_file = Path(project_path) / "coverage.json"
            if coverage_file.exists():
                coverage_data = self._parse_coverage_json(coverage_file)
                result.coverage_percentage = coverage_data["percentage"]
                result.coverage_gaps = coverage_data["gaps"]

            result.success = True
            result.execution_time = time.time() - start_time

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = "Coverage analysis timed out"
            result.execution_time = time.time() - start_time
        except FileNotFoundError as e:
            # pytest-cov not installed - fail fast
            raise ConfigurationError(
                f"pytest-cov not found: {e}\n"
                f"Install with: pip install pytest-cov"
            ) from e
        except Exception as e:
            # Unexpected errors
            result.success = False
            result.error_message = f"Unexpected error in coverage analysis: {e}"
            result.execution_time = time.time() - start_time

        return result

    def run_e2e_tests(self, project_path: str) -> AnalysisResult:
        """Run E2E tests (marked with @pytest.mark.e2e)."""
        start_time = time.time()
        result = AnalysisResult(language=self.language_name, phase="e2e", project_path=project_path)

        try:
            # Run only E2E marked tests
            cmd = ["pytest", "-m", "e2e", "-v"]
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
            # pytest not available - fail fast
            raise ConfigurationError(
                f"pytest not found for E2E tests: {e}\n"
                f"Install with: pip install pytest"
            ) from e
        except Exception as e:
            # Unexpected errors
            result.success = False
            result.error_message = f"Unexpected error in E2E tests: {e}"
            result.execution_time = time.time() - start_time

        return result

    def parse_errors(self, output: str, phase: str) -> List[Dict]:
        """Parse Python error messages using centralized parser (SOLID: SRP)."""
        # Use centralized error parser for all phases
        return ErrorParserStrategy.parse(language="python", output=output, phase=phase)

    def calculate_complexity(self, file_path: str) -> int:
        """Calculate cyclomatic complexity using radon.

        Raises:
            FileNotFoundError: If file doesn't exist
            subprocess.TimeoutExpired: If radon hangs
            RuntimeError: If radon is not installed or fails
        """
        # Verify file exists first
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Cannot calculate complexity: {file_path} does not exist")

        # Use radon for accurate complexity via Python module (works with venv)
        result = subprocess.run(
            [sys.executable, "-m", "radon", "cc", file_path, "-s", "-n", "A"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Check if radon failed
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            if "No module named" in error_msg:
                raise ConfigurationError(
                    f"Radon is not installed. Install with: pip install radon\n"
                    f"Error: {error_msg}"
                )
            raise RuntimeError(f"Radon failed with exit code {result.returncode}: {error_msg}")

        # Parse radon output: "A 1:0 ClassName.method_name - A (1)"
        max_complexity = 0
        for match in re.finditer(r"\((\d+)\)", result.stdout):
            complexity = int(match.group(1))
            max_complexity = max(max_complexity, complexity)

        return max_complexity

    def _simple_complexity(self, file_path: str) -> int:
        """Simple complexity heuristic (fallback)."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            complexity = 1
            complexity += content.count(" if ")
            complexity += content.count(" for ")
            complexity += content.count(" while ")
            complexity += content.count(" and ")
            complexity += content.count(" or ")
            complexity += content.count("except ")

            return complexity

        except Exception:
            return 0

    def _get_source_files(self, project_path: Path) -> List[Path]:
        """Get all Python source files."""
        source_files = []
        for pattern in ["**/*.py"]:
            source_files.extend(project_path.rglob(pattern))

        # Use base class exclusion filtering (COMMON_EXCLUSIONS)
        return self._filter_excluded_paths(source_files)

    def _parse_coverage_json(self, coverage_file: Path) -> Dict:
        """Parse coverage.json file."""
        try:
            with open(coverage_file) as f:
                data = json.load(f)

            # Get overall coverage percentage
            totals = data.get("totals", {})
            percentage = totals.get("percent_covered", 0)

            # Find files with low/no coverage
            gaps = []
            files = data.get("files", {})
            for file_path, file_data in files.items():
                file_coverage = file_data.get("summary", {}).get("percent_covered", 0)
                if file_coverage < 50:  # Less than 50% coverage
                    gaps.append(
                        {
                            "file": file_path,
                            "coverage": file_coverage,
                            "message": f"Low coverage: {file_coverage:.1f}%",
                        }
                    )

            return {"percentage": percentage, "gaps": gaps}

        except Exception:
            return {"percentage": 0, "gaps": []}

    def validate_tools(self) -> List[ToolValidationResult]:
        """Validate Python toolchain availability."""
        results = []

        # 1. Python itself
        results.append(self._validate_python())

        # 2. Linters (from config)
        linters = self.config.get("linters", ["ruff", "mypy"])
        for linter in linters:
            results.append(
                self._validate_tool(
                    linter,
                    version_flag="--version",
                    fix_suggestion=f"Install {linter}: pip install {linter}",
                )
            )

        # 3. Test runner
        test_runner = self.config.get("test_runner", "pytest")
        results.append(
            self._validate_tool(
                test_runner,
                version_flag="--version",
                fix_suggestion=f"Install {test_runner}: pip install {test_runner}",
            )
        )

        # 4. Coverage tool (optional)
        results.append(
            self._validate_tool(
                "coverage",
                version_flag="--version",
                fix_suggestion="Install coverage: pip install coverage",
                optional=True,
            )
        )

        return results

    def _validate_python(self) -> ToolValidationResult:
        """Validate Python installation."""
        python_cmd = shutil.which("python") or shutil.which("python3")

        if not python_cmd:
            return ToolValidationResult(
                tool_name="python",
                available=False,
                error_message="Python not found in PATH",
                fix_suggestion="Install Python: https://python.org/downloads",
            )

        try:
            result = subprocess.run(
                [python_cmd, "--version"], capture_output=True, text=True, timeout=5
            )

            version_match = re.search(r"Python ([\d.]+)", result.stdout + result.stderr)
            version = version_match.group(1) if version_match else "unknown"

            return ToolValidationResult(
                tool_name="python", available=True, version=version, path=python_cmd
            )
        except Exception as e:
            return ToolValidationResult(
                tool_name="python",
                available=False,
                path=python_cmd,
                error_message=f"Python found but failed to run: {e}",
            )

    def _validate_tool(
        self, tool_name: str, version_flag: str, fix_suggestion: str, optional: bool = False
    ) -> ToolValidationResult:
        """Generic tool validation."""
        # First check PATH
        tool_cmd = shutil.which(tool_name)

        # If not in PATH, check if running in venv and look there
        if not tool_cmd:
            import sys

            if hasattr(sys, "prefix") and sys.prefix != sys.base_prefix:
                # We're in a venv, check venv bin directory
                venv_bin = Path(sys.prefix) / "bin" / tool_name
                if venv_bin.exists():
                    tool_cmd = str(venv_bin)

        if not tool_cmd:
            return ToolValidationResult(
                tool_name=tool_name,
                available=False,
                error_message=f"{tool_name} not found in PATH"
                if not optional
                else f"{tool_name} not found (optional)",
                fix_suggestion=fix_suggestion if not optional else None,
            )

        try:
            result = subprocess.run(
                [tool_cmd, version_flag], capture_output=True, text=True, timeout=5
            )

            # Try to extract version from output
            output = result.stdout + result.stderr
            version_match = re.search(r"([\d.]+)", output)
            version = version_match.group(1) if version_match else "unknown"

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

    def run_type_check(self, project_path: str) -> AnalysisResult:
        """Run mypy type checking."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name, phase="type_check", project_path=project_path
        )

        try:
            # Check if mypy is available
            if not shutil.which("mypy"):
                result.success = True  # No mypy, consider it passing
                result.execution_time = time.time() - start_time
                return result

            # Run mypy
            proc = subprocess.run(
                ["mypy", "."], cwd=project_path, capture_output=True, text=True, timeout=120
            )

            if proc.returncode != 0:
                result.success = False
                result.errors = self.parse_errors(proc.stdout + proc.stderr, "type_check")
            else:
                result.success = True

        except subprocess.TimeoutExpired:
            result.success = False
            result.errors = [{"message": "Type checking timed out after 120 seconds"}]
            result.execution_time = time.time() - start_time
        except FileNotFoundError as e:
            # mypy not installed - fail fast
            raise ConfigurationError(
                f"mypy not found: {e}\n"
                f"Install with: pip install mypy"
            ) from e
        except Exception as e:
            # Unexpected errors
            result.success = False
            result.errors = [{"message": f"Unexpected type check error: {str(e)}"}]
            result.execution_time = time.time() - start_time

        result.execution_time = time.time() - start_time
        return result

    def run_build(self, project_path: str) -> AnalysisResult:
        """Run Python syntax check (no traditional build needed)."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name, phase="build", project_path=project_path
        )

        try:
            # For Python, "build" means checking syntax of all .py files
            source_files = self._get_source_files(Path(project_path))

            for file_path in source_files:
                try:
                    # Compile to check syntax
                    with open(file_path) as f:
                        compile(f.read(), str(file_path), "exec")
                except SyntaxError as e:
                    result.success = False
                    result.errors.append(
                        {
                            "file": str(file_path),
                            "line": e.lineno,
                            "message": f"Syntax error: {e.msg}",
                        }
                    )

            if not result.errors:
                result.success = True
            else:
                result.error_message = f"{len(result.errors)} syntax errors found"

        except FileNotFoundError as e:
            # Python not available - fail fast
            raise ConfigurationError(
                f"Python not found for syntax check: {e}\n"
                f"Python installation may be corrupted"
            ) from e
        except Exception as e:
            # Unexpected errors
            result.success = False
            result.error_message = f"Unexpected build check error: {str(e)}"
            result.errors = [{"message": result.error_message}]

        result.execution_time = time.time() - start_time
        return result
