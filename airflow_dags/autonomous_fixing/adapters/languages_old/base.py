"""Base language adapter interface for multi-language support."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ToolValidationResult:
    """Result of tool validation check."""
    tool_name: str
    available: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error_message: Optional[str] = None
    fix_suggestion: Optional[str] = None


@dataclass
class AnalysisResult:
    """Result of language-specific analysis."""
    language: str
    phase: str  # 'static', 'tests', 'coverage', 'e2e'
    project_path: str

    # Static analysis results
    errors: List[Dict] = field(default_factory=list)
    complexity_violations: List[Dict] = field(default_factory=list)
    file_size_violations: List[Dict] = field(default_factory=list)

    # Test results
    test_failures: List[Dict] = field(default_factory=list)
    tests_passed: int = 0
    tests_failed: int = 0

    # Coverage results
    coverage_gaps: List[Dict] = field(default_factory=list)
    coverage_percentage: float = 0.0

    # E2E results
    runtime_errors: List[Dict] = field(default_factory=list)

    # Metadata
    execution_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


class LanguageAdapter(ABC):
    """Base class for language-specific analysis and fixing."""

    def __init__(self, config: Dict):
        self.config = config
        self.complexity_threshold = config.get('complexity_threshold', 10)
        self.max_file_lines = config.get('max_file_lines', 500)

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Name of the language this adapter handles."""
        pass

    @property
    @abstractmethod
    def project_markers(self) -> List[str]:
        """Files that indicate a project of this language (e.g., 'package.json')."""
        pass

    @abstractmethod
    def detect_projects(self, root_path: str) -> List[str]:
        """
        Find all projects of this language in a monorepo.

        Returns:
            List of project paths
        """
        pass

    @abstractmethod
    def static_analysis(self, project_path: str) -> AnalysisResult:
        """
        Priority 1: Fast static analysis.

        Checks:
        - Compilation/analysis errors
        - File size violations
        - Cyclomatic complexity
        - Code smells

        Should complete in ~30 seconds.
        """
        pass

    @abstractmethod
    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """
        Priority 2: Run tests with strategy.

        Args:
            strategy: 'minimal' | 'selective' | 'comprehensive'
                - minimal: Only critical tests (5 min, health < 30%)
                - selective: Changed files + smoke tests (15 min, health 30-60%)
                - comprehensive: Full test suite (30 min, health > 60%)

        Returns:
            Analysis result with test failures and pass/fail counts
        """
        pass

    @abstractmethod
    def analyze_coverage(self, project_path: str) -> AnalysisResult:
        """
        Priority 3: Analyze test coverage gaps.

        Only runs if:
        - P1 score >= 90%
        - P2 score >= 85%

        Returns:
            Analysis result with coverage gaps (uncovered functions/classes)
        """
        pass

    @abstractmethod
    def run_e2e_tests(self, project_path: str) -> AnalysisResult:
        """
        Priority 4: Run E2E tests and capture runtime errors.

        Only runs if overall health >= 90%.

        Steps:
        1. Start application/server
        2. Run E2E test suite
        3. Capture runtime errors
        4. Return errors for fixing

        Returns:
            Analysis result with runtime errors
        """
        pass

    @abstractmethod
    def parse_errors(self, output: str, phase: str) -> List[Dict]:
        """
        Parse language-specific error format.

        Args:
            output: Command output (stderr/stdout)
            phase: 'static' | 'tests' | 'coverage' | 'e2e'

        Returns:
            List of error dictionaries with:
                - file: path to file
                - line: line number
                - column: column number (if available)
                - severity: 'error' | 'warning' | 'info'
                - message: error message
                - code: error code (if available)
        """
        pass

    @abstractmethod
    def calculate_complexity(self, file_path: str) -> int:
        """
        Calculate cyclomatic complexity for a file.

        Returns:
            Maximum complexity found in the file
        """
        pass

    def check_file_sizes(self, project_path: str) -> List[Dict]:
        """
        Check for files exceeding max_file_lines threshold.

        Returns:
            List of violations:
                - file: path to file
                - lines: number of lines
                - threshold: max allowed lines
        """
        violations = []
        project = Path(project_path)

        for file_path in self._get_source_files(project):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)

                if line_count > self.max_file_lines:
                    violations.append({
                        'file': str(file_path),
                        'lines': line_count,
                        'threshold': self.max_file_lines,
                        'message': f'File has {line_count} lines (max: {self.max_file_lines})'
                    })
            except Exception:
                continue

        return violations

    @abstractmethod
    def _get_source_files(self, project_path: Path) -> List[Path]:
        """Get list of source files for this language."""
        pass

    @abstractmethod
    def validate_tools(self) -> List[ToolValidationResult]:
        """
        Validate all required tools are available.

        Called before running any analysis to detect issues early.

        Returns:
            List of ToolValidationResult for each required tool:
            - Static analysis tools (linters, type checkers)
            - Test runners
            - Coverage tools
            - Build tools

        Example for Flutter:
            [
                ToolValidationResult(
                    tool_name='flutter',
                    available=True,
                    version='3.16.0',
                    path='/home/user/flutter/bin/flutter'
                ),
                ToolValidationResult(
                    tool_name='dart',
                    available=True,
                    version='3.2.0',
                    path='/home/user/flutter/bin/dart'
                )
            ]
        """
        pass

    def get_test_strategy_description(self, strategy: str) -> str:
        """Get human-readable description of test strategy."""
        descriptions = {
            'minimal': 'Running minimal tests (critical path only, ~5 min)',
            'selective': 'Running selective tests (changed files + smoke tests, ~15 min)',
            'comprehensive': 'Running comprehensive tests (full suite, ~30 min)'
        }
        return descriptions.get(strategy, strategy)
