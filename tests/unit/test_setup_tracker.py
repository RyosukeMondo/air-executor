"""Unit tests for SetupTracker."""

import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from airflow_dags.autonomous_fixing.config import SetupTrackerConfig
from airflow_dags.autonomous_fixing.core.setup_tracker import SetupTracker


class TestSetupTrackerFilesystem:
    """Test filesystem-based state tracking (no Redis)."""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create SetupTracker with temporary state directory."""
        config = SetupTrackerConfig(state_dir=tmp_path, ttl_days=30, redis_config=None)
        return SetupTracker(config=config)

    def test_mark_setup_complete_creates_marker(self, tracker, tmp_path):
        """Test that marking setup complete creates filesystem marker."""
        project = "/test/project"
        phase = "hooks"

        tracker.mark_setup_complete(project, phase)

        # Verify marker file exists
        marker_files = list(tmp_path.glob("*_hooks_complete.marker"))
        assert len(marker_files) == 1

        # Verify marker contains valid timestamp
        timestamp_str = marker_files[0].read_text()
        timestamp = datetime.fromisoformat(timestamp_str)
        assert isinstance(timestamp, datetime)
        assert (datetime.now() - timestamp).total_seconds() < 1

    def test_is_setup_complete_fresh_marker(self, tracker, tmp_path):
        """Test that fresh markers are recognized as complete."""
        project = "/test/project"
        phase = "tests"

        # Create fresh marker
        tracker.mark_setup_complete(project, phase)

        # Verify recognized as complete
        assert tracker.is_setup_complete(project, phase) is True

    def test_is_setup_complete_missing_marker(self, tracker):
        """Test that missing markers return False."""
        project = "/test/project"
        phase = "hooks"

        assert tracker.is_setup_complete(project, phase) is False

    def test_is_setup_complete_stale_marker(self, tracker, tmp_path):
        """Test that stale markers (>30 days) return False."""
        project = "/test/project"
        phase = "hooks"

        # Create marker with old timestamp
        marker_path = tracker._get_marker_path(project, phase)
        old_timestamp = (datetime.now() - timedelta(days=31)).isoformat()
        marker_path.write_text(old_timestamp)

        assert tracker.is_setup_complete(project, phase) is False

    def test_is_setup_complete_edge_case_29_days(self, tracker, tmp_path):
        """Test that markers just under 30 days are still valid."""
        project = "/test/project"
        phase = "tests"

        # Create marker 29 days old
        marker_path = tracker._get_marker_path(project, phase)
        timestamp_29d = (datetime.now() - timedelta(days=29)).isoformat()
        marker_path.write_text(timestamp_29d)

        assert tracker.is_setup_complete(project, phase) is True

    def test_marker_file_permissions(self, tracker, tmp_path):
        """Test that marker files have restrictive permissions (0o600)."""
        project = "/test/project"
        phase = "hooks"

        tracker.mark_setup_complete(project, phase)

        marker_files = list(tmp_path.glob("*_hooks_complete.marker"))
        assert len(marker_files) == 1

        # Check permissions (owner read/write only)
        import stat

        mode = marker_files[0].stat().st_mode
        assert stat.S_IMODE(mode) == 0o600

    def test_corrupted_marker_returns_false(self, tracker, tmp_path):
        """Test that corrupted marker files return False gracefully."""
        project = "/test/project"
        phase = "tests"

        # Create marker with invalid timestamp
        marker_path = tracker._get_marker_path(project, phase)
        marker_path.write_text("invalid-timestamp")

        assert tracker.is_setup_complete(project, phase) is False

    def test_different_projects_separate_markers(self, tracker, tmp_path):
        """Test that different projects have separate markers."""
        project1 = "/test/project1"
        project2 = "/test/project2"
        phase = "hooks"

        tracker.mark_setup_complete(project1, phase)

        assert tracker.is_setup_complete(project1, phase) is True
        assert tracker.is_setup_complete(project2, phase) is False

    def test_different_phases_separate_markers(self, tracker, tmp_path):
        """Test that different phases have separate markers."""
        project = "/test/project"

        tracker.mark_setup_complete(project, "hooks")

        assert tracker.is_setup_complete(project, "hooks") is True
        assert tracker.is_setup_complete(project, "tests") is False


class TestSetupTrackerRedis:
    """Test Redis-based state tracking."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = MagicMock()
        mock.ping.return_value = True
        mock.exists.return_value = 0
        mock.setex.return_value = True
        return mock

    @pytest.fixture
    def tracker_with_redis(self, mock_redis, tmp_path):
        """Create SetupTracker with mocked Redis."""
        with patch(
            "airflow_dags.autonomous_fixing.core.setup_tracker.redis.Redis", return_value=mock_redis
        ):
            redis_config_dict = {
                "redis_host": "localhost",
                "redis_port": 6379,
                "namespace": "test_namespace",
            }
            config = SetupTrackerConfig(
                state_dir=tmp_path, ttl_days=30, redis_config=redis_config_dict
            )
            tracker = SetupTracker(config=config)
            yield tracker, mock_redis

    def test_redis_initialization_success(self, mock_redis, tmp_path):
        """Test successful Redis initialization."""
        with patch(
            "airflow_dags.autonomous_fixing.core.setup_tracker.redis.Redis", return_value=mock_redis
        ):
            config = SetupTrackerConfig(
                state_dir=tmp_path, redis_config={"redis_host": "localhost", "redis_port": 6379}
            )
            tracker = SetupTracker(config=config)

            assert tracker.redis_client is not None
            mock_redis.ping.assert_called_once()

    def test_redis_initialization_failure_fallback(self, tmp_path):
        """Test graceful fallback when Redis initialization fails."""
        mock_redis = MagicMock()
        # Use redis.ConnectionError for realistic simulation
        import redis as redis_module

        mock_redis.ping.side_effect = redis_module.ConnectionError("Connection failed")

        with patch(
            "airflow_dags.autonomous_fixing.core.setup_tracker.redis.Redis", return_value=mock_redis
        ):
            config = SetupTrackerConfig(
                state_dir=tmp_path, redis_config={"redis_host": "localhost", "redis_port": 6379}
            )
            tracker = SetupTracker(config=config)

            # Should fallback to None (filesystem only)
            assert tracker.redis_client is None

    def test_mark_setup_complete_stores_in_redis(self, tracker_with_redis):
        """Test that marking complete stores in Redis."""
        tracker, mock_redis = tracker_with_redis
        project = "/test/project"
        phase = "hooks"

        tracker.mark_setup_complete(project, phase)

        # Verify Redis setex was called with TTL
        assert mock_redis.setex.called
        call_args = mock_redis.setex.call_args
        key, ttl, value = call_args[0]

        assert "setup:test_namespace:" in key
        assert ":hooks" in key
        assert ttl == tracker.config.ttl_seconds
        assert datetime.fromisoformat(value)  # Valid ISO timestamp

    def test_is_setup_complete_checks_redis_first(self, tracker_with_redis):
        """Test that setup completion checks Redis first."""
        tracker, mock_redis = tracker_with_redis
        project = "/test/project"
        phase = "hooks"

        # Simulate Redis has the key
        mock_redis.exists.return_value = 1

        result = tracker.is_setup_complete(project, phase)

        assert result is True
        mock_redis.exists.assert_called_once()

    def test_is_setup_complete_redis_miss_checks_filesystem(self, tracker_with_redis, tmp_path):
        """Test filesystem fallback when Redis misses."""
        tracker, mock_redis = tracker_with_redis
        project = "/test/project"
        phase = "tests"

        # Simulate Redis miss
        mock_redis.exists.return_value = 0

        # Create filesystem marker
        marker_path = tracker._get_marker_path(project, phase)
        marker_path.write_text(datetime.now().isoformat())

        result = tracker.is_setup_complete(project, phase)

        assert result is True
        mock_redis.exists.assert_called_once()

    def test_redis_query_failure_fallback_to_filesystem(self, tracker_with_redis, tmp_path):
        """Test filesystem fallback when Redis query fails."""
        tracker, mock_redis = tracker_with_redis
        project = "/test/project"
        phase = "hooks"

        # Simulate Redis query failure with realistic exception
        import redis as redis_module

        mock_redis.exists.side_effect = redis_module.RedisError("Redis error")

        # Create filesystem marker
        marker_path = tracker._get_marker_path(project, phase)
        marker_path.write_text(datetime.now().isoformat())

        result = tracker.is_setup_complete(project, phase)

        assert result is True  # Should fallback successfully

    def test_redis_key_format(self, tracker_with_redis):
        """Test Redis key format includes namespace and project hash."""
        tracker, _ = tracker_with_redis
        project = "/test/project/path"
        phase = "hooks"

        key = tracker._get_redis_key(project, phase)

        assert key.startswith("setup:test_namespace:")
        assert key.endswith(":hooks")
        # Should contain hash, not full path (for security)
        assert "/test/project/path" not in key

    def test_redis_store_failure_continues(self, tracker_with_redis, tmp_path):
        """Test that Redis store failure doesn't crash, still creates filesystem marker."""
        tracker, mock_redis = tracker_with_redis
        project = "/test/project"
        phase = "tests"

        # Simulate Redis store failure with realistic exception
        import redis as redis_module

        mock_redis.setex.side_effect = redis_module.RedisError("Redis write failed")

        # Should not raise exception
        tracker.mark_setup_complete(project, phase)

        # Filesystem marker should still be created
        marker_files = list(tmp_path.glob("*_tests_complete.marker"))
        assert len(marker_files) == 1


class TestSetupTrackerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create SetupTracker with temporary state directory."""
        config = SetupTrackerConfig(state_dir=tmp_path, ttl_days=30, redis_config=None)
        return SetupTracker(config=config)

    def test_project_path_with_special_characters(self, tracker, tmp_path):
        """Test handling of project paths with special characters."""
        project = "/test/project-with-dashes/and_underscores/v1.0"
        phase = "hooks"

        tracker.mark_setup_complete(project, phase)
        assert tracker.is_setup_complete(project, phase) is True

    def test_long_project_path(self, tracker, tmp_path):
        """Test handling of very long project paths."""
        project = "/very/long/path/" + "subdir/" * 50 + "project"
        phase = "tests"

        tracker.mark_setup_complete(project, phase)
        assert tracker.is_setup_complete(project, phase) is True

    def test_concurrent_marker_writes(self, tracker, tmp_path):
        """Test concurrent writes to same marker (last-write-wins)."""
        project = "/test/project"
        phase = "hooks"

        # Simulate concurrent writes
        tracker.mark_setup_complete(project, phase)
        time.sleep(0.01)
        tracker.mark_setup_complete(project, phase)

        # Should still be valid
        assert tracker.is_setup_complete(project, phase) is True

    def test_marker_directory_creation(self, tmp_path):
        """Test that state directory is created if missing."""
        state_dir = tmp_path / "new_state_dir"
        assert not state_dir.exists()

        config = SetupTrackerConfig(state_dir=state_dir, redis_config=None)
        _ = SetupTracker(config=config)

        # State directory should be created
        assert state_dir.exists()
        assert state_dir.is_dir()

    def test_namespace_isolation(self, tmp_path):
        """Test that different namespaces are isolated in Redis keys."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True

        with patch(
            "airflow_dags.autonomous_fixing.core.setup_tracker.redis.Redis", return_value=mock_redis
        ):
            config1 = SetupTrackerConfig(
                state_dir=tmp_path, redis_config={"redis_host": "localhost", "namespace": "ns1"}
            )
            config2 = SetupTrackerConfig(
                state_dir=tmp_path, redis_config={"redis_host": "localhost", "namespace": "ns2"}
            )

            tracker1 = SetupTracker(config=config1)
            tracker2 = SetupTracker(config=config2)

            key1 = tracker1._get_redis_key("/project", "hooks")
            key2 = tracker2._get_redis_key("/project", "hooks")

            assert "ns1" in key1
            assert "ns2" in key2
            assert key1 != key2
