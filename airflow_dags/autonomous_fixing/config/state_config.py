"""Configuration for ProjectStateManager.

Provides configurable settings for project state management, enabling test isolation
and custom state directory configurations.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class StateConfig:
    """Configuration for ProjectStateManager.

    Attributes:
        state_dir_name: Name of the state directory within projects.
            Defaults to ".ai-state".
        max_age_days: Maximum age (in days) before state is considered stale.
            Defaults to 30 days.
        external_hook_cache_dir: Path to external hook cache directory.
            Defaults to "config/precommit-cache" for backward compatibility.
        external_test_cache_dir: Path to external test cache directory.
            Defaults to "config/test-cache" for backward compatibility.

    Example:
        >>> # Default configuration (production)
        >>> config = StateConfig()
        >>> manager = ProjectStateManager(project_path, config=config)

        >>> # Test configuration with fast staleness
        >>> test_config = StateConfig(max_age_days=1)
        >>> manager = ProjectStateManager(project_path, config=test_config)

        >>> # Isolated test configuration with custom base directory
        >>> isolated_config = StateConfig().with_base_dir(tmp_path)
        >>> manager = ProjectStateManager(project_path, config=isolated_config)
    """

    state_dir_name: str = ".ai-state"
    max_age_days: int = 30
    external_hook_cache_dir: Path = Path("config/precommit-cache")
    external_test_cache_dir: Path = Path("config/test-cache")

    @property
    def max_age_seconds(self) -> int:
        """Get maximum age in seconds.

        Returns:
            Maximum age in seconds (max_age_days * 24 * 60 * 60).

        Example:
            >>> config = StateConfig(max_age_days=30)
            >>> config.max_age_seconds
            2592000  # 30 * 24 * 60 * 60
        """
        return self.max_age_days * 24 * 60 * 60

    def with_base_dir(self, base: Path) -> "StateConfig":
        """Create config with custom base directory for caches.

        Useful for test isolation - creates isolated cache directories
        under a temporary directory.

        Args:
            base: Base directory for cache files.

        Returns:
            New StateConfig with cache dirs under base directory.

        Example:
            >>> config = StateConfig().with_base_dir(tmp_path)
            >>> # external_hook_cache_dir = tmp_path / "hook-cache"
            >>> # external_test_cache_dir = tmp_path / "test-cache"
        """
        return StateConfig(
            state_dir_name=self.state_dir_name,
            max_age_days=self.max_age_days,
            external_hook_cache_dir=base / "hook-cache",
            external_test_cache_dir=base / "test-cache",
        )

    @classmethod
    def for_testing(cls, tmp_path: Path | None = None) -> "StateConfig":
        """Create configuration optimized for testing.

        Args:
            tmp_path: Optional temporary directory for isolated cache files.
                If provided, cache dirs will be created under tmp_path.

        Returns:
            StateConfig with test-friendly settings.

        Example:
            >>> config = StateConfig.for_testing(tmp_path)
            >>> # Fast staleness (1 day)
            >>> # Isolated cache directories under tmp_path
        """
        if tmp_path:
            return cls(
                state_dir_name=".ai-state",
                max_age_days=1,  # Fast staleness for tests
                external_hook_cache_dir=tmp_path / "hook-cache",
                external_test_cache_dir=tmp_path / "test-cache",
            )
        return cls(
            state_dir_name=".ai-state",
            max_age_days=1,  # Fast staleness for tests
        )
