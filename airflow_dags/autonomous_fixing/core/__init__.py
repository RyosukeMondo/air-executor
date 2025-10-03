"""
Core autonomous fixing modules with clear separation of concerns.

Following SOLID principles:
- Single Responsibility: Each module has ONE job
- Open/Closed: Easy to extend without modifying
- Dependency Inversion: Depend on abstractions (language adapters)
"""

from .analyzer import ProjectAnalyzer
from .fixer import IssueFixer
from .scorer import HealthScorer
from .iteration_engine import IterationEngine
from .analysis_verifier import AnalysisVerifier
from .tool_validator import ToolValidator

__all__ = [
    'ProjectAnalyzer',
    'IssueFixer',
    'HealthScorer',
    'IterationEngine',
    'AnalysisVerifier',
    'ToolValidator'
]
