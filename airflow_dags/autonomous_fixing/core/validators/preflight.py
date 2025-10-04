"""
Pre-flight Validator - Fast computational checks before AI invocation.

Validates setup completion state and cache integrity to determine if
setup phases can be skipped, preventing redundant AI calls.
"""

import logging
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import yaml

from ...config.preflight_config import PreflightConfig
from ...config.state_config import StateConfig
from ...domain.interfaces import ISetupTracker, IStateRepository
from ..state_manager import ProjectStateManager


class PreflightValidator:
    """
    Perform fast computational checks to determine if setup phases can be skipped.

    Responsibilities:
    - Validate hook configuration cache and setup state
    - Validate test discovery cache and setup state
    - Check cache file integrity (YAML parsability, required fields)
    - Return skip decisions with explanatory reasons

    Does NOT:
    - Execute setup operations (that's IssueFixer's job)
    - Store setup state (that's SetupTracker's job)
    - Orchestrate setup flow (that's IterationEngine's job)
    """

    # Legacy constants for backward compatibility (use config instead)
    CACHE_MAX_AGE_SECONDS = 30 * 24 * 60 * 60  # 30 days (matches config default)
    HOOK_CACHE_DIR = Path("config/precommit-cache")
    TEST_CACHE_DIR = Path("config/test-cache")

    def __init__(
        self,
        setup_tracker: ISetupTracker,
        config: Optional[PreflightConfig] = None,
        state_config: Optional[StateConfig] = None,
        state_manager_factory: Optional[Callable[[Path, StateConfig], IStateRepository]] = None,
    ):
        """
        Initialize validator with setup state tracker.

        Args:
            setup_tracker: ISetupTracker instance for querying setup completion
            config: Optional PreflightConfig. If None, uses default configuration.
            state_config: Optional StateConfig for ProjectStateManager.
                If None, uses default paths.
            state_manager_factory: Optional callable that creates state manager instances.
                Signature: (project_path: Path, config: StateConfig) -> IStateRepository
                If None, defaults to ProjectStateManager for backward compatibility.

        Example:
            >>> # Default configuration
            >>> validator = PreflightValidator(tracker)

            >>> # Custom configuration for tests
            >>> test_config = PreflightConfig.for_testing(tmp_path)
            >>> state_config = StateConfig.for_testing(tmp_path)
            >>> validator = PreflightValidator(tracker, config=test_config, state_config=state_config)

            >>> # Inject mock state manager for testing
            >>> mock_factory = lambda path, cfg: MockStateManager()
            >>> validator = PreflightValidator(tracker, state_manager_factory=mock_factory)
        """
        self.logger = logging.getLogger(__name__)
        self.setup_tracker: ISetupTracker = setup_tracker
        self.config = config or PreflightConfig()
        self.state_config = state_config or StateConfig()
        # Default to ProjectStateManager for backward compatibility
        self.state_manager_factory: Callable[[Path, StateConfig], IStateRepository] = (
            state_manager_factory or ProjectStateManager
        )

    @contextmanager
    def _measure_validation(
        self, project_name: str, phase: str, start_time: float
    ) -> Iterator[None]:
        """
        Context manager for validation timing measurement.

        Args:
            project_name: Name of project being validated
            phase: Phase name ('hooks' or 'tests')
            start_time: Validation start timestamp

        Yields:
            None
        """
        try:
            yield
        finally:
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(
                f"PreflightValidator: {phase.title()} validation for {project_name} ({elapsed:.0f}ms)"
            )

    def _check_setup_state(
        self, project_path: Path, phase: str, start_time: float
    ) -> tuple[bool, str] | None:
        """
        Check if setup state is tracked as complete.

        Args:
            project_path: Path to project directory
            phase: Setup phase name ('hooks' or 'tests')
            start_time: Validation start timestamp for elapsed calculation

        Returns:
            (False, reason) if setup not complete, None if setup complete (continue checks)
        """
        if not self.setup_tracker.is_setup_complete(str(project_path), phase):
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(
                f"PreflightValidator: {phase.title()} setup not tracked as complete "
                f"for {project_path.name} ({elapsed:.0f}ms)"
            )
            return (False, "setup state not tracked")
        return None

    def _check_cache_freshness(
        self, cache_path: Path, project_name: str, phase: str, start_time: float
    ) -> tuple[bool, str] | None:
        """
        Check if cache file exists and is fresh (<7 days).

        Args:
            cache_path: Path to cache file
            project_name: Name of project for logging
            phase: Phase name ('hooks' or 'tests') for logging
            start_time: Validation start timestamp

        Returns:
            (False, reason) if cache missing or stale, None if cache fresh (continue checks)
        """
        # Check existence
        if not cache_path.exists():
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(
                f"PreflightValidator: {phase.title()} cache missing for {project_name} ({elapsed:.0f}ms)"
            )
            return (False, "cache file missing")

        # Check freshness
        cache_age = time.time() - cache_path.stat().st_mtime
        max_age_seconds = self.config.cache_max_age_days * 24 * 60 * 60
        if cache_age > max_age_seconds:
            days_old = int(cache_age / 86400)
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(
                f"PreflightValidator: {phase.title()} cache stale ({days_old}d) "
                f"for {project_name} ({elapsed:.0f}ms)"
            )
            return (False, f"cache stale ({days_old}d old)")

        return None

    def _get_cache_age_days(self, cache_path: Path) -> int:
        """
        Get cache file age in days.

        Args:
            cache_path: Path to cache file

        Returns:
            Age in days (integer)
        """
        cache_age = time.time() - cache_path.stat().st_mtime
        return int(cache_age / 86400)

    def _check_hook_cache_validity(
        self, cache_path: Path, project_name: str, start_time: float
    ) -> tuple[bool, str] | None:
        """
        Check if hook cache is valid and complete.

        Args:
            cache_path: Path to cache file
            project_name: Name of project for logging
            start_time: Validation start timestamp

        Returns:
            (False, reason) if cache invalid, None if cache valid (continue checks)
        """
        is_valid, reason = self._validate_hook_cache(cache_path)
        if not is_valid:
            elapsed = (time.time() - start_time) * 1000
            self.logger.warning(
                f"PreflightValidator: Hook cache invalid for {project_name}: {reason} ({elapsed:.0f}ms)"
            )
            return (False, f"cache invalid: {reason}")
        return None

    def _check_hook_files_exist(
        self, project_path: Path, project_name: str, start_time: float
    ) -> tuple[bool, str] | None:
        """
        Check if hook files exist on filesystem.

        Args:
            project_path: Path to project directory
            project_name: Name of project for logging
            start_time: Validation start timestamp

        Returns:
            (False, reason) if files missing, None if files exist (continue checks)
        """
        precommit_config = project_path / ".pre-commit-config.yaml"
        git_hook = project_path / ".git" / "hooks" / "pre-commit"

        if not precommit_config.exists():
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(
                f"PreflightValidator: .pre-commit-config.yaml missing for {project_name} ({elapsed:.0f}ms)"
            )
            return (False, ".pre-commit-config.yaml not found")

        if not git_hook.exists():
            elapsed = (time.time() - start_time) * 1000
            self.logger.debug(
                f"PreflightValidator: .git/hooks/pre-commit missing for {project_name} ({elapsed:.0f}ms)"
            )
            return (False, "git hook not installed")

        return None

    def _check_test_cache_validity(
        self, cache_path: Path, project_name: str, start_time: float
    ) -> tuple[bool, str] | None:
        """
        Check if test cache is valid and complete.

        Args:
            cache_path: Path to cache file
            project_name: Name of project for logging
            start_time: Validation start timestamp

        Returns:
            (False, reason) if cache invalid, None if cache valid (continue checks)
        """
        is_valid, reason = self._validate_test_cache(cache_path)
        if not is_valid:
            elapsed = (time.time() - start_time) * 1000
            self.logger.warning(
                f"PreflightValidator: Test cache invalid for {project_name}: {reason} ({elapsed:.0f}ms)"
            )
            return (False, f"cache invalid: {reason}")
        return None

    def can_skip_hook_config(self, project_path: Path) -> tuple[bool, str]:
        """
        Check if pre-commit hooks setup can be skipped.

        Delegates to ProjectStateManager for state validation with smart
        invalidation based on configuration changes and file deletions.

        Args:
            project_path: Path to project directory

        Returns:
            (can_skip, reason) where can_skip is True if setup can be skipped,
            and reason explains the decision
        """
        start_time = time.time()
        project_name = project_path.name

        # Check 1: Use injected state manager factory for state validation (checks filesystem + cache)
        state_manager = self.state_manager_factory(project_path, config=self.state_config)
        should_reconfig, reason = state_manager.should_reconfigure("hooks")

        elapsed = (time.time() - start_time) * 1000

        if should_reconfig:
            self.logger.debug(
                f"PreflightValidator: Hooks need reconfiguration for {project_name}: {reason} ({elapsed:.0f}ms)"
            )
            return (False, reason)

        # Check 2: Is setup tracked as complete in memory? (faster check for subsequent runs)
        if self._check_setup_state(project_path, "hooks", start_time):
            # Setup tracker says not complete, but state_manager says it is - trust state_manager
            pass

        self.logger.debug(
            f"PreflightValidator: Hooks can be skipped for {project_name}: {reason} ({elapsed:.0f}ms)"
        )
        return (True, f"{reason} (saved 60s + $0.50)")

    def can_skip_test_discovery(self, project_path: Path) -> tuple[bool, str]:
        """
        Check if test discovery can be skipped.

        Delegates to ProjectStateManager for state validation with smart
        invalidation based on configuration changes.

        Args:
            project_path: Path to project directory

        Returns:
            (can_skip, reason) where can_skip is True if discovery can be skipped,
            and reason explains the decision
        """
        start_time = time.time()
        project_name = project_path.name

        # Check 1: Is setup tracked as complete?
        if result := self._check_setup_state(project_path, "tests", start_time):
            return result

        # Check 2: Use injected state manager factory for state validation
        state_manager = self.state_manager_factory(project_path, config=self.state_config)
        should_reconfig, reason = state_manager.should_reconfigure("tests")

        elapsed = (time.time() - start_time) * 1000

        if should_reconfig:
            self.logger.debug(
                f"PreflightValidator: Tests need reconfiguration for {project_name}: {reason} ({elapsed:.0f}ms)"
            )
            return (False, reason)

        self.logger.debug(
            f"PreflightValidator: Tests can be skipped for {project_name}: {reason} ({elapsed:.0f}ms)"
        )
        return (True, f"{reason} (saved 90s + $0.60)")

    def _validate_hook_cache(self, cache_path: Path) -> tuple[bool, str]:
        """
        Validate hook configuration cache integrity.

        Checks:
        - YAML parsability
        - Presence of hook_framework.installed: true

        Args:
            cache_path: Path to cache file

        Returns:
            (is_valid, reason) where is_valid is True if cache is valid,
            and reason explains validation result
        """
        try:
            with open(cache_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                return (False, "cache is not a YAML dict")

            # Check required field: hook_framework.installed
            hook_framework = data.get("hook_framework", {})
            if not isinstance(hook_framework, dict):
                return (False, "hook_framework is not a dict")

            if not hook_framework.get("installed"):
                return (False, "hook_framework.installed != true")

            return (True, "cache valid and complete")

        except yaml.YAMLError as e:
            return (False, f"YAML parse error: {e}")
        except (PermissionError, OSError) as e:
            return (False, f"cache file unreadable: {e}")
        except Exception as e:
            self.logger.error("Unexpected error validating hook cache %s: %s", cache_path, e)
            return (False, f"unexpected error: {e}")

    def _validate_test_cache(self, cache_path: Path) -> tuple[bool, str]:
        """
        Validate test discovery cache integrity.

        Checks:
        - YAML parsability
        - Presence of required fields: test_framework, test_command, test_patterns

        Args:
            cache_path: Path to cache file

        Returns:
            (is_valid, reason) where is_valid is True if cache is valid,
            and reason explains validation result
        """
        try:
            with open(cache_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                return (False, "cache is not a YAML dict")

            # Check required fields
            required_fields = ["test_framework", "test_command", "test_patterns"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                return (False, f"missing fields: {', '.join(missing_fields)}")

            # Validate non-empty values
            for field in required_fields:
                if not data[field]:
                    return (False, f"{field} is empty")

            return (True, "cache valid and complete")

        except yaml.YAMLError as e:
            return (False, f"YAML parse error: {e}")
        except (PermissionError, OSError) as e:
            return (False, f"cache file unreadable: {e}")
        except Exception as e:
            self.logger.error("Unexpected error validating test cache %s: %s", cache_path, e)
            return (False, f"unexpected error: {e}")
