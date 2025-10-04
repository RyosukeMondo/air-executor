"""Analysis result models - unified across all components."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..enums import Phase


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
    """
    Unified analysis result model used across all language adapters.

    Replaces multiple inconsistent result structures.
    Single Source of Truth for analysis data.
    """

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

    def compute_quality_check(self) -> bool:
        """
        Compute quality check based on phase.

        Quality check logic centralized in the model (Single Responsibility).
        All adapters delegate to this method instead of duplicating logic.

        Returns:
            True if quality check passes, False otherwise
        """
        if self.phase == str(Phase.STATIC):
            # Static analysis: no errors, size violations, or complexity violations
            return (
                len(self.errors) == 0
                and len(self.file_size_violations) == 0
                and len(self.complexity_violations) == 0
            )
        elif self.phase == str(Phase.TESTS):
            # Tests: no test failures
            return len(self.test_failures) == 0 and self.tests_failed == 0
        elif self.phase == str(Phase.COVERAGE):
            # Coverage: no significant gaps (can be customized)
            return len(self.coverage_gaps) == 0
        elif self.phase == str(Phase.E2E):
            # E2E: no runtime errors
            return len(self.runtime_errors) == 0
        else:
            # Unknown phase - default to error check
            return len(self.errors) == 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "language": self.language,
            "phase": self.phase,
            "project_path": self.project_path,
            "errors": self.errors,
            "complexity_violations": self.complexity_violations,
            "file_size_violations": self.file_size_violations,
            "test_failures": self.test_failures,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "coverage_gaps": self.coverage_gaps,
            "coverage_percentage": self.coverage_percentage,
            "runtime_errors": self.runtime_errors,
            "execution_time": self.execution_time,
            "success": self.success,
            "error_message": self.error_message,
        }

    @staticmethod
    def from_dict(data: Dict) -> "AnalysisResult":
        """Create from dictionary."""
        return AnalysisResult(**data)
