"""Configuration for SetupTracker.

Provides configurable settings for setup tracking, enabling test isolation
and custom state directory configurations.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SetupTrackerConfig:
    """Configuration for SetupTracker.

    Attributes:
        state_dir: Path to the state directory for setup markers.
            Defaults to ".ai-state".
        ttl_days: Time-to-live in days before setup markers are considered stale.
            Defaults to 30 days.
        redis_config: Optional Redis configuration dict with keys:
            - redis_host: Redis server host (default: localhost)
            - redis_port: Redis server port (default: 6379)
            - namespace: Redis key namespace (default: autonomous_fix)
            If None, only filesystem storage is used.

    Example:
        >>> # Default configuration (production)
        >>> config = SetupTrackerConfig()
        >>> tracker = SetupTracker(config=config)

        >>> # Test configuration with fast TTL
        >>> test_config = SetupTrackerConfig(ttl_days=1)
        >>> tracker = SetupTracker(config=test_config)

        >>> # Isolated test configuration with custom state directory
        >>> isolated_config = SetupTrackerConfig(
        ...     state_dir=tmp_path / "setup-state",
        ...     ttl_days=1
        ... )
        >>> tracker = SetupTracker(config=isolated_config)

        >>> # With Redis configuration
        >>> redis_config = SetupTrackerConfig(
        ...     redis_config={
        ...         "redis_host": "localhost",
        ...         "redis_port": 6379,
        ...         "namespace": "test_fix"
        ...     }
        ... )
    """

    state_dir: Path = Path(".ai-state")
    ttl_days: int = 30
    redis_config: dict[str, Any] | None = None

    @property
    def ttl_seconds(self) -> int:
        """Get TTL in seconds.

        Returns:
            TTL in seconds (ttl_days * 24 * 60 * 60).

        Example:
            >>> config = SetupTrackerConfig(ttl_days=30)
            >>> config.ttl_seconds
            2592000  # 30 * 24 * 60 * 60
        """
        return self.ttl_days * 24 * 60 * 60

    @classmethod
    def for_testing(
        cls, tmp_path: Path | None = None, with_redis: bool = False
    ) -> "SetupTrackerConfig":
        """Create configuration optimized for testing.

        Args:
            tmp_path: Optional temporary directory for isolated state files.
                If provided, state_dir will be created under tmp_path.
            with_redis: If True, include minimal Redis configuration.
                Defaults to False (filesystem-only).

        Returns:
            SetupTrackerConfig with test-friendly settings.

        Example:
            >>> # Filesystem-only test config
            >>> config = SetupTrackerConfig.for_testing(tmp_path)
            >>> # Fast TTL (1 day)
            >>> # Isolated state directory

            >>> # With Redis for integration tests
            >>> config = SetupTrackerConfig.for_testing(tmp_path, with_redis=True)
        """
        redis_cfg = None
        if with_redis:
            redis_cfg = {
                "redis_host": "localhost",
                "redis_port": 6379,
                "namespace": "test_autonomous_fix",
            }

        if tmp_path:
            return cls(
                state_dir=tmp_path / "setup-state",
                ttl_days=1,  # Fast TTL for tests
                redis_config=redis_cfg,
            )
        return cls(
            state_dir=Path(".ai-state"),
            ttl_days=1,  # Fast TTL for tests
            redis_config=redis_cfg,
        )

    def with_state_dir(self, state_dir: Path) -> "SetupTrackerConfig":
        """Create config with custom state directory.

        Useful for test isolation - creates isolated state directory
        under a temporary directory.

        Args:
            state_dir: Custom state directory path.

        Returns:
            New SetupTrackerConfig with custom state directory.

        Example:
            >>> config = SetupTrackerConfig().with_state_dir(tmp_path / "state")
            >>> # state_dir = tmp_path / "state"
        """
        return SetupTrackerConfig(
            state_dir=state_dir,
            ttl_days=self.ttl_days,
            redis_config=self.redis_config,
        )
