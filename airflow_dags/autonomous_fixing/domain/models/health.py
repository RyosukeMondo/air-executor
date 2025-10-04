"""Health metrics models."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class StaticMetrics:
    """Static analysis metrics (fast checks: linting, complexity, file sizes)."""
    analysis_status: str  # 'pass' | 'fail'
    analysis_errors: int
    analysis_warnings: int
    file_size_violations: int
    complexity_violations: int
    static_health_score: float  # 0.0 - 1.0

    def passes_static(self) -> bool:
        """Check if static analysis passes."""
        return self.analysis_status == 'pass' and self.analysis_errors == 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'analysis_status': self.analysis_status,
            'analysis_errors': self.analysis_errors,
            'analysis_warnings': self.analysis_warnings,
            'file_size_violations': self.file_size_violations,
            'complexity_violations': self.complexity_violations,
            'static_health_score': self.static_health_score,
        }


@dataclass
class DynamicMetrics:
    """Dynamic runtime metrics (slower checks: tests, E2E, coverage)."""
    total_tests: int
    test_pass_rate: float  # 0.0 - 1.0
    coverage_percentage: float  # 0.0 - 100.0
    e2e_errors: int
    dynamic_health_score: float  # 0.0 - 1.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'total_tests': self.total_tests,
            'test_pass_rate': self.test_pass_rate,
            'coverage_percentage': self.coverage_percentage,
            'e2e_errors': self.e2e_errors,
            'dynamic_health_score': self.dynamic_health_score,
        }


@dataclass
class HealthMetrics:
    """
    Complete health metrics combining static and dynamic checks.

    Follows tiered checking strategy:
    - Always run static checks (fast)
    - Only run dynamic checks when needed (slow)
    """
    static: StaticMetrics
    dynamic: Optional[DynamicMetrics] = None
    overall_health_score: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'static': self.static.to_dict(),
            'dynamic': self.dynamic.to_dict() if self.dynamic else None,
            'overall_health_score': self.overall_health_score,
        }

    @staticmethod
    def from_dict(data: Dict) -> 'HealthMetrics':
        """Create from dictionary."""
        static = StaticMetrics(**data['static'])
        dynamic = DynamicMetrics(**data['dynamic']) if data.get('dynamic') else None
        return HealthMetrics(
            static=static,
            dynamic=dynamic,
            overall_health_score=data.get('overall_health_score', 0.0)
        )
