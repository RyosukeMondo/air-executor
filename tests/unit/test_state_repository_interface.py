"""Tests for IStateRepository interface and implementations."""

import pytest

from airflow_dags.autonomous_fixing.adapters.state import MemoryStateRepository
from airflow_dags.autonomous_fixing.core.state_manager import ProjectStateManager
from airflow_dags.autonomous_fixing.domain.interfaces.state_repository import (
    IStateRepository,
)


class TestIStateRepositoryInterface:
    """Test that implementations comply with IStateRepository interface."""

    def test_project_state_manager_implements_interface(self, tmp_path):
        """Test that ProjectStateManager implements IStateRepository."""
        manager = ProjectStateManager(tmp_path)
        assert isinstance(manager, IStateRepository)

    def test_memory_state_repository_implements_interface(self):
        """Test that MemoryStateRepository implements IStateRepository."""
        repo = MemoryStateRepository()
        assert isinstance(repo, IStateRepository)


class TestMemoryStateRepository:
    """Test MemoryStateRepository implementation."""

    @pytest.fixture
    def repo(self):
        """Create MemoryStateRepository."""
        return MemoryStateRepository()

    def test_should_reconfigure_no_state(self, repo):
        """Test should_reconfigure when no state exists."""
        should_reconfig, reason = repo.should_reconfigure("hooks")
        assert should_reconfig is True
        assert "no hooks state in memory" in reason

    def test_should_reconfigure_with_state(self, repo):
        """Test should_reconfigure when state exists."""
        repo.save_state("hooks", {"installed": True})

        should_reconfig, reason = repo.should_reconfigure("hooks")
        assert should_reconfig is False
        assert "cached in memory" in reason

    def test_save_state(self, repo):
        """Test save_state stores data."""
        data = {"installed": True, "repos": ["ruff"]}
        repo.save_state("hooks", data)

        # Verify state was saved
        should_reconfig, _ = repo.should_reconfigure("hooks")
        assert should_reconfig is False

    def test_get_state(self, repo):
        """Test get_state retrieves saved data."""
        data = {"installed": True, "repos": ["ruff", "mypy"]}
        repo.save_state("hooks", data)

        retrieved = repo.get_state("hooks")
        assert retrieved == data

    def test_get_state_missing(self, repo):
        """Test get_state returns None for missing state."""
        assert repo.get_state("hooks") is None

    def test_different_phases_separate(self, repo):
        """Test different phases have separate state."""
        repo.save_state("hooks", {"type": "hooks"})
        repo.save_state("tests", {"type": "tests"})

        hooks_state = repo.get_state("hooks")
        tests_state = repo.get_state("tests")

        assert hooks_state["type"] == "hooks"
        assert tests_state["type"] == "tests"

    def test_clear_state_single_phase(self, repo):
        """Test clearing state for single phase."""
        repo.save_state("hooks", {"data": "hooks"})
        repo.save_state("tests", {"data": "tests"})

        repo.clear_state("hooks")

        assert repo.get_state("hooks") is None
        assert repo.get_state("tests") is not None

    def test_clear_state_all(self, repo):
        """Test clearing all state."""
        repo.save_state("hooks", {"data": "hooks"})
        repo.save_state("tests", {"data": "tests"})

        repo.clear_state()

        assert repo.get_state("hooks") is None
        assert repo.get_state("tests") is None


class TestProjectStateManagerGetState:
    """Test get_state method on ProjectStateManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create ProjectStateManager with temp directory."""
        return ProjectStateManager(tmp_path)

    def test_get_state_after_save(self, manager):
        """Test get_state retrieves data after save_state."""
        data = {"installed": True, "repos": ["ruff", "mypy"]}
        manager.save_state("hooks", data)

        retrieved = manager.get_state("hooks")
        assert retrieved == data

    def test_get_state_missing(self, manager):
        """Test get_state returns None for missing state."""
        assert manager.get_state("hooks") is None

    def test_get_state_different_phases(self, manager):
        """Test get_state for different phases."""
        hooks_data = {"installed": True, "repos": ["ruff"]}
        tests_data = {"test_count": 42, "framework": "pytest"}

        manager.save_state("hooks", hooks_data)
        manager.save_state("tests", tests_data)

        assert manager.get_state("hooks") == hooks_data
        assert manager.get_state("tests") == tests_data

    def test_get_state_complex_data(self, manager):
        """Test get_state with complex nested data."""
        complex_data = {
            "repos": [{"repo": "ruff", "hooks": ["ruff"]}, {"repo": "mypy", "hooks": ["mypy"]}],
            "metadata": {"version": "1.0", "config_file": ".pre-commit-config.yaml"},
        }

        manager.save_state("hooks", complex_data)
        retrieved = manager.get_state("hooks")

        assert retrieved == complex_data


class TestInterfaceCompliance:
    """Test that both implementations have the same interface."""

    @pytest.fixture
    def memory_repo(self):
        """Create MemoryStateRepository."""
        return MemoryStateRepository()

    @pytest.fixture
    def filesystem_repo(self, tmp_path):
        """Create ProjectStateManager."""
        return ProjectStateManager(tmp_path)

    def test_both_have_should_reconfigure(self, memory_repo, filesystem_repo):
        """Test both implementations have should_reconfigure."""
        assert callable(memory_repo.should_reconfigure)
        assert callable(filesystem_repo.should_reconfigure)

    def test_both_have_save_state(self, memory_repo, filesystem_repo):
        """Test both implementations have save_state."""
        assert callable(memory_repo.save_state)
        assert callable(filesystem_repo.save_state)

    def test_both_have_get_state(self, memory_repo, filesystem_repo):
        """Test both implementations have get_state."""
        assert callable(memory_repo.get_state)
        assert callable(filesystem_repo.get_state)

    def test_save_and_get_consistency(self, memory_repo, filesystem_repo):
        """Test save and get work consistently across implementations."""
        data = {"test": "data"}

        # Memory repo
        memory_repo.save_state("hooks", data)
        assert memory_repo.get_state("hooks") == data

        # Filesystem repo
        filesystem_repo.save_state("hooks", data)
        assert filesystem_repo.get_state("hooks") == data
