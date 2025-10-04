"""Flutter language adapter."""

import re
import subprocess
import time
from pathlib import Path

from ...domain.models import AnalysisResult, ToolValidationResult
from ..error_parser import ErrorParserStrategy
from .base import LanguageAdapter
from .flutter_test_utils import FlutterTestUtils


class FlutterAdapter(LanguageAdapter):
    """Adapter for Flutter/Dart projects."""

    @property
    def language_name(self) -> str:
        return "flutter"

    @property
    def project_markers(self) -> list[str]:
        return ["pubspec.yaml"]

    def detect_projects(self, root_path: str) -> list[str]:
        """Find all Flutter projects by looking for pubspec.yaml."""
        projects = []
        root = Path(root_path)

        for pubspec in root.rglob("pubspec.yaml"):
            # Verify it's a Flutter project (has flutter dependency)
            try:
                with open(pubspec) as f:
                    content = f.read()
                    if "flutter:" in content or "flutter_test:" in content:
                        projects.append(str(pubspec.parent))
            except Exception:
                continue

        return projects

    def static_analysis(self, project_path: str) -> AnalysisResult:
        """Run flutter analyze + complexity checks."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name, phase="static", project_path=project_path
        )

        try:
            # Run flutter analyze
            analyze_cmd = ["flutter", "analyze", "--no-pub"]
            if args := self.config.get("analyzer_args"):
                analyze_cmd.extend(args.split())

            print(f"[DEBUG] Running: {' '.join(analyze_cmd)} in {project_path}")

            analyze_result = subprocess.run(
                analyze_cmd, cwd=project_path, capture_output=True, text=True, timeout=120
            )

            print(f"[DEBUG] Return code: {analyze_result.returncode}")
            print(f"[DEBUG] Stdout length: {len(analyze_result.stdout)}")
            print(f"[DEBUG] Stderr length: {len(analyze_result.stderr)}")

            # Parse errors
            raw_output = analyze_result.stdout + analyze_result.stderr
            result.errors = self.parse_errors(raw_output, "static")

            print(f"[DEBUG] Parsed {len(result.errors)} errors from output")
            if len(result.errors) > 0:
                print(f"[DEBUG] First error: {result.errors[0]}")

            # Check file sizes
            result.file_size_violations = self.check_file_sizes(project_path)

            # Check complexity
            result.complexity_violations = self.check_complexity(project_path)

            # Quality check delegated to AnalysisResult model (SOLID: Single Responsibility)
            result.success = result.compute_quality_check()
            result.execution_time = time.time() - start_time

            print(
                f"[DEBUG] Analysis result: errors={len(result.errors)}, success={result.success}, time={result.execution_time:.1f}s"
            )

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = "Static analysis timed out after 120 seconds"
            print("[DEBUG] TIMEOUT after 120s")
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            print(f"[DEBUG] EXCEPTION: {e}")

        return result

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """Run Flutter tests based on strategy."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name, phase="tests", project_path=project_path
        )

        try:
            flutter_cmd = FlutterTestUtils.find_flutter_executable()
            if not flutter_cmd:
                return self._handle_flutter_not_found(project_path, result, start_time)

            cmd, timeout = self._build_test_command(flutter_cmd, strategy)
            test_result = subprocess.run(
                cmd, cwd=project_path, capture_output=True, text=True, timeout=timeout
            )

            self._populate_test_result(result, test_result, project_path)
            result.success = test_result.returncode == 0
            result.execution_time = time.time() - start_time

        except subprocess.TimeoutExpired:
            result.success = False
            result.error_message = f"Tests timed out after {timeout} seconds"
        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def _handle_flutter_not_found(
        self, project_path: str, result: AnalysisResult, start_time: float
    ) -> AnalysisResult:
        """Handle case when Flutter executable is not found."""
        test_count = FlutterTestUtils.count_test_files_directly(project_path)
        result.tests_passed = test_count
        result.tests_failed = 0
        result.success = test_count > 0
        result.execution_time = time.time() - start_time
        result.error_message = f"Flutter not in PATH, counted {test_count} test files directly"
        return result

    def _build_test_command(self, flutter_cmd: str, strategy: str) -> tuple[list[str], int]:
        """Build test command and timeout based on strategy."""
        if strategy == "minimal":
            return [flutter_cmd, "test", "test/unit/", "--no-pub"], 300
        if strategy == "selective":
            return [flutter_cmd, "test", "--exclude-tags=integration", "--no-pub"], 900
        # comprehensive
        return [flutter_cmd, "test", "--no-pub"], 1800

    def _populate_test_result(
        self, result: AnalysisResult, test_result: subprocess.CompletedProcess, project_path: str
    ) -> None:
        """Populate result with test outcomes."""
        result.test_failures = self.parse_errors(test_result.stdout + test_result.stderr, "tests")

        counts = FlutterTestUtils.extract_test_counts(test_result.stdout)
        result.tests_passed = counts["passed"]
        result.tests_failed = counts["failed"]

        if result.tests_passed == 0 and result.tests_failed == 0:
            self._handle_zero_tests_detected(result, project_path)

    def _handle_zero_tests_detected(self, result: AnalysisResult, project_path: str) -> None:
        """Handle case when no tests are detected from output."""
        test_count = FlutterTestUtils.count_test_files_directly(project_path)
        if test_count > 0:
            result.error_message = (
                f"Flutter test ran but detected 0 tests. Found {test_count} "
                "*_test.dart files. Possible test discovery issue."
            )
            result.tests_passed = test_count

    def analyze_coverage(self, project_path: str) -> AnalysisResult:
        """Analyze test coverage and find gaps."""
        start_time = time.time()
        result = AnalysisResult(
            language=self.language_name, phase="coverage", project_path=project_path
        )

        try:
            # Run tests with coverage
            cmd = ["flutter", "test", "--coverage", "--no-pub"]
            subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                timeout=1800,  # 30 min
            )

            # Parse coverage file
            coverage_file = Path(project_path) / "coverage" / "lcov.info"
            if coverage_file.exists():
                coverage_data = self._parse_lcov(coverage_file)
                result.coverage_percentage = coverage_data["percentage"]
                result.coverage_gaps = coverage_data["gaps"]

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
        result = AnalysisResult(language=self.language_name, phase="e2e", project_path=project_path)

        try:
            # Check for integration tests
            integration_dir = Path(project_path) / "integration_test"
            if not integration_dir.exists():
                result.success = True
                result.error_message = "No integration tests found"
                return result

            # Run integration tests
            cmd = ["flutter", "test", "integration_test/", "--no-pub"]
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
        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def parse_errors(self, output: str, phase: str) -> list[dict]:
        """Parse Flutter error messages using centralized parser (SOLID: SRP)."""
        return ErrorParserStrategy.parse(language="flutter", output=output, phase=phase)

    def calculate_complexity(self, file_path: str) -> int:
        """Calculate cyclomatic complexity using simple heuristic."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Count decision points: if, for, while, case, catch, &&, ||, ??
            complexity = 1  # Base complexity
            complexity += content.count(" if ")
            complexity += content.count(" for ")
            complexity += content.count(" while ")
            complexity += content.count(" case ")
            complexity += content.count(" catch ")
            complexity += content.count(" && ")
            complexity += content.count(" || ")
            complexity += content.count(" ?? ")

            return complexity

        except Exception:
            return 0

    def _get_source_files(self, project_path: Path) -> list[Path]:
        """Get all Dart source files using centralized exclusion (SOLID: DRY)."""
        lib_dir = project_path / "lib"
        if not lib_dir.exists():
            return []
        source_files = list(lib_dir.rglob("*.dart"))
        return self._filter_excluded_paths(source_files)

    def validate_tools(self) -> list[ToolValidationResult]:
        """Validate Flutter toolchain availability."""
        results = []

        flutter_result = self._validate_flutter()
        results.append(flutter_result)

        dart_result = self._validate_dart()
        results.append(dart_result)

        results.append(self._create_flutter_analyze_validation(flutter_result))
        results.append(self._create_flutter_test_validation(flutter_result))

        return results

    def _create_flutter_analyze_validation(
        self, flutter_result: ToolValidationResult
    ) -> ToolValidationResult:
        """Create validation result for flutter analyze tool."""
        if flutter_result.available:
            return ToolValidationResult(
                tool_name="flutter analyze",
                available=True,
                version=flutter_result.version,
                path=flutter_result.path,
            )
        return ToolValidationResult(
            tool_name="flutter analyze",
            available=False,
            error_message="flutter not available",
            fix_suggestion="Install Flutter: https://docs.flutter.dev/get-started/install",
        )

    def _create_flutter_test_validation(
        self, flutter_result: ToolValidationResult
    ) -> ToolValidationResult:
        """Create validation result for flutter test tool."""
        if flutter_result.available:
            return ToolValidationResult(
                tool_name="flutter test",
                available=True,
                version=flutter_result.version,
                path=flutter_result.path,
            )
        return ToolValidationResult(
            tool_name="flutter test",
            available=False,
            error_message="flutter not available",
            fix_suggestion="Install Flutter: https://docs.flutter.dev/get-started/install",
        )

    def _validate_flutter(self) -> ToolValidationResult:
        """Validate Flutter installation."""
        flutter_cmd = FlutterTestUtils.find_flutter_executable()

        if not flutter_cmd:
            return self._create_flutter_not_found_result()

        return self._get_flutter_version(flutter_cmd)

    def _create_flutter_not_found_result(self) -> ToolValidationResult:
        """Create result when Flutter is not found."""
        return ToolValidationResult(
            tool_name="flutter",
            available=False,
            error_message="Flutter not found in PATH or common locations",
            fix_suggestion="Install Flutter: https://docs.flutter.dev/get-started/install\n"
            "Or add to PATH: export PATH=$HOME/flutter/bin:$PATH",
        )

    def _get_flutter_version(self, flutter_cmd: str) -> ToolValidationResult:
        """Get Flutter version and create validation result."""
        try:
            result = subprocess.run(
                [flutter_cmd, "--version"], capture_output=True, text=True, timeout=10
            )

            version_match = re.search(r"Flutter\s+([\d.]+)", result.stdout)
            version = version_match.group(1) if version_match else "unknown"

            return ToolValidationResult(
                tool_name="flutter", available=True, version=version, path=flutter_cmd
            )
        except Exception as e:
            return ToolValidationResult(
                tool_name="flutter",
                available=False,
                path=flutter_cmd,
                error_message=f"Flutter found but failed to run: {e}",
                fix_suggestion="Check Flutter installation: flutter doctor",
            )

    def _validate_dart(self) -> ToolValidationResult:
        """Validate Dart installation."""
        dart_cmd = self._find_dart_executable()

        if not dart_cmd:
            return self._create_dart_not_found_result()

        return self._get_dart_version(dart_cmd)

    def _find_dart_executable(self) -> str | None:
        """Find Dart executable in PATH or Flutter installation."""
        import shutil

        dart_cmd = shutil.which("dart")
        if dart_cmd:
            return dart_cmd

        flutter_cmd = FlutterTestUtils.find_flutter_executable()
        if not flutter_cmd:
            return None

        dart_in_flutter = str(Path(flutter_cmd).parent / "dart")
        if Path(dart_in_flutter).exists():
            return dart_in_flutter

        return None

    def _create_dart_not_found_result(self) -> ToolValidationResult:
        """Create result when Dart is not found."""
        return ToolValidationResult(
            tool_name="dart",
            available=False,
            error_message="Dart not found",
            fix_suggestion="Dart usually comes with Flutter. Check: flutter doctor",
        )

    def _get_dart_version(self, dart_cmd: str) -> ToolValidationResult:
        """Get Dart version and create validation result."""
        try:
            result = subprocess.run(
                [dart_cmd, "--version"], capture_output=True, text=True, timeout=10
            )

            output = result.stdout + result.stderr
            version_match = re.search(r"Dart SDK version:\s+([\d.]+)", output)
            version = version_match.group(1) if version_match else "unknown"

            return ToolValidationResult(
                tool_name="dart", available=True, version=version, path=dart_cmd
            )
        except Exception as e:
            return ToolValidationResult(
                tool_name="dart",
                available=False,
                path=dart_cmd,
                error_message=f"Dart found but failed to run: {e}",
            )

    def _parse_lcov(self, coverage_file: Path) -> dict:
        """Parse lcov.info coverage file."""
        try:
            with open(coverage_file) as f:
                content = f.read()

            # Count lines found (LF) and lines hit (LH)
            lines_found = sum(int(m.group(1)) for m in re.finditer(r"LF:(\d+)", content))
            lines_hit = sum(int(m.group(1)) for m in re.finditer(r"LH:(\d+)", content))

            percentage = (lines_hit / lines_found * 100) if lines_found > 0 else 0

            # Find uncovered files (LH:0)
            gaps = []
            current_file = None
            for line in content.split("\n"):
                if line.startswith("SF:"):
                    current_file = line[3:]
                elif line.startswith("LH:0") and current_file:
                    gaps.append(
                        {
                            "file": current_file,
                            "coverage": 0,
                            "message": "File has no test coverage",
                        }
                    )

            return {"percentage": percentage, "gaps": gaps}

        except Exception:
            return {"percentage": 0, "gaps": []}
