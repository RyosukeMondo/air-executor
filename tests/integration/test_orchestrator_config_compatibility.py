"""Integration tests for OrchestratorConfig backward compatibility.

Tests that MultiLanguageOrchestrator works with both OrchestratorConfig
and dict configurations.
"""

from airflow_dags.autonomous_fixing.config import OrchestratorConfig
from airflow_dags.autonomous_fixing.multi_language_orchestrator import (
    MultiLanguageOrchestrator,
)


def test_orchestrator_accepts_orchestrator_config():
    """Test orchestrator accepts OrchestratorConfig object."""
    config = OrchestratorConfig(
        projects=[{"path": "/tmp/test", "language": "python"}],
        languages={"enabled": ["python"]},
    )

    # Should not raise
    orchestrator = MultiLanguageOrchestrator(config)

    # Verify config is properly set
    assert orchestrator.orchestrator_config is not None
    assert orchestrator.config is not None
    assert isinstance(orchestrator.config, dict)  # Internal dict for components


def test_orchestrator_accepts_dict_config():
    """Test orchestrator accepts dict config for backward compatibility."""
    config_dict = {
        "projects": [{"path": "/tmp/test", "language": "python"}],
        "languages": {"enabled": ["python"]},
    }

    # Should not raise
    orchestrator = MultiLanguageOrchestrator(config_dict)

    # Verify config is converted
    assert orchestrator.orchestrator_config is not None
    assert isinstance(orchestrator.orchestrator_config, OrchestratorConfig)
    assert orchestrator.config == config_dict


def test_orchestrator_config_roundtrip():
    """Test config can roundtrip through OrchestratorConfig."""
    original_dict = {
        "projects": [
            {"path": "/tmp/proj1", "language": "python"},
            {"path": "/tmp/proj2", "language": "javascript"},
        ],
        "languages": {
            "enabled": ["python", "javascript"],
            "auto_detect": False,
        },
        "execution": {
            "parallel_languages": True,
            "max_iterations": 10,
        },
    }

    # Convert to OrchestratorConfig and back
    config = OrchestratorConfig.from_dict(original_dict)
    roundtrip_dict = config.to_dict()

    # Verify critical fields preserved
    assert roundtrip_dict["projects"] == original_dict["projects"]
    assert roundtrip_dict["languages"] == original_dict["languages"]
    assert roundtrip_dict["execution"]["parallel_languages"] is True
    assert roundtrip_dict["execution"]["max_iterations"] == 10


def test_orchestrator_with_for_testing_config(tmp_path):
    """Test orchestrator works with for_testing() config."""
    config = OrchestratorConfig.for_testing(
        tmp_path, projects=[str(tmp_path / "test-project")], languages=["python"]
    )

    orchestrator = MultiLanguageOrchestrator(config)

    # Verify orchestrator is properly initialized
    assert orchestrator.orchestrator_config is not None
    assert orchestrator.config is not None
    assert "python" in orchestrator.adapters
