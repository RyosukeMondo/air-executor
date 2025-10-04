"""Configuration management with validation."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class Config(BaseModel):
    """
    Configuration for Air-Executor job manager.

    All settings have sensible defaults and are validated on load.
    """

    # Polling settings
    poll_interval: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Polling interval in seconds (1-60)"
    )

    # Runner settings
    task_timeout: int = Field(
        default=1800,
        ge=60,
        le=7200,
        description="Task timeout in seconds (60-7200, default 30 minutes)"
    )
    max_concurrent_runners: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum concurrent task runners (1-50)"
    )

    # Storage settings
    base_path: Path = Field(
        default=Path(".air-executor"),
        description="Base directory for all storage"
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json, console)"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of: {', '.join(valid_levels)}")
        return v_upper

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        valid_formats = {"json", "console"}
        v_lower = v.lower()
        if v_lower not in valid_formats:
            raise ValueError(f"log_format must be one of: {', '.join(valid_formats)}")
        return v_lower

    @field_validator("base_path", mode="before")
    @classmethod
    def convert_base_path(cls, v) -> Path:
        """Convert string to Path if needed."""
        if isinstance(v, str):
            return Path(v)
        return Path(v)

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """
        Load config from YAML file with validation.

        Args:
            path: Path to config.yaml file

        Returns:
            Config instance with validated settings

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)

            if data is None:
                data = {}

            # Warn about unknown keys
            known_keys = set(cls.model_fields.keys())
            unknown_keys = set(data.keys()) - known_keys
            if unknown_keys:
                import sys
                print(
                    f"Warning: Unknown config keys (will be ignored): {', '.join(unknown_keys)}",
                    file=sys.stderr
                )

            return cls(**data)

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file {path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load config from {path}: {e}")

    @classmethod
    def load_or_default(cls, path: Optional[Path] = None) -> "Config":
        """
        Load config from file or return default if file doesn't exist.

        Args:
            path: Optional path to config file (default: .air-executor/config.yaml)

        Returns:
            Config instance (loaded from file or default)
        """
        if path is None:
            path = Path(".air-executor") / "config.yaml"

        if path.exists():
            try:
                return cls.from_file(path)
            except Exception as e:
                import sys
                print(f"Warning: Failed to load config from {path}, using defaults: {e}", file=sys.stderr)
                return cls()
        else:
            return cls()

    @classmethod
    def default(cls) -> "Config":
        """
        Return default configuration.

        Returns:
            Config instance with all default values
        """
        return cls()

    def to_file(self, path: Path) -> None:
        """
        Save config to YAML file.

        Args:
            path: Path to config file

        Raises:
            OSError: If write fails
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w") as f:
                # Convert to dict and handle Path serialization
                data = self.model_dump()
                data["base_path"] = str(data["base_path"])
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise OSError(f"Failed to write config to {path}: {e}")

    def __repr__(self) -> str:
        """Representation of config."""
        return (
            f"Config(poll_interval={self.poll_interval}, "
            f"task_timeout={self.task_timeout}, "
            f"max_concurrent_runners={self.max_concurrent_runners})"
        )
