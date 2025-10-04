"""Language adapter interface."""

from abc import ABC, abstractmethod
from typing import List

from ..models import AnalysisResult, ToolValidationResult


class ILanguageAdapter(ABC):
    """
    Interface for language-specific analysis and operations.

    Each language adapter implements this interface to provide:
    - Project detection
    - Static analysis
    - Test execution
    - Coverage analysis
    - E2E testing
    - Tool validation
    """

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Name of the language this adapter handles."""
        pass

    @property
    @abstractmethod
    def project_markers(self) -> List[str]:
        """Files that indicate a project of this language."""
        pass

    @abstractmethod
    def detect_projects(self, root_path: str) -> List[str]:
        """
        Find all projects of this language in a monorepo.

        Args:
            root_path: Root directory to search

        Returns:
            List of project paths
        """
        pass

    @abstractmethod
    def static_analysis(self, project_path: str) -> AnalysisResult:
        """
        Run fast static analysis (linting, complexity, file sizes).

        Args:
            project_path: Path to project

        Returns:
            AnalysisResult with static analysis data
        """
        pass

    @abstractmethod
    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """
        Run tests with specified strategy.

        Args:
            project_path: Path to project
            strategy: 'minimal' | 'selective' | 'comprehensive'

        Returns:
            AnalysisResult with test results
        """
        pass

    @abstractmethod
    def analyze_coverage(self, project_path: str) -> AnalysisResult:
        """
        Analyze test coverage.

        Args:
            project_path: Path to project

        Returns:
            AnalysisResult with coverage data
        """
        pass

    @abstractmethod
    def run_e2e_tests(self, project_path: str) -> AnalysisResult:
        """
        Run end-to-end tests.

        Args:
            project_path: Path to project

        Returns:
            AnalysisResult with E2E test results
        """
        pass

    @abstractmethod
    def validate_tools(self) -> List[ToolValidationResult]:
        """
        Validate all required tools are available.

        Returns:
            List of ToolValidationResult for each tool
        """
        pass

    @abstractmethod
    def parse_errors(self, output: str, phase: str) -> List[dict]:
        """
        Parse language-specific error format.

        Args:
            output: Command output
            phase: 'static' | 'tests' | 'coverage' | 'e2e'

        Returns:
            List of error dictionaries
        """
        pass

    @abstractmethod
    def calculate_complexity(self, file_path: str) -> int:
        """
        Calculate cyclomatic complexity for a file.

        Args:
            file_path: Path to file

        Returns:
            Maximum complexity found in the file
        """
        pass
