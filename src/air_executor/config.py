"""
Configuration management for Air Executor.

Loads configuration from TOML file with environment variable overrides.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Python 3.11+ has built-in tomllib, earlier versions need tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "tomli is required for Python < 3.11. Install with: pip install tomli"
        )


class Config:
    """
    Air Executor configuration loaded from TOML file.

    Usage:
        config = Config.load()
        wrapper_path = config.wrapper_path
        venv_python = config.venv_python
    """

    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize config from parsed TOML dictionary."""
        self._config = config_dict

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """
        Load configuration from TOML file.

        Args:
            config_path: Path to config file. If None, searches in order:
                         1. AIR_EXECUTOR_CONFIG env var
                         2. ./config/air-executor.toml
                         3. ~/.air-executor/config.toml
                         4. /etc/air-executor/config.toml

        Returns:
            Config instance

        Raises:
            FileNotFoundError: If no config file found
            ValueError: If config file is invalid
        """
        if config_path is None:
            config_path = cls._find_config_file()

        if not config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_path}\n"
                f"Create one from: config/air-executor.example.toml"
            )

        try:
            with open(config_path, "rb") as f:
                config_dict = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Invalid TOML in {config_path}: {e}")

        # Apply environment variable overrides
        config_dict = cls._apply_env_overrides(config_dict)

        return cls(config_dict)

    @staticmethod
    def _find_config_file() -> Path:
        """
        Find config file in standard locations.

        Priority:
        1. AIR_EXECUTOR_CONFIG environment variable
        2. ./config/air-executor.toml (project root)
        3. ~/.air-executor/config.toml (user home)
        4. /etc/air-executor/config.toml (system-wide)
        """
        # 1. Environment variable
        env_path = os.getenv("AIR_EXECUTOR_CONFIG")
        if env_path:
            return Path(env_path)

        # 2. Project root (relative to this file)
        project_root = Path(__file__).parent.parent.parent
        project_config = project_root / "config" / "air-executor.toml"
        if project_config.exists():
            return project_config

        # 3. User home
        user_config = Path.home() / ".air-executor" / "config.toml"
        if user_config.exists():
            return user_config

        # 4. System-wide
        system_config = Path("/etc/air-executor/config.toml")
        if system_config.exists():
            return system_config

        # Default to project root (even if doesn't exist, for error message)
        return project_config

    @staticmethod
    def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to config.

        Environment variables:
            AIR_EXECUTOR_ROOT - Override project.root
            AIRFLOW_HOME - Override airflow.home
            CLAUDE_TIMEOUT - Override claude.timeout_seconds
        """
        # Project paths
        if "AIR_EXECUTOR_ROOT" in os.environ:
            config.setdefault("project", {})["root"] = os.environ["AIR_EXECUTOR_ROOT"]

        # Airflow paths
        if "AIRFLOW_HOME" in os.environ:
            config.setdefault("airflow", {})["home"] = os.environ["AIRFLOW_HOME"]

        # Claude settings
        if "CLAUDE_TIMEOUT" in os.environ:
            config.setdefault("claude", {})["timeout_seconds"] = int(
                os.environ["CLAUDE_TIMEOUT"]
            )

        if "CLAUDE_PERMISSION_MODE" in os.environ:
            config.setdefault("claude", {})["permission_mode"] = os.environ[
                "CLAUDE_PERMISSION_MODE"
            ]

        return config

    # === Project Paths ===

    @property
    def project_root(self) -> Path:
        """Project root directory (absolute path)."""
        return Path(self._config["project"]["root"])

    @property
    def scripts_dir(self) -> Path:
        """Scripts directory (absolute path)."""
        root = self.project_root
        scripts = self._config["project"]["scripts_dir"]
        return root / scripts

    @property
    def wrapper_path(self) -> Path:
        """Claude wrapper script path (absolute path)."""
        wrapper = self._config["claude"]["wrapper_script"]
        return self.scripts_dir / wrapper

    @property
    def venv_python(self) -> Path:
        """Python executable in venv (absolute path)."""
        root = self.project_root
        venv = self._config["project"]["venv_python"]
        return root / venv

    # === Airflow Paths ===

    @property
    def airflow_home(self) -> Path:
        """Airflow home directory (absolute path)."""
        return Path(self._config["airflow"]["home"])

    @property
    def airflow_dags(self) -> Path:
        """Airflow DAGs folder (absolute path)."""
        home = self.airflow_home
        dags = self._config["airflow"]["dags_folder"]
        return home / dags

    @property
    def airflow_logs(self) -> Path:
        """Airflow logs folder (absolute path)."""
        home = self.airflow_home
        logs = self._config["airflow"]["logs_folder"]
        return home / logs

    @property
    def airflow_scripts(self) -> Path:
        """Airflow scripts folder (absolute path)."""
        home = self.airflow_home
        scripts = self._config["airflow"]["scripts_folder"]
        return home / scripts

    # === Claude Settings ===

    @property
    def claude_timeout(self) -> int:
        """Claude query timeout in seconds."""
        return self._config["claude"]["timeout_seconds"]

    @property
    def claude_permission_mode(self) -> str:
        """Claude permission mode."""
        return self._config["claude"]["permission_mode"]

    @property
    def claude_default_options(self) -> Dict[str, Any]:
        """Claude default options."""
        return self._config["claude"]["default_options"]

    # === Development Settings ===

    @property
    def debug(self) -> bool:
        """Debug mode enabled."""
        return self._config.get("development", {}).get("debug", False)

    # === Validation ===

    def validate(self) -> None:
        """
        Validate configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        # Check required paths exist
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {self.project_root}")

        if not self.wrapper_path.exists():
            raise ValueError(f"Wrapper script not found: {self.wrapper_path}")

        if not self.venv_python.exists():
            raise ValueError(f"Python venv not found: {self.venv_python}")

        # Check Airflow home exists
        if not self.airflow_home.exists():
            raise ValueError(f"Airflow home not found: {self.airflow_home}")

        # Validate timeout
        if self.claude_timeout <= 0:
            raise ValueError(f"Invalid timeout: {self.claude_timeout}")

        # Validate permission mode
        valid_modes = {"bypassPermissions", "ask"}
        if self.claude_permission_mode not in valid_modes:
            raise ValueError(
                f"Invalid permission mode: {self.claude_permission_mode}. "
                f"Must be one of {valid_modes}"
            )

    def __repr__(self) -> str:
        """String representation of config."""
        return (
            f"Config(\n"
            f"  project_root={self.project_root},\n"
            f"  wrapper_path={self.wrapper_path},\n"
            f"  airflow_home={self.airflow_home},\n"
            f"  claude_timeout={self.claude_timeout}s\n"
            f")"
        )


# === Convenience Functions ===


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load and validate configuration.

    Args:
        config_path: Optional path to config file

    Returns:
        Validated Config instance
    """
    config = Config.load(config_path)

    # Validate if enabled
    if config._config.get("development", {}).get("validate_config", True):
        config.validate()

    return config


def get_config() -> Config:
    """
    Get cached config instance (loads once, reuses).

    Returns:
        Config instance
    """
    if not hasattr(get_config, "_cached_config"):
        get_config._cached_config = load_config()
    return get_config._cached_config
