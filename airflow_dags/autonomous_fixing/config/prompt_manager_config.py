"""Configuration for PromptManager.

Provides configurable settings for prompt manager, enabling test isolation
and custom prompt configuration paths.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PromptManagerConfig:
    """Configuration for PromptManager.

    Attributes:
        prompts_config_path: Path to prompts configuration file.
            Defaults to "config/prompts.yaml".

    Example:
        >>> # Default configuration (production)
        >>> config = PromptManagerConfig()
        >>> manager = PromptManager(config=config)

        >>> # Test configuration with custom prompts file
        >>> test_config = PromptManagerConfig.for_testing(tmp_path)
        >>> manager = PromptManager(config=test_config)
    """

    prompts_config_path: Path = Path("config/prompts.yaml")

    @classmethod
    def for_testing(cls, tmp_path: Path | None = None) -> "PromptManagerConfig":
        """Create configuration optimized for testing.

        Args:
            tmp_path: Optional temporary directory for isolated config files.
                If provided, prompts config will be under tmp_path.

        Returns:
            PromptManagerConfig with test-friendly isolated path.

        Example:
            >>> config = PromptManagerConfig.for_testing(tmp_path)
            >>> # prompts_config_path = tmp_path / "prompts.yaml"
        """
        if tmp_path:
            return cls(prompts_config_path=tmp_path / "prompts.yaml")
        return cls()
