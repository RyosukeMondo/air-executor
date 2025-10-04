"""Unit tests for OrchestratorCLI and OrchestratorResult."""

from unittest.mock import Mock, patch

import pytest

from airflow_dags.autonomous_fixing.cli import OrchestratorCLI
from airflow_dags.autonomous_fixing.config import OrchestratorConfig
from airflow_dags.autonomous_fixing.domain.models import OrchestratorResult


class TestOrchestratorResult:
    """Test OrchestratorResult dataclass."""

    def test_result_creation_minimal(self):
        """Test creating result with minimal required fields."""
        result = OrchestratorResult(
            success=True, exit_code=0, iterations_completed=3, final_health_score=85.5
        )

        assert result.success is True
        assert result.exit_code == 0
        assert result.iterations_completed == 3
        assert result.final_health_score == 85.5
        assert result.errors == []
        assert result.warnings == []
        assert result.metrics == {}
        assert result.duration_seconds == 0.0

    def test_result_creation_full(self):
        """Test creating result with all fields populated."""
        result = OrchestratorResult(
            success=False,
            exit_code=1,
            iterations_completed=2,
            final_health_score=45.0,
            errors=["Missing tools", "Build failed"],
            warnings=["No tests found"],
            metrics={"cache_hits": 5, "projects_analyzed": 2},
            duration_seconds=12.5,
        )

        assert result.success is False
        assert result.exit_code == 1
        assert result.iterations_completed == 2
        assert result.final_health_score == 45.0
        assert result.errors == ["Missing tools", "Build failed"]
        assert result.warnings == ["No tests found"]
        assert result.metrics == {"cache_hits": 5, "projects_analyzed": 2}
        assert result.duration_seconds == 12.5

    def test_result_immutable_after_creation(self):
        """Test that result fields can be modified (dataclass is not frozen)."""
        result = OrchestratorResult(
            success=True, exit_code=0, iterations_completed=1, final_health_score=90.0
        )

        # Dataclass allows modification (not frozen)
        result.success = False
        assert result.success is False


class TestOrchestratorCLI:
    """Test OrchestratorCLI programmatic interface."""

    def test_run_with_config_object(self, tmp_path):
        """Test run() with OrchestratorConfig object."""
        config = OrchestratorConfig.for_testing(tmp_path)

        with patch(
            "airflow_dags.autonomous_fixing.cli.orchestrator_cli.MultiLanguageOrchestrator"
        ) as mock_orch_class:
            mock_orch = Mock()
            mock_orch_class.return_value = mock_orch
            mock_orch.execute.return_value = {
                "success": True,
                "iterations_completed": 2,
                "final_health_score": 88.0,
            }

            result = OrchestratorCLI.run(config)

            assert isinstance(result, OrchestratorResult)
            assert result.success is True
            assert result.exit_code == 0
            assert result.iterations_completed == 2
            assert result.final_health_score == 88.0
            assert result.duration_seconds > 0

    def test_run_with_yaml_path(self, tmp_path):
        """Test run() with Path to YAML config."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(
            """
projects:
  - /tmp/test-project
languages:
  enabled: [python]
"""
        )

        with (
            patch(
                "airflow_dags.autonomous_fixing.cli.orchestrator_cli.OrchestratorConfig.from_yaml"
            ) as mock_from_yaml,
            patch(
                "airflow_dags.autonomous_fixing.cli.orchestrator_cli.MultiLanguageOrchestrator"
            ) as mock_orch_class,
        ):
            mock_config = OrchestratorConfig.for_testing(tmp_path)
            mock_from_yaml.return_value = mock_config

            mock_orch = Mock()
            mock_orch_class.return_value = mock_orch
            mock_orch.execute.return_value = {"success": True, "iterations_completed": 1}

            result = OrchestratorCLI.run(config_file)

            mock_from_yaml.assert_called_once_with(config_file)
            assert result.success is True

    def test_run_with_overrides(self, tmp_path):
        """Test run() with config overrides."""
        config = OrchestratorConfig.for_testing(tmp_path)
        config.redis_host = "original"

        with patch(
            "airflow_dags.autonomous_fixing.cli.orchestrator_cli.MultiLanguageOrchestrator"
        ) as mock_orch_class:
            mock_orch = Mock()
            mock_orch_class.return_value = mock_orch
            mock_orch.execute.return_value = {"success": True}

            OrchestratorCLI.run(config, redis_host="overridden", verbose=True)

            # Verify config was modified
            assert config.redis_host == "overridden"

    def test_run_from_yaml_convenience_method(self, tmp_path):
        """Test run_from_yaml() convenience method."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("projects: []\nlanguages:\n  enabled: [python]")

        with patch(
            "airflow_dags.autonomous_fixing.cli.orchestrator_cli.OrchestratorCLI.run"
        ) as mock_run:
            mock_run.return_value = OrchestratorResult(
                success=True, exit_code=0, iterations_completed=0, final_health_score=0.0
            )

            result = OrchestratorCLI.run_from_yaml(config_file, redis_host="test")

            mock_run.assert_called_once_with(config_file, redis_host="test")
            assert result.success is True

    def test_convert_to_result_success_case(self):
        """Test _convert_to_result with successful execution."""
        raw = {
            "success": True,
            "iterations_completed": 3,
            "final_health_score": 92.5,
            "reason": "all_gates_passed",
        }

        result = OrchestratorCLI._convert_to_result(raw, duration=5.2)

        assert result.success is True
        assert result.exit_code == 0
        assert result.iterations_completed == 3
        assert result.final_health_score == 92.5
        assert result.duration_seconds == 5.2
        assert result.errors == []
        assert "reason" in result.metrics

    def test_convert_to_result_failure_case(self):
        """Test _convert_to_result with failed execution."""
        raw = {
            "success": False,
            "error": "Missing critical tools",
            "iterations_completed": 0,
        }

        result = OrchestratorCLI._convert_to_result(raw, duration=0.5)

        assert result.success is False
        assert result.exit_code == 1
        assert result.errors == ["Missing critical tools"]
        assert result.iterations_completed == 0

    def test_convert_to_result_health_score_fallback(self):
        """Test _convert_to_result uses health_score as fallback."""
        raw = {"success": True, "iterations_completed": 1, "health_score": 75.0}

        result = OrchestratorCLI._convert_to_result(raw, duration=1.0)

        assert result.final_health_score == 75.0

    def test_convert_to_result_validation_errors(self):
        """Test _convert_to_result extracts validation errors."""

        class MockValidation:
            errors = ["Tool A missing", "Tool B not found"]
            warnings = ["Tool C is old"]

        raw = {
            "success": False,
            "error": "Validation failed",
            "validation": MockValidation(),
        }

        result = OrchestratorCLI._convert_to_result(raw, duration=0.1)

        assert result.errors == ["Validation failed", "Tool A missing", "Tool B not found"]
        assert result.warnings == ["Tool C is old"]

    def test_convert_to_result_metrics_extraction(self):
        """Test _convert_to_result extracts metrics correctly."""
        raw = {
            "success": True,
            "iterations_completed": 2,
            "final_health_score": 80.0,
            "cache_hits": 10,
            "projects_processed": 3,
            "total_fixes": 15,
        }

        result = OrchestratorCLI._convert_to_result(raw, duration=10.0)

        assert result.metrics["cache_hits"] == 10
        assert result.metrics["projects_processed"] == 3
        assert result.metrics["total_fixes"] == 15
        assert "iterations_completed" not in result.metrics  # excluded field
        assert "final_health_score" not in result.metrics  # excluded field

    def test_run_measures_duration(self, tmp_path):
        """Test that run() measures execution duration."""
        config = OrchestratorConfig.for_testing(tmp_path)

        with (
            patch(
                "airflow_dags.autonomous_fixing.cli.orchestrator_cli.MultiLanguageOrchestrator"
            ) as mock_orch_class,
            patch("airflow_dags.autonomous_fixing.cli.orchestrator_cli.time.time") as mock_time,
        ):
            mock_time.side_effect = [100.0, 105.5]  # start, end

            mock_orch = Mock()
            mock_orch_class.return_value = mock_orch
            mock_orch.execute.return_value = {"success": True}

            result = OrchestratorCLI.run(config)

            assert result.duration_seconds == 5.5

    def test_run_handles_exception_gracefully(self, tmp_path):
        """Test run() handles orchestrator exceptions."""
        config = OrchestratorConfig.for_testing(tmp_path)

        with patch(
            "airflow_dags.autonomous_fixing.cli.orchestrator_cli.MultiLanguageOrchestrator"
        ) as mock_orch_class:
            mock_orch = Mock()
            mock_orch_class.return_value = mock_orch
            mock_orch.execute.side_effect = RuntimeError("Orchestrator failed")

            with pytest.raises(RuntimeError, match="Orchestrator failed"):
                OrchestratorCLI.run(config)
