"""Unit tests for OrchestratorConfig.

Tests configuration loading, backward compatibility, and test helpers.
"""

from pathlib import Path

import pytest

from airflow_dags.autonomous_fixing.config import OrchestratorConfig


def test_orchestrator_config_defaults():
    """Test default configuration values."""
    config = OrchestratorConfig()

    # Verify defaults
    assert config.projects == []
    assert "enabled" in config.languages
    assert config.execution["parallel_languages"] is True
    assert config.execution["max_iterations"] == 50


def test_orchestrator_config_from_dict():
    """Test creating config from dictionary."""
    config_dict = {
        "projects": [{"path": "/tmp/test", "language": "python"}],
        "languages": {"enabled": ["python"]},
        "execution": {"max_iterations": 10},
    }

    config = OrchestratorConfig.from_dict(config_dict)

    assert config.projects == [{"path": "/tmp/test", "language": "python"}]
    assert config.languages == {"enabled": ["python"]}
    assert config.execution["max_iterations"] == 10


def test_orchestrator_config_to_dict():
    """Test converting config to dictionary."""
    config = OrchestratorConfig(
        projects=[{"path": "/tmp/test", "language": "python"}],
        languages={"enabled": ["python"]},
    )

    config_dict = config.to_dict()

    assert config_dict["projects"] == [{"path": "/tmp/test", "language": "python"}]
    assert config_dict["languages"] == {"enabled": ["python"]}
    assert "execution" in config_dict


def test_orchestrator_config_for_testing(tmp_path):
    """Test creating isolated test configuration."""
    config = OrchestratorConfig.for_testing(
        tmp_path, projects=[str(tmp_path / "project1")], languages=["python"]
    )

    # Verify test-friendly defaults
    assert len(config.projects) == 1
    assert config.projects[0]["path"] == str(tmp_path / "project1")
    assert config.projects[0]["language"] == "python"
    assert config.languages["enabled"] == ["python"]
    assert config.execution["parallel_languages"] is False  # Sequential for debugging
    assert config.execution["max_iterations"] == 5  # Fewer iterations
    assert config.execution["fail_fast"] is True  # Fast failure

    # Verify state isolation
    assert config.state_config.max_age_days == 1  # Fast staleness
    assert config.state_config.external_hook_cache_dir == tmp_path / "hook-cache"

    # Verify preflight isolation
    assert config.preflight_config.cache_max_age_days == 1


def test_orchestrator_config_for_testing_with_overrides(tmp_path):
    """Test for_testing() with custom overrides."""
    config = OrchestratorConfig.for_testing(
        tmp_path,
        projects=[str(tmp_path / "custom")],
        languages=["javascript", "python"],
    )

    assert len(config.projects) == 1
    assert config.projects[0]["language"] == "javascript"  # First language
    assert config.languages["enabled"] == ["javascript", "python"]


def test_orchestrator_config_from_yaml_not_found():
    """Test loading from non-existent YAML file."""
    with pytest.raises(FileNotFoundError):
        OrchestratorConfig.from_yaml(Path("/nonexistent/config.yaml"))


def test_orchestrator_config_sub_configs():
    """Test that sub-configs are properly initialized."""
    config = OrchestratorConfig()

    # Verify sub-configs exist
    assert config.state_config is not None
    assert config.preflight_config is not None

    # Verify default values
    assert config.state_config.state_dir_name == ".ai-state"
    assert config.preflight_config.state_dir_name == ".ai-state"
