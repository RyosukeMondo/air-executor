"""
Tests for ISetupTracker interface compliance.

Validates that both SetupTracker and MemorySetupTracker properly implement
the ISetupTracker interface and provide consistent behavior.
"""

from unittest.mock import MagicMock

import pytest

from airflow_dags.autonomous_fixing.adapters.tracking.memory_setup_tracker import (
    MemorySetupTracker,
)
from airflow_dags.autonomous_fixing.config.setup_tracker_config import SetupTrackerConfig
from airflow_dags.autonomous_fixing.core.setup_tracker import SetupTracker
from airflow_dags.autonomous_fixing.domain.interfaces.setup_tracker import ISetupTracker


class TestISetupTrackerInterface:
    """Test that implementations properly implement ISetupTracker interface."""

    def test_setup_tracker_implements_interface(self):
        """SetupTracker should implement ISetupTracker interface."""
        assert issubclass(SetupTracker, ISetupTracker)

    def test_memory_setup_tracker_implements_interface(self):
        """MemorySetupTracker should implement ISetupTracker interface."""
        assert issubclass(MemorySetupTracker, ISetupTracker)


class TestMemorySetupTracker:
    """Test MemorySetupTracker in-memory implementation."""

    @pytest.fixture
    def tracker(self):
        """Create fresh MemorySetupTracker for each test."""
        return MemorySetupTracker()

    def test_initial_state_empty(self, tracker):
        """New tracker should have no completions."""
        assert not tracker.is_setup_complete("/project", "hooks")
        assert not tracker.is_setup_complete("/project", "tests")

    def test_mark_setup_complete(self, tracker):
        """mark_setup_complete should mark phase as complete."""
        tracker.mark_setup_complete("/project", "hooks")

        assert tracker.is_setup_complete("/project", "hooks")
        assert not tracker.is_setup_complete("/project", "tests")  # Other phases unaffected

    def test_different_projects_separate(self, tracker):
        """Different projects should have independent state."""
        tracker.mark_setup_complete("/project1", "hooks")
        tracker.mark_setup_complete("/project2", "tests")

        assert tracker.is_setup_complete("/project1", "hooks")
        assert not tracker.is_setup_complete("/project1", "tests")

        assert tracker.is_setup_complete("/project2", "tests")
        assert not tracker.is_setup_complete("/project2", "hooks")

    def test_different_phases_separate(self, tracker):
        """Different phases for same project should be independent."""
        tracker.mark_setup_complete("/project", "hooks")

        assert tracker.is_setup_complete("/project", "hooks")
        assert not tracker.is_setup_complete("/project", "tests")
        assert not tracker.is_setup_complete("/project", "complexity")

    def test_clear_setup_state(self, tracker):
        """clear_setup_state should remove completion marker."""
        tracker.mark_setup_complete("/project", "hooks")
        assert tracker.is_setup_complete("/project", "hooks")

        tracker.clear_setup_state("/project", "hooks")
        assert not tracker.is_setup_complete("/project", "hooks")

    def test_clear_setup_state_only_affects_target(self, tracker):
        """clear_setup_state should only clear specified phase."""
        tracker.mark_setup_complete("/project", "hooks")
        tracker.mark_setup_complete("/project", "tests")

        tracker.clear_setup_state("/project", "hooks")

        assert not tracker.is_setup_complete("/project", "hooks")
        assert tracker.is_setup_complete("/project", "tests")  # Unaffected

    def test_clear_all(self, tracker):
        """clear_all should remove all completion markers."""
        tracker.mark_setup_complete("/project1", "hooks")
        tracker.mark_setup_complete("/project2", "tests")

        tracker.clear_all()

        assert not tracker.is_setup_complete("/project1", "hooks")
        assert not tracker.is_setup_complete("/project2", "tests")

    def test_multiple_completions(self, tracker):
        """Should handle multiple projects and phases."""
        projects = ["/p1", "/p2", "/p3"]
        phases = ["hooks", "tests", "complexity"]

        for project in projects:
            for phase in phases:
                tracker.mark_setup_complete(project, phase)

        for project in projects:
            for phase in phases:
                assert tracker.is_setup_complete(project, phase)


class TestSetupTrackerInterfaceCompliance:
    """Test SetupTracker implements ISetupTracker correctly."""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create SetupTracker with isolated state directory."""
        config = SetupTrackerConfig(state_dir=tmp_path / "state", redis_config=None)
        return SetupTracker(config=config)

    def test_mark_and_check_complete(self, tracker):
        """SetupTracker should mark and check completion correctly."""
        project = "/test/project"
        phase = "hooks"

        assert not tracker.is_setup_complete(project, phase)

        tracker.mark_setup_complete(project, phase)

        assert tracker.is_setup_complete(project, phase)

    def test_clear_setup_state_filesystem(self, tracker, tmp_path):
        """SetupTracker.clear_setup_state should remove filesystem markers."""
        project = str(tmp_path / "project")
        phase = "hooks"

        tracker.mark_setup_complete(project, phase)
        assert tracker.is_setup_complete(project, phase)

        # Verify marker file exists
        marker_path = tracker._get_marker_path(project, phase)
        assert marker_path.exists()

        tracker.clear_setup_state(project, phase)

        # Marker should be removed
        assert not marker_path.exists()
        assert not tracker.is_setup_complete(project, phase)

    def test_clear_setup_state_redis(self, tmp_path):
        """SetupTracker.clear_setup_state should remove Redis entries."""
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 1
        mock_redis.delete.return_value = True

        config = SetupTrackerConfig(state_dir=tmp_path / "state")
        tracker = SetupTracker(config=config, redis_factory=lambda: mock_redis)

        project = "/test/project"
        phase = "hooks"

        tracker.clear_setup_state(project, phase)

        # Verify Redis delete was called
        expected_key = tracker._get_redis_key(project, phase)
        mock_redis.delete.assert_called_once_with(expected_key)


class TestInterfaceConsistency:
    """Test both implementations provide consistent behavior."""

    @pytest.fixture
    def memory_tracker(self):
        """Create MemorySetupTracker."""
        return MemorySetupTracker()

    @pytest.fixture
    def fs_tracker(self, tmp_path):
        """Create SetupTracker with filesystem."""
        config = SetupTrackerConfig(state_dir=tmp_path / "state", redis_config=None)
        return SetupTracker(config=config)

    def test_both_have_mark_setup_complete(self, memory_tracker, fs_tracker):
        """Both implementations should have mark_setup_complete."""
        assert hasattr(memory_tracker, "mark_setup_complete")
        assert callable(memory_tracker.mark_setup_complete)

        assert hasattr(fs_tracker, "mark_setup_complete")
        assert callable(fs_tracker.mark_setup_complete)

    def test_both_have_is_setup_complete(self, memory_tracker, fs_tracker):
        """Both implementations should have is_setup_complete."""
        assert hasattr(memory_tracker, "is_setup_complete")
        assert callable(memory_tracker.is_setup_complete)

        assert hasattr(fs_tracker, "is_setup_complete")
        assert callable(fs_tracker.is_setup_complete)

    def test_both_have_clear_setup_state(self, memory_tracker, fs_tracker):
        """Both implementations should have clear_setup_state."""
        assert hasattr(memory_tracker, "clear_setup_state")
        assert callable(memory_tracker.clear_setup_state)

        assert hasattr(fs_tracker, "clear_setup_state")
        assert callable(fs_tracker.clear_setup_state)

    def test_consistent_behavior_mark_and_check(self, memory_tracker, fs_tracker):
        """Both should provide consistent mark and check behavior."""
        project = "/test/project"
        phase = "hooks"

        # Both start with no completion
        assert not memory_tracker.is_setup_complete(project, phase)
        assert not fs_tracker.is_setup_complete(project, phase)

        # Mark complete in both
        memory_tracker.mark_setup_complete(project, phase)
        fs_tracker.mark_setup_complete(project, phase)

        # Both should report complete
        assert memory_tracker.is_setup_complete(project, phase)
        assert fs_tracker.is_setup_complete(project, phase)

    def test_consistent_behavior_clear(self, memory_tracker, fs_tracker):
        """Both should provide consistent clear behavior."""
        project = "/test/project"
        phase = "hooks"

        # Mark complete in both
        memory_tracker.mark_setup_complete(project, phase)
        fs_tracker.mark_setup_complete(project, phase)

        # Clear in both
        memory_tracker.clear_setup_state(project, phase)
        fs_tracker.clear_setup_state(project, phase)

        # Both should report not complete
        assert not memory_tracker.is_setup_complete(project, phase)
        assert not fs_tracker.is_setup_complete(project, phase)
