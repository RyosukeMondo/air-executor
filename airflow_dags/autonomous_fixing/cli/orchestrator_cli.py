"""Programmatic CLI interface for orchestrator.

This module provides an in-process interface to the orchestrator,
enabling fast E2E tests without subprocess overhead.
"""

import time
from pathlib import Path
from typing import Union

from airflow_dags.autonomous_fixing.config import OrchestratorConfig
from airflow_dags.autonomous_fixing.domain.models import OrchestratorResult
from airflow_dags.autonomous_fixing.multi_language_orchestrator import (
    MultiLanguageOrchestrator,
)


class OrchestratorCLI:
    """Programmatic interface to orchestrator.

    Enables running the orchestrator in-process with structured result objects,
    replacing subprocess.run() and exit codes with direct method calls.

    Example:
        >>> config = OrchestratorConfig.for_testing(tmp_path)
        >>> result = OrchestratorCLI.run(config)
        >>> assert result.success
        >>> print(f"Score: {result.final_health_score}")
    """

    @staticmethod
    def run(config: Union[Path, OrchestratorConfig], **overrides) -> OrchestratorResult:
        """Run orchestrator in-process.

        Args:
            config: Either path to YAML config or OrchestratorConfig object
            **overrides: Override config parameters (e.g., redis_host="localhost")

        Returns:
            OrchestratorResult with success status, errors, metrics, etc.

        Example:
            >>> result = OrchestratorCLI.run(
            ...     config_path,
            ...     redis_host="localhost",
            ...     verbose=True
            ... )
        """
        start_time = time.time()

        # Load config from YAML if path provided
        if isinstance(config, Path):
            config = OrchestratorConfig.from_yaml(config)

        # Apply overrides
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)

        # Create orchestrator
        orchestrator = MultiLanguageOrchestrator(config)

        # Execute and capture result
        raw_result = orchestrator.execute()

        # Convert to structured result
        duration = time.time() - start_time
        return OrchestratorCLI._convert_to_result(raw_result, duration)

    @staticmethod
    def run_from_yaml(config_path: Path, **overrides) -> OrchestratorResult:
        """Convenience method for YAML configs.

        Args:
            config_path: Path to YAML configuration file
            **overrides: Override config parameters

        Returns:
            OrchestratorResult with execution details

        Example:
            >>> result = OrchestratorCLI.run_from_yaml(
            ...     Path("config/local.yaml"),
            ...     redis_host="localhost"
            ... )
        """
        return OrchestratorCLI.run(config_path, **overrides)

    @staticmethod
    def _convert_to_result(raw_result: dict, duration: float) -> OrchestratorResult:
        """Convert raw orchestrator dict result to OrchestratorResult.

        Args:
            raw_result: Dict returned by MultiLanguageOrchestrator.execute()
            duration: Execution time in seconds

        Returns:
            Structured OrchestratorResult object
        """
        success = raw_result.get("success", False)
        iterations = raw_result.get("iterations_completed", 0)

        # Extract health score
        final_score = 0.0
        if "final_health_score" in raw_result:
            final_score = raw_result["final_health_score"]
        elif "health_score" in raw_result:
            final_score = raw_result["health_score"]

        # Extract errors and warnings
        errors = []
        warnings = []

        if "error" in raw_result:
            errors.append(raw_result["error"])

        if "validation" in raw_result:
            validation = raw_result["validation"]
            if hasattr(validation, "errors"):
                errors.extend(validation.errors)
            if hasattr(validation, "warnings"):
                warnings.extend(validation.warnings)

        # Build metrics dict from remaining fields
        metrics = {
            k: v
            for k, v in raw_result.items()
            if k
            not in {
                "success",
                "iterations_completed",
                "final_health_score",
                "health_score",
                "error",
                "validation",
            }
        }

        # Determine exit code
        exit_code = 0 if success else 1

        return OrchestratorResult(
            success=success,
            exit_code=exit_code,
            iterations_completed=iterations,
            final_health_score=final_score,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            duration_seconds=duration,
        )
