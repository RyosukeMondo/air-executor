"""Python language adapter - orchestrates sub-components."""

from typing import Dict, List

from ....domain.models import AnalysisResult, ToolValidationResult
from ..base import LanguageAdapter
from .detector import PythonProjectDetector
from .static_analyzer import PythonStaticAnalyzer
from .test_runner import PythonTestRunner
from .tool_validator import PythonToolValidator


class PythonAdapter(LanguageAdapter):
    """
    Python language adapter - THIN ORCHESTRATOR.

    Delegates to focused sub-components:
    - PythonProjectDetector: Find Python projects
    - PythonStaticAnalyzer: Run linters, check complexity
    - PythonTestRunner: Run pytest, coverage, E2E
    - PythonToolValidator: Validate toolchain
    """

    def __init__(self, config: Dict):
        super().__init__(config)

        # Initialize sub-components (SRP: each has one job)
        self.detector = PythonProjectDetector()
        self.static_analyzer = PythonStaticAnalyzer(config)
        self.test_runner = PythonTestRunner(config)
        self.tool_validator = PythonToolValidator(config)

    @property
    def language_name(self) -> str:
        """Name of the language this adapter handles."""
        return "python"

    @property
    def project_markers(self) -> List[str]:
        """Files that indicate a Python project."""
        return self.detector.project_markers

    def detect_projects(self, root_path: str) -> List[str]:
        """
        Find all Python projects in a directory tree.

        Delegates to: PythonProjectDetector
        """
        return self.detector.detect_projects(root_path)

    def static_analysis(self, project_path: str) -> AnalysisResult:
        """
        Run static analysis (linting, complexity, file sizes).

        Delegates to: PythonStaticAnalyzer
        """
        return self.static_analyzer.analyze(project_path)

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """
        Run tests with specified strategy.

        Delegates to: PythonTestRunner
        """
        return self.test_runner.run_tests(project_path, strategy)

    def analyze_coverage(self, project_path: str) -> AnalysisResult:
        """
        Analyze test coverage.

        Delegates to: PythonTestRunner
        """
        return self.test_runner.analyze_coverage(project_path)

    def run_e2e_tests(self, project_path: str) -> AnalysisResult:
        """
        Run E2E tests.

        Delegates to: PythonTestRunner
        """
        return self.test_runner.run_e2e_tests(project_path)

    def validate_tools(self) -> List[ToolValidationResult]:
        """
        Validate Python toolchain.

        Delegates to: PythonToolValidator
        """
        return self.tool_validator.validate_tools()

    def parse_errors(self, output: str, phase: str) -> List[Dict]:
        """
        Parse Python error messages.

        Args:
            output: Command output
            phase: 'static' | 'tests' | 'coverage' | 'e2e'

        Returns:
            List of error dictionaries
        """
        if phase == 'static':
            # Already parsed by static_analyzer
            return []
        elif phase in ('tests', 'e2e'):
            # Delegate to test_runner
            return self.test_runner._parse_errors(output)
        else:
            return []

    def calculate_complexity(self, file_path: str) -> int:
        """
        Calculate cyclomatic complexity for a file.

        Delegates to: PythonStaticAnalyzer
        """
        return self.static_analyzer._calculate_complexity(file_path)

    def _get_source_files(self, project_path):
        """Get Python source files (for base class compatibility)."""
        from pathlib import Path
        return self.detector.get_source_files(Path(project_path))
