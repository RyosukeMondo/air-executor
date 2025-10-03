"""Analysis result models - unified across all components."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


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

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'language': self.language,
            'phase': self.phase,
            'project_path': self.project_path,
            'errors': self.errors,
            'complexity_violations': self.complexity_violations,
            'file_size_violations': self.file_size_violations,
            'test_failures': self.test_failures,
            'tests_passed': self.tests_passed,
            'tests_failed': self.tests_failed,
            'coverage_gaps': self.coverage_gaps,
            'coverage_percentage': self.coverage_percentage,
            'runtime_errors': self.runtime_errors,
            'execution_time': self.execution_time,
            'success': self.success,
            'error_message': self.error_message,
        }

    @staticmethod
    def from_dict(data: Dict) -> 'AnalysisResult':
        """Create from dictionary."""
        return AnalysisResult(**data)
