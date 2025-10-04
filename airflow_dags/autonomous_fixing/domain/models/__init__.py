"""Domain models for autonomous fixing."""
from .analysis import AnalysisResult, ToolValidationResult
from .health import DynamicMetrics, HealthMetrics, StaticMetrics
from .tasks import FixResult, Task

__all__ = [
    'AnalysisResult',
    'ToolValidationResult',
    'HealthMetrics',
    'StaticMetrics',
    'DynamicMetrics',
    'Task',
    'FixResult',
]
