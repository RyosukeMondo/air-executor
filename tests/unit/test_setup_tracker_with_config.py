"""Unit tests for SetupTracker with SetupTrackerConfig.

Tests the new config-based initialization and backward compatibility.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from airflow_dags.autonomous_fixing.config import SetupTrackerConfig
from airflow_dags.autonomous_fixing.core.setup_tracker import SetupTracker


class TestSetupTrackerWithConfig:
    """Test SetupTracker with SetupTrackerConfig."""

    def test_setup_tracker_with_config_object(self, tmp_path):
        """Test SetupTracker initialized with SetupTrackerConfig."""
        config = SetupTrackerConfig(state_dir=tmp_path / "state", ttl_days=7, redis_config=None)
        tracker = SetupTracker(config=config)

        # Verify config applied
        assert tracker.config.state_dir == tmp_path / "state"
        assert tracker.config.ttl_days == 7
        assert tracker.config.ttl_seconds == 7 * 24 * 60 * 60
        assert tracker.redis_client is None

        # Verify state dir created
        assert (tmp_path / "state").exists()

    def test_setup_tracker_with_dict_backward_compatibility(self, tmp_path):
        """Test backward compatibility: passing dict is treated as redis_config."""
        redis_dict = {
            "redis_host": "localhost",
            "redis_port": 6379,
            "namespace": "test",
        }

        # Mock Redis to avoid real connection
        with patch(
            "airflow_dags.autonomous_fixing.core.setup_tracker.redis.Redis"
        ) as mock_redis_class:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis_class.return_value = mock_client

            tracker = SetupTracker(config=redis_dict)

            # Should create SetupTrackerConfig internally
            assert isinstance(tracker.config, SetupTrackerConfig)
            assert tracker.config.redis_config == redis_dict
            assert tracker.redis_client is not None

    def test_setup_tracker_with_none_uses_defaults(self, tmp_path):
        """Test passing None uses default SetupTrackerConfig."""
        # Change working dir to tmp_path to isolate state_dir
        import os

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tracker = SetupTracker(config=None)

            # Should use defaults
            assert isinstance(tracker.config, SetupTrackerConfig)
            assert tracker.config.state_dir == Path(".ai-state")
            assert tracker.config.ttl_days == 30
            assert tracker.config.redis_config is None
        finally:
            os.chdir(original_cwd)

    def test_setup_tracker_for_testing_config(self, tmp_path):
        """Test SetupTracker with for_testing() config."""
        config = SetupTrackerConfig.for_testing(tmp_path)
        tracker = SetupTracker(config=config)

        # Verify test-friendly settings
        assert tracker.config.state_dir == tmp_path / "setup-state"
        assert tracker.config.ttl_days == 1  # Fast TTL
        assert tracker.config.ttl_seconds == 24 * 60 * 60
        assert tracker.redis_client is None

    def test_setup_tracker_custom_ttl(self, tmp_path):
        """Test custom TTL in config affects marker validation."""
        config = SetupTrackerConfig(state_dir=tmp_path, ttl_days=1)
        tracker = SetupTracker(config=config)

        project = "/test/project"
        phase = "hooks"

        # Create marker that's 2 days old (stale for 1-day TTL)
        marker_path = tracker._get_marker_path(project, phase)
        old_timestamp = (datetime.now() - timedelta(days=2)).isoformat()
        marker_path.write_text(old_timestamp)

        # Should be stale (TTL is 1 day)
        assert tracker.is_setup_complete(project, phase) is False

    def test_setup_tracker_custom_ttl_fresh_marker(self, tmp_path):
        """Test custom TTL with fresh marker."""
        config = SetupTrackerConfig(state_dir=tmp_path, ttl_days=1)
        tracker = SetupTracker(config=config)

        project = "/test/project"
        phase = "hooks"

        # Create fresh marker
        tracker.mark_setup_complete(project, phase)

        # Should be valid
        assert tracker.is_setup_complete(project, phase) is True

    def test_setup_tracker_isolated_state_dirs(self, tmp_path):
        """Test multiple trackers with isolated state directories."""
        config1 = SetupTrackerConfig(state_dir=tmp_path / "tracker1")
        config2 = SetupTrackerConfig(state_dir=tmp_path / "tracker2")

        tracker1 = SetupTracker(config=config1)
        tracker2 = SetupTracker(config=config2)

        project = "/test/project"
        phase = "hooks"

        # Mark complete in tracker1
        tracker1.mark_setup_complete(project, phase)

        # tracker1 should see it
        assert tracker1.is_setup_complete(project, phase) is True

        # tracker2 should NOT see it (different state dir)
        assert tracker2.is_setup_complete(project, phase) is False

    def test_setup_tracker_with_state_dir_helper(self, tmp_path):
        """Test with_state_dir() helper creates isolated tracker."""
        base_config = SetupTrackerConfig(ttl_days=7)
        custom_config = base_config.with_state_dir(tmp_path / "custom")

        tracker = SetupTracker(config=custom_config)

        # Verify custom state_dir
        assert tracker.config.state_dir == tmp_path / "custom"
        assert tracker.config.ttl_days == 7

        # State dir should be created
        assert (tmp_path / "custom").exists()

    def test_setup_tracker_redis_config_integration(self, tmp_path):
        """Test Redis config properly passed through."""
        redis_cfg = {
            "redis_host": "redis.example.com",
            "redis_port": 6380,
            "namespace": "test_ns",
        }

        config = SetupTrackerConfig(state_dir=tmp_path, ttl_days=14, redis_config=redis_cfg)

        with patch(
            "airflow_dags.autonomous_fixing.core.setup_tracker.redis.Redis"
        ) as mock_redis_class:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis_class.return_value = mock_client

            tracker = SetupTracker(config=config)

            # Verify Redis initialized with correct params
            mock_redis_class.assert_called_once()
            call_kwargs = mock_redis_class.call_args[1]
            assert call_kwargs["host"] == "redis.example.com"
            assert call_kwargs["port"] == 6380

            # Verify namespace set correctly
            assert tracker.namespace == "test_ns"

    def test_setup_tracker_ttl_seconds_used_in_redis(self, tmp_path):
        """Test that config.ttl_seconds is used for Redis TTL."""
        config = SetupTrackerConfig(
            state_dir=tmp_path,
            ttl_days=7,
            redis_config={"redis_host": "localhost", "redis_port": 6379},
        )

        with patch(
            "airflow_dags.autonomous_fixing.core.setup_tracker.redis.Redis"
        ) as mock_redis_class:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.setex.return_value = True
            mock_redis_class.return_value = mock_client

            tracker = SetupTracker(config=config)
            tracker.mark_setup_complete("/test/project", "hooks")

            # Verify setex called with correct TTL (7 days in seconds)
            expected_ttl = 7 * 24 * 60 * 60
            mock_client.setex.assert_called_once()
            call_args = mock_client.setex.call_args[0]
            assert call_args[1] == expected_ttl  # TTL is second argument
