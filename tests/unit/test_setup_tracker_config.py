"""Unit tests for SetupTrackerConfig.

Tests configuration creation, helpers, and backward compatibility.
"""

from pathlib import Path

from airflow_dags.autonomous_fixing.config import SetupTrackerConfig


def test_setup_tracker_config_defaults():
    """Test default configuration values."""
    config = SetupTrackerConfig()

    # Verify defaults
    assert config.state_dir == Path(".ai-state")
    assert config.ttl_days == 30
    assert config.redis_config is None


def test_setup_tracker_config_custom():
    """Test creating config with custom values."""
    custom_state_dir = Path("/tmp/custom-state")
    redis_cfg = {
        "redis_host": "redis.example.com",
        "redis_port": 6380,
        "namespace": "custom_fix",
    }

    config = SetupTrackerConfig(state_dir=custom_state_dir, ttl_days=7, redis_config=redis_cfg)

    assert config.state_dir == custom_state_dir
    assert config.ttl_days == 7
    assert config.redis_config == redis_cfg


def test_setup_tracker_config_ttl_seconds_property():
    """Test ttl_seconds computed property."""
    config = SetupTrackerConfig(ttl_days=30)

    # 30 days = 30 * 24 * 60 * 60 = 2,592,000 seconds
    assert config.ttl_seconds == 2_592_000

    # Test with different TTL
    config_7_days = SetupTrackerConfig(ttl_days=7)
    assert config_7_days.ttl_seconds == 7 * 24 * 60 * 60


def test_setup_tracker_config_for_testing_no_tmp_path():
    """Test for_testing() without tmp_path (filesystem-only)."""
    config = SetupTrackerConfig.for_testing()

    # Verify test-friendly defaults
    assert config.state_dir == Path(".ai-state")  # Default location
    assert config.ttl_days == 1  # Fast TTL for tests
    assert config.redis_config is None  # No Redis by default


def test_setup_tracker_config_for_testing_with_tmp_path(tmp_path):
    """Test for_testing() with isolated tmp_path."""
    config = SetupTrackerConfig.for_testing(tmp_path)

    # Verify isolation
    assert config.state_dir == tmp_path / "setup-state"
    assert config.ttl_days == 1  # Fast TTL for tests
    assert config.redis_config is None  # No Redis by default


def test_setup_tracker_config_for_testing_with_redis(tmp_path):
    """Test for_testing() with Redis enabled."""
    config = SetupTrackerConfig.for_testing(tmp_path, with_redis=True)

    # Verify Redis config
    assert config.redis_config is not None
    assert config.redis_config["redis_host"] == "localhost"
    assert config.redis_config["redis_port"] == 6379
    assert config.redis_config["namespace"] == "test_autonomous_fix"

    # Verify other test settings
    assert config.state_dir == tmp_path / "setup-state"
    assert config.ttl_days == 1


def test_setup_tracker_config_with_state_dir(tmp_path):
    """Test with_state_dir() helper method."""
    config = SetupTrackerConfig(ttl_days=30)
    custom_dir = tmp_path / "custom-state"

    new_config = config.with_state_dir(custom_dir)

    # Verify new config has custom state_dir
    assert new_config.state_dir == custom_dir

    # Verify other settings preserved
    assert new_config.ttl_days == 30
    assert new_config.redis_config is None

    # Original config unchanged
    assert config.state_dir == Path(".ai-state")


def test_setup_tracker_config_with_state_dir_preserves_redis():
    """Test with_state_dir() preserves Redis config."""
    redis_cfg = {"redis_host": "localhost", "redis_port": 6379}
    config = SetupTrackerConfig(redis_config=redis_cfg)

    custom_dir = Path("/tmp/new-state")
    new_config = config.with_state_dir(custom_dir)

    # Verify Redis config preserved
    assert new_config.redis_config == redis_cfg
    assert new_config.state_dir == custom_dir


def test_setup_tracker_config_backward_compatibility():
    """Test that config supports same Redis config as before."""
    # Old-style Redis config dict
    redis_config = {
        "redis_host": "localhost",
        "redis_port": 6379,
        "namespace": "autonomous_fix",
    }

    config = SetupTrackerConfig(redis_config=redis_config)

    # Verify Redis config stored correctly
    assert config.redis_config == redis_config
    assert config.redis_config["redis_host"] == "localhost"
    assert config.redis_config["redis_port"] == 6379
    assert config.redis_config["namespace"] == "autonomous_fix"
