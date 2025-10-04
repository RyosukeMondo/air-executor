"""Orchestrator execution result model."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OrchestratorResult:
    """Structured result from orchestrator execution.

    This model provides a programmatic interface to orchestrator results,
    replacing exit codes and stdout parsing with structured data.
    """

    success: bool
    """Whether the orchestrator execution completed successfully."""

    exit_code: int
    """Exit code (0 for success, non-zero for errors)."""

    iterations_completed: int
    """Number of improvement iterations completed."""

    final_health_score: float
    """Final health score after all iterations (0.0-100.0)."""

    errors: list[str] = field(default_factory=list)
    """List of error messages encountered during execution."""

    warnings: list[str] = field(default_factory=list)
    """List of warning messages encountered during execution."""

    metrics: dict[str, Any] = field(default_factory=dict)
    """Additional metrics and execution details."""

    duration_seconds: float = 0.0
    """Total execution time in seconds."""
