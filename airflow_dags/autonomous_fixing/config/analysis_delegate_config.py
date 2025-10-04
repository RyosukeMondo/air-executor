"""Configuration for AnalysisDelegate.

Provides configurable settings for analysis delegate, enabling test isolation
and custom cache paths.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AnalysisDelegateConfig:
    """Configuration for AnalysisDelegate.

    Attributes:
        analysis_cache_dir: Directory for static analysis cache files.
            Defaults to "config/analysis-cache".
        hook_cache_dir: Directory for hook configuration cache files.
            Defaults to "config/precommit-cache".
        test_cache_dir: Directory for test discovery cache files.
            Defaults to "config/test-cache".
        wrapper_settings: Settings for Claude wrapper.
            Contains 'path' and 'python_executable' keys.

    Example:
        >>> # Default configuration (production)
        >>> config = AnalysisDelegateConfig()
        >>> delegate = AnalysisDelegate(orchestrator_config, config=config)

        >>> # Test configuration with isolated paths
        >>> test_config = AnalysisDelegateConfig.for_testing(tmp_path)
        >>> delegate = AnalysisDelegate(orchestrator_config, config=test_config)
    """

    analysis_cache_dir: Path = Path("config/analysis-cache")
    hook_cache_dir: Path = Path("config/precommit-cache")
    test_cache_dir: Path = Path("config/test-cache")
    wrapper_settings: dict[str, Any] = field(
        default_factory=lambda: {
            "path": "scripts/claude_wrapper.py",
            "python_executable": "python",
        }
    )

    @classmethod
    def for_testing(cls, tmp_path: Path | None = None) -> "AnalysisDelegateConfig":
        """Create configuration optimized for testing.

        Args:
            tmp_path: Optional temporary directory for isolated cache files.
                If provided, all cache paths will be under tmp_path.

        Returns:
            AnalysisDelegateConfig with test-friendly isolated paths.

        Example:
            >>> config = AnalysisDelegateConfig.for_testing(tmp_path)
            >>> # analysis_cache_dir = tmp_path / "analysis-cache"
            >>> # hook_cache_dir = tmp_path / "hook-cache"
            >>> # test_cache_dir = tmp_path / "test-cache"
        """
        if tmp_path:
            return cls(
                analysis_cache_dir=tmp_path / "analysis-cache",
                hook_cache_dir=tmp_path / "hook-cache",
                test_cache_dir=tmp_path / "test-cache",
            )
        return cls()
