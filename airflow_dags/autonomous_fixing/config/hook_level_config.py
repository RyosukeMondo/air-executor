"""Configuration for HookLevelManager.

Provides configurable settings for hook level management, enabling test isolation
and custom configuration paths.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class HookLevelConfig:
    """Configuration for HookLevelManager.

    Attributes:
        config_path: Path to hook levels configuration file.
            Defaults to "config/hook-levels.yaml".
        cache_dir: Directory for hook metadata cache files.
            Defaults to "config/precommit-cache".

    Example:
        >>> # Default configuration (production)
        >>> config = HookLevelConfig()
        >>> manager = HookLevelManager(config=config)

        >>> # Test configuration with isolated paths
        >>> test_config = HookLevelConfig.for_testing(tmp_path)
        >>> manager = HookLevelManager(config=test_config)
    """

    config_path: Path = Path("config/hook-levels.yaml")
    cache_dir: Path = Path("config/precommit-cache")

    @classmethod
    def for_testing(cls, tmp_path: Path | None = None) -> "HookLevelConfig":
        """Create configuration optimized for testing.

        Args:
            tmp_path: Optional temporary directory for isolated cache files.
                If provided, config and cache paths will be under tmp_path.

        Returns:
            HookLevelConfig with test-friendly isolated paths.

        Example:
            >>> config = HookLevelConfig.for_testing(tmp_path)
            >>> # config_path = tmp_path / "hook-levels.yaml"
            >>> # cache_dir = tmp_path / "hook-cache"
        """
        if tmp_path:
            return cls(
                config_path=tmp_path / "hook-levels.yaml",
                cache_dir=tmp_path / "hook-cache",
            )
        return cls()
