"""Configuration for PreflightValidator.

Provides configurable settings for preflight validation, enabling test isolation
and custom validation behavior.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PreflightConfig:
    """Configuration for PreflightValidator.

    Attributes:
        cache_max_age_days: Maximum age (in days) before state is considered stale.
            Defaults to 30 days to match ProjectStateManager implementation.
        state_dir_name: Name of the state directory within projects.
            Defaults to ".ai-state".
        hook_cache_dir: Optional custom directory for hook cache files.
            If None, uses default "config/precommit-cache".
        test_cache_dir: Optional custom directory for test cache files.
            If None, uses default "config/test-cache".
        validation_timeout_ms: Maximum time for validation operations.
            Defaults to 100ms for fast validation.

    Example:
        >>> # Default configuration (production)
        >>> config = PreflightConfig()
        >>> validator = PreflightValidator(tracker, config=config)

        >>> # Test configuration with fast staleness
        >>> test_config = PreflightConfig(cache_max_age_days=1)
        >>> validator = PreflightValidator(tracker, config=test_config)

        >>> # Isolated test configuration with custom cache dirs
        >>> isolated_config = PreflightConfig(
        ...     cache_max_age_days=1,
        ...     hook_cache_dir=tmp_path / "hooks",
        ...     test_cache_dir=tmp_path / "tests"
        ... )
    """

    cache_max_age_days: int = 30  # Match ProjectStateManager's 30-day limit
    state_dir_name: str = ".ai-state"
    hook_cache_dir: Path | None = None  # None = use default "config/precommit-cache"
    test_cache_dir: Path | None = None  # None = use default "config/test-cache"
    validation_timeout_ms: int = 100  # Fast validation

    @classmethod
    def for_testing(cls, tmp_path: Path | None = None) -> "PreflightConfig":
        """Create configuration optimized for testing.

        Args:
            tmp_path: Optional temporary directory for isolated cache files.
                If provided, cache dirs will be created under tmp_path.

        Returns:
            PreflightConfig with test-friendly settings.

        Example:
            >>> config = PreflightConfig.for_testing(tmp_path)
            >>> # Fast staleness (1 day)
            >>> # Isolated cache directories
        """
        if tmp_path:
            return cls(
                cache_max_age_days=1,  # Fast staleness for tests
                hook_cache_dir=tmp_path / "hook-cache",
                test_cache_dir=tmp_path / "test-cache",
                validation_timeout_ms=50,  # Even faster for tests
            )
        else:
            return cls(
                cache_max_age_days=1,
                validation_timeout_ms=50,
            )

    def get_hook_cache_dir(self) -> Path:
        """Get hook cache directory (custom or default).

        Returns:
            Path to hook cache directory.
        """
        return self.hook_cache_dir or Path("config/precommit-cache")

    def get_test_cache_dir(self) -> Path:
        """Get test cache directory (custom or default).

        Returns:
            Path to test cache directory.
        """
        return self.test_cache_dir or Path("config/test-cache")
