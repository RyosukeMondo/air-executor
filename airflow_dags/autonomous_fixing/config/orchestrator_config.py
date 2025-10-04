"""Central configuration for MultiLanguageOrchestrator.

Provides unified configuration management for the entire orchestrator system,
supporting both YAML loading (existing behavior) and programmatic configuration
(new for tests).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .preflight_config import PreflightConfig
from .state_config import StateConfig


@dataclass
class OrchestratorConfig:
    """Central configuration for entire orchestrator.

    Consolidates all configuration parameters into a single, type-safe object.
    Supports loading from YAML (existing behavior) and programmatic construction
    (new for tests).

    Attributes:
        projects: List of project configurations with path and language.
        languages: Language-specific settings and enabled languages.
        priorities: Priority-based execution strategy settings.
        execution: Execution control settings (parallelism, timeouts).
        issue_grouping: Issue batching and grouping settings.
        batch_sizes: Tasks per phase per run.
        health_check: Health scoring method and thresholds.
        wrapper: Claude wrapper configuration.
        state_manager: Redis state management settings.
        logging: Logging configuration.
        git: Git automation settings.
        coverage_prompts: Test generation settings.
        safety: Safety and validation settings.
        project_overrides: Per-project configuration overrides.
        notifications: Notification settings.
        exclusions: Path exclusion patterns.
        state_config: State management configuration.
        preflight_config: Preflight validation configuration.

    Example:
        >>> # Load from YAML (existing behavior)
        >>> config = OrchestratorConfig.from_yaml(Path("config/real_projects_fix.yaml"))
        >>> orchestrator = MultiLanguageOrchestrator(config)

        >>> # Programmatic configuration (new for tests)
        >>> config = OrchestratorConfig(
        ...     projects=[{"path": "/tmp/test", "language": "python"}],
        ...     languages={"enabled": ["python"]}
        ... )

        >>> # Test configuration with isolation
        >>> config = OrchestratorConfig.for_testing(
        ...     tmp_path,
        ...     projects=[str(tmp_path / "test-project")],
        ...     languages=["python"]
        ... )
    """

    # Project settings
    projects: list[dict[str, str]] = field(default_factory=list)
    languages: dict[str, Any] = field(default_factory=lambda: {"enabled": ["python", "javascript"]})

    # Execution strategy
    priorities: dict[str, Any] = field(default_factory=dict)
    execution: dict[str, Any] = field(
        default_factory=lambda: {
            "parallel_languages": True,
            "max_concurrent_projects": 5,
            "fail_fast": False,
            "priority_gates": True,
            "max_iterations": 50,
            "max_duration_hours": 2,
        }
    )

    # Issue handling
    issue_grouping: dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": True,
            "mega_batch_mode": False,
            "max_cleanup_batch_size": 30,
            "max_location_batch_size": 15,
        }
    )
    batch_sizes: dict[str, int] = field(
        default_factory=lambda: {
            "p1_fixes": 2,
            "p2_fixes": 1,
            "p3_fixes": 1,
            "p4_fixes": 1,
        }
    )

    # Health and scoring
    health_check: dict[str, Any] = field(
        default_factory=lambda: {
            "method": "priority_based",
            "static_only_threshold": 0.60,
            "comprehensive_threshold": 0.80,
        }
    )

    # External integrations
    wrapper: dict[str, Any] = field(default_factory=dict)
    state_manager: dict[str, Any] = field(default_factory=dict)
    logging: dict[str, Any] = field(
        default_factory=lambda: {
            "level": "INFO",
            "format": "%(asctime)s - %(levelname)s - %(message)s",
        }
    )

    # Git automation
    git: dict[str, Any] = field(
        default_factory=lambda: {
            "auto_commit": True,
            "commit_prefix": "fix",
            "push_after_commit": False,
        }
    )

    # Coverage and testing
    coverage_prompts: dict[str, Any] = field(
        default_factory=lambda: {
            "generate_tests": True,
            "focus_areas": [
                "Critical business logic with no coverage",
                "Public APIs with low coverage",
                "Error handling paths",
            ],
        }
    )

    # Safety and validation
    safety: dict[str, Any] = field(
        default_factory=lambda: {
            "create_backup": False,
            "dry_run": False,
            "stop_on_git_errors": True,
            "stop_on_test_failures": False,
        }
    )

    # Path exclusions
    exclusions: dict[str, list[str]] = field(
        default_factory=lambda: {
            "patterns": [
                "node_modules",
                ".next",
                "build",
                "dist",
                ".venv",
                "venv",
                "__pycache__",
                ".pytest_cache",
                "coverage",
            ]
        }
    )

    # Per-project overrides
    project_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Notifications
    notifications: dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": False,
            "on_completion": False,
            "on_error": False,
        }
    )

    # Sub-configurations
    state_config: StateConfig = field(default_factory=StateConfig)
    preflight_config: PreflightConfig = field(default_factory=PreflightConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "OrchestratorConfig":
        """Load configuration from YAML file.

        Maintains backward compatibility with existing YAML configuration format.
        Loads all settings and creates appropriate sub-configs.

        Args:
            path: Path to YAML configuration file.

        Returns:
            OrchestratorConfig loaded from YAML.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If YAML parsing fails.

        Example:
            >>> config = OrchestratorConfig.from_yaml(Path("config/warps.yaml"))
            >>> orchestrator = MultiLanguageOrchestrator(config)
        """
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Create sub-configs (use defaults for now, could be extended)
        state_config = StateConfig()
        preflight_config = PreflightConfig()

        return cls(
            projects=data.get("projects", []),
            languages=data.get("languages", {}),
            priorities=data.get("priorities", {}),
            execution=data.get("execution", {}),
            issue_grouping=data.get("issue_grouping", {}),
            batch_sizes=data.get("batch_sizes", {}),
            health_check=data.get("health_check", {}),
            wrapper=data.get("wrapper", {}),
            state_manager=data.get("state_manager", {}),
            logging=data.get("logging", {}),
            git=data.get("git", {}),
            coverage_prompts=data.get("coverage_prompts", {}),
            safety=data.get("safety", {}),
            exclusions=data.get("exclusions", {}),
            project_overrides=data.get("project_overrides", {}),
            notifications=data.get("notifications", {}),
            state_config=state_config,
            preflight_config=preflight_config,
        )

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "OrchestratorConfig":
        """Create configuration from dictionary.

        Provides backward compatibility for code that passes dict configs.
        Extracts known fields and creates OrchestratorConfig.

        Args:
            config_dict: Configuration as dictionary.

        Returns:
            OrchestratorConfig created from dictionary.

        Example:
            >>> config_dict = {"projects": [...], "languages": {...}}
            >>> config = OrchestratorConfig.from_dict(config_dict)
        """
        return cls(
            projects=config_dict.get("projects", []),
            languages=config_dict.get("languages", {}),
            priorities=config_dict.get("priorities", {}),
            execution=config_dict.get("execution", {}),
            issue_grouping=config_dict.get("issue_grouping", {}),
            batch_sizes=config_dict.get("batch_sizes", {}),
            health_check=config_dict.get("health_check", {}),
            wrapper=config_dict.get("wrapper", {}),
            state_manager=config_dict.get("state_manager", {}),
            logging=config_dict.get("logging", {}),
            git=config_dict.get("git", {}),
            coverage_prompts=config_dict.get("coverage_prompts", {}),
            safety=config_dict.get("safety", {}),
            exclusions=config_dict.get("exclusions", {}),
            project_overrides=config_dict.get("project_overrides", {}),
            notifications=config_dict.get("notifications", {}),
        )

    @classmethod
    def for_testing(
        cls,
        tmp_path: Path,
        projects: list[str] | None = None,
        languages: list[str] | None = None,
        **overrides,
    ) -> "OrchestratorConfig":
        """Create isolated test configuration.

        Provides test-friendly defaults with isolated paths and fast timeouts.
        Uses temporary directory for all state and cache files.

        Args:
            tmp_path: Temporary directory for test isolation.
            projects: List of project paths to test. Defaults to [tmp_path / "test-project"].
            languages: List of enabled languages. Defaults to ["python"].
            **overrides: Additional configuration overrides.

        Returns:
            OrchestratorConfig optimized for testing.

        Example:
            >>> config = OrchestratorConfig.for_testing(
            ...     tmp_path,
            ...     projects=[str(tmp_path / "my-project")],
            ...     languages=["python", "javascript"]
            ... )
            >>> orchestrator = MultiLanguageOrchestrator(config)
        """
        # Default test projects
        if projects is None:
            projects = [str(tmp_path / "test-project")]

        # Convert project strings to project dicts
        if languages is None:
            languages = ["python"]

        project_dicts = [{"path": project, "language": languages[0]} for project in projects]

        # Create isolated configs
        state_config = StateConfig.for_testing(tmp_path)
        preflight_config = PreflightConfig.for_testing(tmp_path)

        # Test-friendly defaults
        config = cls(
            projects=project_dicts,
            languages={
                "enabled": languages,
                "auto_detect": False,
            },
            execution={
                "parallel_languages": False,  # Sequential for easier debugging
                "max_concurrent_projects": 1,
                "fail_fast": True,  # Fast failure in tests
                "priority_gates": False,  # Disabled for flexibility
                "max_iterations": 5,  # Fewer iterations
                "max_duration_hours": 0.5,  # 30 minutes max
            },
            state_manager={},  # No Redis in tests
            wrapper={},  # No external wrapper
            safety={
                "create_backup": False,
                "dry_run": False,
                "stop_on_git_errors": False,  # More lenient
                "stop_on_test_failures": False,
            },
            state_config=state_config,
            preflight_config=preflight_config,
        )

        # Apply overrides
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Useful for backward compatibility with code expecting dict configs.

        Returns:
            Dictionary representation of configuration.

        Example:
            >>> config = OrchestratorConfig.for_testing(tmp_path)
            >>> config_dict = config.to_dict()
            >>> # Use with legacy code that expects dict
        """
        return {
            "projects": self.projects,
            "languages": self.languages,
            "priorities": self.priorities,
            "execution": self.execution,
            "issue_grouping": self.issue_grouping,
            "batch_sizes": self.batch_sizes,
            "health_check": self.health_check,
            "wrapper": self.wrapper,
            "state_manager": self.state_manager,
            "logging": self.logging,
            "git": self.git,
            "coverage_prompts": self.coverage_prompts,
            "safety": self.safety,
            "exclusions": self.exclusions,
            "project_overrides": self.project_overrides,
            "notifications": self.notifications,
        }
