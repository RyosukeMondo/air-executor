"""
Core autonomous fixing modules with clear separation of concerns.

Following SOLID principles:
- Single Responsibility: Each module has ONE job
- Open/Closed: Easy to extend without modifying
- Dependency Inversion: Depend on abstractions (language adapters)
"""

from .analysis_verifier import AnalysisVerifier
from .analyzer import ProjectAnalyzer
from .fixer import IssueFixer
from .iteration_engine import IterationEngine
from .scorer import HealthScorer
from .tool_validator import ToolValidator

__all__ = [
    "AnalysisVerifier",
    "HealthScorer",
    "IssueFixer",
    "IterationEngine",
    "ProjectAnalyzer",
    "ToolValidator",
]
